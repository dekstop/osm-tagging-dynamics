-- Implements a bulkimport filter. Creates a dedicated schema for it first.
-- 2014-04-08 15:22:21

CREATE SCHEMA filter_1k;

CREATE TABLE filter_1k.poi AS 
  SELECT p.* FROM poi p
  JOIN changeset c ON p.changeset=c.id
  WHERE c.num_edits<=1000;
VACUUM ANALYZE filter_1k.poi;

CREATE TABLE filter_1k.poi_tag AS 
  SELECT p.* FROM poi_tag p
  JOIN filter_1k.poi f ON (f.id=p.poi_id and f.version=p.version);
VACUUM ANALYZE filter_1k.poi_tag;

CREATE TABLE filter_1k.poi_tag_edit_action AS 
  SELECT p.* FROM poi_tag_edit_action p
  JOIN filter_1k.poi f ON (f.id=p.poi_id and f.version=p.version);
VACUUM ANALYZE filter_1k.poi_tag_edit_action;

CREATE TABLE filter_1k.world_borders_poi_latest AS 
  SELECT p.* FROM world_borders_poi_latest p
  JOIN (SELECT DISTINCT id FROM filter_1k.poi) f ON (f.id=p.poi_id);
VACUUM ANALYZE filter_1k.world_borders_poi_latest;

CREATE TABLE filter_1k.shared_poi AS 
  SELECT p.* FROM shared_poi p
  JOIN (SELECT DISTINCT id FROM filter_1k.poi) f ON (f.id=p.poi_id);
VACUUM ANALYZE filter_1k.shared_poi;

CREATE TABLE filter_1k.changeset AS 
  SELECT p.* FROM changeset p
  JOIN (SELECT DISTINCT changeset FROM filter_1k.poi) f ON (f.changeset=p.id);
VACUUM ANALYZE filter_1k.changeset;
