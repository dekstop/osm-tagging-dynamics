-- User activity stats: number of nodes/edits, min/max timestamp, min/max coordinates.
-- TODO: filter empty changesets, broken dates/coordinates

-- parameters:
-- $input -- node data.
-- $output


/*SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;
*/
node = LOAD '$input' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

username_group = GROUP node BY username;
username_stats = FOREACH username_group {
  entries = $1;
  node_ids = DISTINCT entries.id;
  first_time = MIN(entries.timestamp);
  last_time = MAX(entries.timestamp);
  min_lat = MIN(entries.latitude);
  min_lon = MIN(entries.longitude);
  max_lat = MAX(entries.latitude);
  max_lon = MAX(entries.longitude);
  GENERATE $0 as username, COUNT(node_ids) as num_nodes, COUNT(entries) as num_edits, first_time, last_time, min_lat, min_lon, max_lat, max_lon;
};

store username_stats into '$output';
