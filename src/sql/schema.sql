DROP VIEW IF EXISTS view_poi_currentversion;
DROP VIEW IF EXISTS view_poi_tag_reach;
DROP VIEW IF EXISTS view_poi_tag_edit_actions;
DROP VIEW IF EXISTS view_poi_tag_additions;
DROP VIEW IF EXISTS view_poi_tag_removals;
DROP VIEW IF EXISTS view_poi_tag_updates;
DROP VIEW IF EXISTS view_region_poi_any;
DROP VIEW IF EXISTS view_region_poi_latest;

DROP TABLE IF EXISTS node;
DROP TABLE IF EXISTS poi;
DROP TABLE IF EXISTS poi_tag;
DROP TABLE IF EXISTS region;

DROP TYPE IF EXISTS action;

-- ========
-- = Node =
-- ========

CREATE TABLE node (
  id          INTEGER NOT NULL,
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
  id          INTEGER NOT NULL,
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
DROP TABLE IF EXISTS poi_sequence;
CREATE TABLE poi_sequence (
  poi_id        INTEGER NOT NULL,
  version       INTEGER NOT NULL,
  prev_version  INTEGER,
  next_version  INTEGER
);

CREATE UNIQUE INDEX poi_sequence_poi_id_version ON poi_sequence(poi_id, version);

-- ===========
-- = POI Tag =
-- ===========

CREATE TABLE poi_tag (
  poi_id      INTEGER NOT NULL,
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
CREATE VIEW view_poi_tag_additions AS 
  SELECT t2.*
  FROM poi_tag t2 JOIN poi_sequence s 
  ON (t2.poi_id=s.poi_id AND t2.version=s.version)
  LEFT OUTER JOIN poi_tag t1 
  ON (t1.poi_id=t2.poi_id AND t1.version=s.prev_version AND t1.key=t2.key)
  WHERE t1.key IS NULL;

-- poi versions that removed particular tags (an existing key in the set of poi annotations)
CREATE VIEW view_poi_tag_removals AS 
  SELECT t1.poi_id, s.next_version AS version, t1.key, t1.value
  FROM poi_tag t1 JOIN poi_sequence s 
  ON (t1.poi_id=s.poi_id AND t1.version=s.version)
  LEFT OUTER JOIN poi_tag t2
  ON (t1.poi_id=t2.poi_id AND t2.version=s.next_version AND t1.key=t2.key)
  WHERE s.next_version IS NOT NULL AND t2.key IS NULL;

-- poi versions that updated existing tags (same key, new value)
CREATE VIEW view_poi_tag_updates AS
  SELECT t2.* 
  FROM poi_tag t1 JOIN poi_sequence s 
  ON (t1.poi_id=s.poi_id AND t1.version=s.version)
  JOIN poi_tag t2 ON (t1.poi_id=t2.poi_id AND t2.version=s.next_version 
    AND t1.key=t2.key)
  WHERE t1.value!=t2.value;

-- full tag editing sequence: add/remove/update
CREATE TYPE action AS ENUM ('add', 'remove', 'update');

CREATE VIEW view_poi_tag_edit_actions AS
  SELECT 'add'::action, * FROM view_poi_tag_additions
  UNION ALL
  SELECT 'remove'::action, * FROM view_poi_tag_removals
  UNION ALL
  SELECT 'update'::action, * FROM view_poi_tag_updates;

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
