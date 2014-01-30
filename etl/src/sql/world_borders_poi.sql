-- Requires the world_borders_simpl table.

-- shp2pgsql -c -I ~/osm/data/basemaps/TM_WORLD_BORDERS-0.3/TM_WORLD_BORDERS-0.3.shp world_borders > ~/osm/data/basemaps/TM_WORLD_BORDERS-0.3.sql
-- shp2pgsql -c -I ~/osm/data/basemaps/TM_WORLD_BORDERS_SIMPL-0.3/TM_WORLD_BORDERS_SIMPL-0.3.shp world_borders_simpl > ~/osm/data/basemaps/TM_WORLD_BORDERS_SIMPL-0.3.sql
-- 
-- $ psql --set ON_ERROR_STOP=1 -U osm -h localhost osm_regions_a < osm/data/world-borders/TM_WORLD_BORDERS-0.3.sql
-- $ psql --set ON_ERROR_STOP=1 -U osm -h localhost osm_regions_a < osm/data/world-borders/TM_WORLD_BORDERS_SIMPL-0.3.sql

DROP TABLE IF EXISTS world_borders_poi_latest;
DROP VIEW IF EXISTS view_world_borders_poi_latest;

CREATE VIEW view_world_borders_poi_latest AS
  SELECT w.gid AS country_gid, p.id AS poi_id
  FROM (SELECT id, max(version) AS version FROM poi GROUP BY id) pl
  JOIN (
    SELECT id, version, ST_MakePoint(longitude, latitude) as poi_loc 
    FROM poi) p ON (pl.id=p.id AND pl.version=p.version)
  JOIN world_borders_simpl w
  ON (ST_Contains(the_geom, poi_loc))
  GROUP BY w.gid, p.id;

CREATE TABLE world_borders_poi_latest as SELECT * FROM view_world_borders_poi_latest;
VACUUM ANALYZE world_borders_poi_latest;
