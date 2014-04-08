-- Expects the standard schema with shared_poi and world_borders_poi scripts.
-- Implements a more strict POI filter: all nodes with a name or amenity tag.
-- 2014-04-08 15:22:21

CREATE VIEW view_poi_strict_ids AS
  SELECT distinct poi_id FROM poi_tag 
  WHERE (key='name' AND value IS NOT NULL AND value!='')
  OR (key='amenity' AND value IS NOT NULL AND value!='');

ALTER TABLE poi RENAME TO poi_full;
CREATE TABLE poi AS 
  SELECT p.* FROM poi_full p 
  JOIN view_poi_strict_ids t ON p.id=t.poi_id;
VACUUM ANALYZE poi;

ALTER TABLE poi_tag RENAME TO poi_tag_full;
CREATE TABLE poi_tag AS 
  SELECT p.* FROM poi_tag_full p 
  JOIN view_poi_strict_ids t ON p.poi_id=t.poi_id;
VACUUM ANALYZE poi_tag;

ALTER TABLE poi_tag_edit_action RENAME TO poi_tag_edit_action_full;
CREATE TABLE poi_tag_edit_action AS 
  SELECT p.* FROM poi_tag_edit_action_full p 
  JOIN view_poi_strict_ids t ON p.poi_id=t.poi_id;
VACUUM ANALYZE poi_tag_edit_action;

ALTER TABLE world_borders_poi_latest RENAME TO world_borders_poi_latest_full;
CREATE TABLE world_borders_poi_latest AS 
  SELECT p.* FROM world_borders_poi_latest_full p 
  JOIN view_poi_strict_ids t ON p.poi_id=t.poi_id;
VACUUM ANALYZE world_borders_poi_latest;

ALTER TABLE shared_poi RENAME TO shared_poi_full;
CREATE TABLE shared_poi AS 
  SELECT p.* FROM shared_poi_full p 
  JOIN view_poi_strict_ids t ON p.poi_id=t.poi_id;
VACUUM ANALYZE shared_poi;

ALTER TABLE changeset RENAME TO changeset_full;
CREATE TABLE changeset AS SELECT * FROM view_changeset;
VACUUM ANALYZE changeset;
