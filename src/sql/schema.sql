-- =======
-- = POI =
-- =======

DROP TABLE poi;
CREATE TABLE poi (
  id          INTEGER NOT NULL,
  version     INTEGER NOT NULL,
  changeset   INTEGER NOT NULL,
  timestamp   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  uid         INTEGER,
  username    CHARACTER VARYING,
  -- visible     BOOL NOT NULL DEFAULT true,
  latitude    NUMERIC NOT NULL,
  longitude   NUMERIC NOT NULL
);

CREATE UNIQUE INDEX idx_poi_id_version ON poi(id, version);

DROP TABLE poi_tag;
CREATE TABLE poi_tag (
  id          SERIAL PRIMARY KEY,
  poi_id      INTEGER NOT NULL,
  version     INTEGER NOT NULL,
  key         CHARACTER VARYING,
  value       CHARACTER VARYING
);

CREATE INDEX idx_poi_tag_poi_id_version ON poi_tag(poi_id, version);
CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value);

-- =========
-- = Views =
-- =========

DROP VIEW view_poi_tag_history;
CREATE VIEW view_poi_tag_history AS 
  SELECT 
    poi_id, poi.version as version,
    changeset, timestamp, uid, username, latitude, longitude,
    key, value
  FROM poi JOIN poi_tag ON (poi.id=poi_tag.poi_id AND poi.version=poi_tag.version);

DROP VIEW view_poi_tag_firstversion;
CREATE VIEW view_poi_tag_firstversion AS
  SELECT min(id) AS poi_tag_id 
  FROM poi_tag 
  GROUP BY poi_id, key, value 
  ORDER BY poi_tag_id;

-- ===============
-- = Derivatives =
-- ===============

-- DROP TABLE poi_tag_first_version;
-- CREATE TABLE poi_tag_first_version (
--   poi_tag_id  INTEGER NOT NULL,
--   UNIQUE(poi_tag_id)
-- );
