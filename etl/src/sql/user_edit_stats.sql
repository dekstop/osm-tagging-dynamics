-- Requires the world_borders_poi_latest and poi_multiple_editors tables.

DROP TABLE IF EXISTS user_edit_stats;

CREATE TABLE user_edit_stats AS 
  SELECT country_gid, uid, 
        CASE
          WHEN pm.poi_id IS NOT NULL 
          AND t.version>=pm.first_shared_version 
          THEN TRUE
          ELSE FALSE
        END as is_collab_work,
        count(distinct t.poi_id) as num_poi, 
        count(distinct t.poi_id ||' '|| version) as num_poi_edits,
        count(distinct poi_add) as num_poi_add, 
        count(distinct poi_update) as num_poi_update, 
        count(distinct changeset) as num_changesets, 
        count(*) as num_tag_edits,
        count(tag_add) as num_tag_add,
        count(tag_update) as num_tag_update,
        count(tag_remove) as num_tag_remove,
        count(distinct(key)) as num_tag_keys,
        count(distinct to_char(t.timestamp, 'YYYY-MM-DD')) as days_active,
        extract(day from max(t.timestamp)-min(t.timestamp)) + 1 as lifespan_days
  FROM (
    SELECT country_gid, p.id as poi_id, p.version, uid, changeset, timestamp, key,
      CASE WHEN p.version=1 THEN id ELSE NULL END as poi_add,
      CASE WHEN p.version>1 THEN id ELSE NULL END as poi_update,
      CASE WHEN e.action='add' THEN 1 ELSE NULL END as tag_add,
      CASE WHEN e.action='update' THEN 1 ELSE NULL END as tag_update,
      CASE WHEN e.action='remove' THEN 1 ELSE NULL END as tag_remove
    FROM poi p 
    JOIN poi_tag_edit_action e ON (p.id=e.poi_id and p.version=e.version)
    JOIN world_borders_poi_latest wp ON (p.id=wp.poi_id)) t
  LEFT OUTER JOIN poi_multiple_editors pm ON (t.poi_id=pm.poi_id)
  WHERE uid IS NOT NULL
  GROUP BY country_gid, uid, is_collab_work;
VACUUM ANALYZE user_edit_stats;
