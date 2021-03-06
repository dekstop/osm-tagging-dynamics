-- poi_edit_stats
-- 2014-05-23 13:44:20

-- Requires the world_borders_poi_latest and shared_poi tables.

DROP TABLE IF EXISTS filter_1k.poi_edit_stats;

CREATE TABLE filter_1k.poi_edit_stats AS
  SELECT alledits.country_gid, alledits.kind,
    num_users, 
    coalesce(num_coll_users, 0) as num_coll_users, 
    num_poi,
    num_edits, num_tag_add, num_tag_update, num_tag_remove,
    coalesce(num_coll_edits, 0) as num_coll_edits, 
    coalesce(num_coll_tag_add, 0) as num_coll_tag_add, 
    coalesce(num_coll_tag_update, 0) as num_coll_tag_update, 
    coalesce(num_coll_tag_remove, 0) as num_coll_tag_remove, 
    num_tag_values
  FROM (
    SELECT country_gid, kind,
      count(distinct uid) as num_users,
      count(distinct poi_id) as num_poi,
      count(*) as num_edits,
      sum(tag_add) as num_tag_add,
      sum(tag_update) as num_tag_update,
      sum(tag_remove) as num_tag_remove,
      count(distinct value) as num_tag_values
    FROM (
      SELECT country_gid, uid, p.id as poi_id, 
        CASE
          WHEN key='amenity' AND value IS NOT NULL THEN value
          ELSE 'other POI'
        END as kind, 
        value,
        CASE WHEN action='add' THEN 1 ELSE 0 END as tag_add,
        CASE WHEN action='update' THEN 1 ELSE 0 END as tag_update,
        CASE WHEN action='remove' THEN 1 ELSE 0 END as tag_remove
      FROM filter_1k.poi p
      JOIN filter_1k.world_borders_poi_latest wp ON (p.id=wp.poi_id)
      JOIN filter_1k.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
      WHERE uid IS NOT NULL
    ) t1
    GROUP BY country_gid, kind
  ) alledits
  LEFT OUTER JOIN (
    SELECT country_gid, kind, 
      count(distinct uid) as num_coll_users,
      count(*) as num_coll_edits,
      sum(tag_add) as num_coll_tag_add,
      sum(tag_update) as num_coll_tag_update,
      sum(tag_remove) as num_coll_tag_remove
    FROM (
      SELECT country_gid, uid, 
        CASE
          WHEN key='amenity' AND value IS NOT NULL THEN value
          ELSE 'other POI'
        END as kind, 
        CASE WHEN action='add' THEN 1 ELSE 0 END as tag_add,
        CASE WHEN action='update' THEN 1 ELSE 0 END as tag_update,
        CASE WHEN action='remove' THEN 1 ELSE 0 END as tag_remove
      FROM filter_1k.poi p
      JOIN filter_1k.shared_poi sp ON (p.id=sp.poi_id AND p.version>=sp.first_shared_version)
      JOIN filter_1k.world_borders_poi_latest wp ON (p.id=wp.poi_id)
      JOIN filter_1k.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
      WHERE uid IS NOT NULL
    ) t2
    GROUP BY country_gid, kind
  ) ce ON (alledits.country_gid=ce.country_gid AND alledits.kind=ce.kind);
VACUUM ANALYZE filter_1k.poi_edit_stats;
