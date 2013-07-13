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
  poi_version INTEGER NOT NULL,
  key         CHARACTER VARYING,
  value       CHARACTER VARYING
);

CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value);

-- ===============
-- = Derivatives =
-- ===============

DROP TABLE poi_tag_first_version;
CREATE TABLE poi_tag_first_version (
  poi_tag_id  INTEGER NOT NULL,
  UNIQUE(poi_tag_id)
);
