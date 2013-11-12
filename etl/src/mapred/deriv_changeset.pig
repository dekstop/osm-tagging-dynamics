-- Changeset stats: number of POI, min/max timestamp, min/max coordinates.
-- TODO: filter empty changesets, broken dates/coordinates

-- parameters:
-- $input_poi
-- $output


SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

changeset_group = GROUP poi BY changeset;
changeset_stats = FOREACH changeset_group {
  entries = $1;
  poi_ids = DISTINCT entries.id;
  first_time = MIN(entries.timestamp);
  last_time = MAX(entries.timestamp);
  min_lat = MIN(entries.latitude);
  min_lon = MIN(entries.longitude);
  max_lat = MAX(entries.latitude);
  max_lon = MAX(entries.longitude);
  GENERATE $0 as changeset, COUNT(poi_ids) as num_poi, first_time, last_time, min_lat, min_lon, max_lat, max_lon;
};

store changeset_stats into '$output';
