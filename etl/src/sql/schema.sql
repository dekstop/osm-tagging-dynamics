DROP VIEW IF EXISTS view_poi_tag_reach;
DROP VIEW IF EXISTS view_poi_tag_edit_action;
DROP VIEW IF EXISTS view_poi_tag_addition;
DROP VIEW IF EXISTS view_poi_tag_removal;
DROP VIEW IF EXISTS view_poi_tag_update;
DROP VIEW IF EXISTS view_poi_sequence;
DROP VIEW IF EXISTS view_region_poi_any;
DROP VIEW IF EXISTS view_region_poi_latest;

DROP TABLE IF EXISTS node;
DROP TABLE IF EXISTS poi;
DROP TABLE IF EXISTS poi_sequence;
DROP TABLE IF EXISTS poi_multiple_editors;
DROP TABLE IF EXISTS poi_tag;
DROP TABLE IF EXISTS poi_tag_edit_action;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS changeset;

DROP TYPE IF EXISTS action CASCADE;

-- ========
-- = Node =
-- ========

CREATE TABLE node (
  id          BIGINT NOT NULL,
  version     INTEGER NOT NULL,
  changeset   INTEGER NOT NULL,
  timestamp   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  uid         INTEGER,
  username    TEXT,
  -- visible     BOOL NOT NULL DEFAULT true,
  latitude    NUMERIC,
  longitude   NUMERIC
);

-- =======
-- = POI =
-- =======

CREATE TABLE poi (
  id          BIGINT NOT NULL,
  version     INTEGER NOT NULL,
  changeset   INTEGER NOT NULL,
  timestamp   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  uid         INTEGER,
  username    TEXT,
  -- visible     BOOL NOT NULL DEFAULT true,
  latitude    NUMERIC NOT NULL,
  longitude   NUMERIC NOT NULL
);

CREATE UNIQUE INDEX idx_poi_id_version ON poi(id, version);
  
-- Sequence of poi versions, skipping over redactions.
-- As view, and as table (to create a materialised view during ETL.)
CREATE VIEW view_poi_sequence AS
  SELECT p.id, p.version,
  (SELECT max(version) FROM poi p2 WHERE p.id=p2.id AND p.version>p2.version) as prev_version,
  (SELECT min(version) FROM poi p3 WHERE p.id=p3.id AND p.version<p3.version) as next_version
  FROM poi p;

CREATE TABLE poi_sequence (
  poi_id        BIGINT NOT NULL,
  version       INTEGER NOT NULL,
  prev_version  INTEGER,
  next_version  INTEGER
);

CREATE UNIQUE INDEX idx_poi_sequence_poi_id_version ON poi_sequence(poi_id, version);

-- POI that are "shared" between editors (that have more than one editor)
-- POI in this list are considered as "shared"
CREATE VIEW view_poi_multiple_editors AS
  SELECT p1.id as poi_id, p1.uid as creator, MIN(p2.version) as first_shared_version
  FROM (
    SELECT id, uid from poi 
    WHERE version=1 AND uid IS NOT NULL) p1
  JOIN (
    SELECT id, uid, version FROM poi
    WHERE version>1) p2 ON (p1.id=p2.id AND p1.uid!=p2.uid)
  GROUP BY p1.id, p1.uid;

CREATE TABLE poi_multiple_editors (
  poi_id                INTEGER NOT NULL,
  creator               INTEGER NOT NULL,
  first_shared_version  INTEGER NOT NULL
);

CREATE UNIQUE INDEX idx_poi_multiple_editors_poi_id ON poi_multiple_editors(poi_id);

-- ===========
-- = POI Tag =
-- ===========

CREATE TABLE poi_tag (
  poi_id      BIGINT NOT NULL,
  version     INTEGER NOT NULL,
  key         TEXT,
  value       TEXT
);

CREATE INDEX idx_poi_tag_poi_id_version ON poi_tag(poi_id, version);
CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value);

-- Tag reach
CREATE VIEW view_poi_tag_reach AS
  SELECT key, count(distinct username) AS reach
  FROM poi p JOIN poi_tag t ON (p.id=t.poi_id)
  GROUP BY key;

-- ===================
-- = POI Tag History =
-- ===================

