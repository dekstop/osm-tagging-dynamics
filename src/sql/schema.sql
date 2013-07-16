-- =======
-- = POI =
-- =======

DROP TABLE node;
CREATE TABLE node (
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

-- tag reach
DROP VIEW view_poi_tag_reach;
CREATE VIEW view_poi_tag_reach AS
  SELECT key, count(distinct username) reach
  FROM poi p JOIN poi_tag t ON (p.id=t.poi_id)
  GROUP BY key;

-- all first versions for (object, tag) tuples
DROP VIEW view_poi_tag_firstversion;
CREATE VIEW view_poi_tag_firstversion AS
  SELECT min(id) AS poi_tag_id 
  FROM poi_tag 
  GROUP BY poi_id, key, value 
  ORDER BY poi_tag_id;

-- poi versions that introduced new tags (a new tag key in the set of annotations for this poi)
DROP VIEW view_poi_tag_additions;
CREATE VIEW view_poi_tag_additions AS 
  SELECT t2.* 
  FROM poi_tag t2 LEFT OUTER JOIN poi_tag t1 
  ON (t1.poi_id=t2.poi_id 
    AND t1.version=(t2.version-1) 
    AND t1.key=t2.key) 
  WHERE t1.key IS NULL;

-- poi versions that removed particular tags (an existing key in the set of poi annotations)
DROP VIEW view_poi_tag_removals;
CREATE VIEW view_poi_tag_removals AS 
  SELECT t1.id, t1.poi_id, (t1.version + 1) as version, t1.key, t1.value
  FROM poi_tag t1 LEFT OUTER JOIN poi_tag t2
  ON (t1.poi_id=t2.poi_id 
    AND t1.version=(t2.version-1) 
    AND t1.key=t2.key) 
  WHERE t2.key IS NULL 
  AND t1.version < (
    SELECT MAX(version) 
    FROM poi_tag tx 
    WHERE t1.poi_id=tx.poi_id);

-- poi versions that updated existing tags (same key, new value)
DROP VIEW view_poi_tag_updates;
CREATE VIEW view_poi_tag_updates AS
  SELECT t2.* 
  FROM poi_tag t1 JOIN poi_tag t2 
  ON (t1.poi_id=t2.poi_id 
    AND t1.version=(t2.version-1) 
    AND t1.key=t2.key 
    AND t1.value!=t2.value);

-- full tag editing sequence: add/remove/update
DROP TYPE action;
CREATE TYPE action AS ENUM ('add', 'remove', 'update');

DROP VIEW view_poi_tag_edit_sequence;
CREATE VIEW view_poi_tag_edit_sequence AS
  SELECT 'add'::action, * FROM view_poi_tag_additions
  UNION
  SELECT 'remove'::action, * FROM view_poi_tag_removals
  UNION
  SELECT 'update'::action, * FROM view_poi_tag_updates;
