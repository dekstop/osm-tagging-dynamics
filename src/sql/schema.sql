DROP VIEW IF EXISTS view_poi_currentversion;
DROP VIEW IF EXISTS view_poi_tag_reach;
DROP VIEW IF EXISTS view_poi_tag_edit_sequence;
DROP VIEW IF EXISTS view_poi_tag_additions;
DROP VIEW IF EXISTS view_poi_tag_removals;
DROP VIEW IF EXISTS view_poi_tag_updates;
DROP VIEW IF EXISTS view_region_poi;

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
  id          SERIAL PRIMARY KEY,
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
  SELECT t1.id, t1.poi_id, s.next_version AS version, t1.key, t1.value
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

CREATE VIEW view_poi_tag_edit_sequence AS
  SELECT 'add'::action, * FROM view_poi_tag_additions2
  UNION ALL
  SELECT 'remove'::action, * FROM view_poi_tag_removals2
  UNION ALL
  SELECT 'update'::action, * FROM view_poi_tag_updates2;

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

INSERT INTO region(name, minlat, minlon, maxlat, maxlon) VALUES 
  ('Greater London', 51.2825347, -0.585022, 51.7066085, 0.2842712),
  ('San Francisco', 37.603352, -122.529144, 37.812496, -122.341003),
  ('New York', 40.495004, -73.672943, 40.918701, -74.268951),
  ('Wales', 51.340907, -5.570068, 53.455349, -2.614746),
  ('Quebec City', 46.611715, -71.856079, 47.098175, -70.872803),
  ('Berlin', 52.318, 13.092, 52.672, 13.67),
  ('Paris', 48.501, 1.947, 49.093, 2.793),
  ('Mainz', 49.9507, 8.2051, 50.0385, 8.3349),
  ('South Africa', -35.86, 12.15, -20.63, 36.85),
  ('Israel', 29.34, 34.2299999, 33.39, 35.99);

-- Mapping region and poi IDs
CREATE VIEW view_region_poi AS
  SELECT r.id AS region_id, p.id AS poi_id
  FROM node p JOIN region r 
  ON (p.latitude>=r.minlat AND p.latitude<=r.maxlat 
    AND p.longitude>=r.minlon AND p.longitude<=r.maxlon)
  GROUP BY r.id, p.id;