-- poi versions that introduced new tags (a new tag key in the set of annotations for this poi)
CREATE VIEW view_poi_tag_addition AS 
  SELECT t2.*
  FROM poi_tag t2 JOIN poi_sequence s 
  ON (t2.poi_id=s.poi_id AND t2.version=s.version)
  LEFT OUTER JOIN poi_tag t1 
  ON (t1.poi_id=t2.poi_id AND t1.version=s.prev_version AND t1.key=t2.key)
  WHERE t1.key IS NULL;

-- poi versions that removed particular tags (an existing key in the set of poi annotations)
CREATE VIEW view_poi_tag_removal AS 
  SELECT t1.poi_id, s.next_version AS version, t1.key, t1.value
  FROM poi_tag t1 JOIN poi_sequence s 
  ON (t1.poi_id=s.poi_id AND t1.version=s.version)
  LEFT OUTER JOIN poi_tag t2
  ON (t1.poi_id=t2.poi_id AND t2.version=s.next_version AND t1.key=t2.key)
  WHERE s.next_version IS NOT NULL AND t2.key IS NULL;

-- poi versions that updated existing tags (same key, new value)
CREATE VIEW view_poi_tag_update AS
  SELECT t2.* 
  FROM poi_tag t1 JOIN poi_sequence s 
  ON (t1.poi_id=s.poi_id AND t1.version=s.version)
  JOIN poi_tag t2 ON (t1.poi_id=t2.poi_id AND t2.version=s.next_version 
    AND t1.key=t2.key)
  WHERE t1.value!=t2.value;

-- Full tag editing sequence: add/remove/update
CREATE TYPE action AS ENUM ('add', 'remove', 'update');

-- Combined: this excludes versions of a tag that did not introduce any changes.
-- As view, and as table (to create a materialised view during ETL.)
CREATE VIEW view_poi_tag_edit_action AS
  SELECT *, 'add'::action FROM view_poi_tag_addition
  UNION ALL
  SELECT *, 'remove'::action FROM view_poi_tag_removal
  UNION ALL
  SELECT *, 'update'::action FROM view_poi_tag_update;

CREATE TABLE poi_tag_edit_action (
  poi_id      BIGINT NOT NULL,
  version     INTEGER NOT NULL,
  key         TEXT,
  value       TEXT,
  action      action NOT NULL
);

CREATE UNIQUE INDEX idx_poi_tag_edit_action_poi_id_version_key ON poi_tag_edit_action(poi_id, version, key);

-- ==========
-- = Region =
-- ==========

CREATE TABLE region (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  minlat      NUMERIC NOT NULL,
  minlon      NUMERIC NOT NULL,
  maxlat      NUMERIC NOT NULL,
  maxlon      NUMERIC NOT NULL
);

-- Mapping region and poi IDs
CREATE VIEW view_region_poi_any AS
  SELECT r.id AS region_id, p.id AS poi_id
  FROM poi p LEFT OUTER JOIN region r 
  ON (p.latitude>=r.minlat AND p.latitude<=r.maxlat 
    AND p.longitude>=r.minlon AND p.longitude<=r.maxlon)
  GROUP BY r.id, p.id;

CREATE VIEW view_region_poi_latest AS
  SELECT r.id AS region_id, p.id AS poi_id
  FROM (SELECT id, max(version) AS version FROM poi GROUP BY id) pl
  JOIN poi p ON (pl.id=p.id AND pl.version=p.version) 
  LEFT OUTER JOIN region r 
  ON (p.latitude>=r.minlat AND p.latitude<=r.maxlat 
    AND p.longitude>=r.minlon AND p.longitude<=r.maxlon)
  GROUP BY r.id, p.id;

-- ========================
-- = Changeset Statistics =
-- ========================

CREATE TABLE changeset (
  id          INTEGER NOT NULL,
  num_nodes   INTEGER NOT NULL,
  first_time  TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  last_time   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  minlat      NUMERIC,
  minlon      NUMERIC,
  maxlat      NUMERIC,
  maxlon      NUMERIC
);

CREATE UNIQUE INDEX idx_changeset_id ON changeset(id);
CREATE INDEX idx_changeset_num_nodes ON changeset(num_nodes);
