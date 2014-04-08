-- Standard user_edit_stats, but into a dedicated schema along with bulkimport filter.
-- 2014-04-08 15:26:57

-- Requires the world_borders_poi_latest and shared_poi tables.

DROP TABLE IF EXISTS filter_1k.user_edit_stats;

CREATE TABLE filter_1k.user_edit_stats AS
  SELECT alledits.country_gid, alledits.uid, alledits.username,
    num_poi,
    num_edits, num_tag_add, num_tag_update, num_tag_remove,
    coalesce(num_coll_edits, 0) as num_coll_edits, 
    coalesce(num_coll_tag_add, 0) as num_coll_tag_add, 
    coalesce(num_coll_tag_update, 0) as num_coll_tag_update, 
    coalesce(num_coll_tag_remove, 0) as num_coll_tag_remove,
    coalesce(num_coll_edits, 0)::numeric / num_edits as p_coll_edit, 
    coalesce(num_coll_tag_add, 0)::numeric / num_edits as p_coll_tag_add, 
    coalesce(num_coll_tag_update, 0)::numeric / num_edits as p_coll_tag_update, 
    coalesce(num_coll_tag_remove, 0)::numeric / num_edits as p_coll_tag_remove, 
    num_tag_keys, days_active, activity_period_days
  FROM (
    SELECT country_gid, uid, MAX(username) as username,
      count(distinct poi_id) as num_poi,
      count(*) as num_edits,
      sum(tag_add) as num_tag_add,
      sum(tag_update) as num_tag_update,
      sum(tag_remove) as num_tag_remove,
      count(distinct key) as num_tag_keys,
      count(distinct to_char(timestamp, 'YYYY-MM-DD')) as days_active,
      extract(day from max(timestamp)-min(timestamp)) as activity_period_days
    FROM (
      SELECT country_gid, uid, username, timestamp, p.id as poi_id, key,
        CASE WHEN action='add' THEN 1 ELSE 0 END as tag_add,
        CASE WHEN action='update' THEN 1 ELSE 0 END as tag_update,
        CASE WHEN action='remove' THEN 1 ELSE 0 END as tag_remove
      FROM filter_1k.poi p
      JOIN filter_1k.world_borders_poi_latest wp ON (p.id=wp.poi_id)
      JOIN filter_1k.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
      WHERE uid IS NOT NULL
    ) t1
    GROUP BY country_gid, uid
  ) alledits
  LEFT OUTER JOIN (
    SELECT country_gid, uid,
      count(*) as num_coll_edits,
      sum(tag_add) as num_coll_tag_add,
      sum(tag_update) as num_coll_tag_update,
      sum(tag_remove) as num_coll_tag_remove
    FROM (
      SELECT country_gid, uid,
        CASE WHEN action='add' THEN 1 ELSE 0 END as tag_add,
        CASE WHEN action='update' THEN 1 ELSE 0 END as tag_update,
        CASE WHEN action='remove' THEN 1 ELSE 0 END as tag_remove
      FROM filter_1k.poi p
      JOIN filter_1k.shared_poi sp ON (p.id=sp.poi_id AND p.version>=sp.first_shared_version)
      JOIN filter_1k.world_borders_poi_latest wp ON (p.id=wp.poi_id)
      JOIN filter_1k.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
      WHERE uid IS NOT NULL
    ) t2
    GROUP BY country_gid, uid
  ) ce ON (alledits.country_gid=ce.country_gid AND alledits.uid=ce.uid);
VACUUM ANALYZE filter_1k.user_edit_stats;
