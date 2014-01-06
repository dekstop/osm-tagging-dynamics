-- User activity stats: number of poi, edits, changesets, min/max timestamp, min/max coordinates.
-- TODO: filter empty changesets, broken dates/coordinates

-- parameters:
-- $input_poi -- poi data.
-- $output


/*SET default_parallel 10;*/
/*SET output.compression.enabled true; */
/*SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;*/

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
clean_poi = FILTER poi BY (id IS NOT NULL AND version IS NOT NULL AND changeset IS NOT NULL AND timestamp IS NOT NULL AND uid IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL);

uid_group = GROUP clean_poi BY uid;
uid_stats = FOREACH uid_group {
  entries = $1;
  poi_ids = DISTINCT entries.id;
  changesets = DISTINCT entries.changeset;
  first_time = MIN(entries.timestamp);
  first_date = ToDate(first_time);
  last_time = MAX(entries.timestamp);
  last_date = ToDate(last_time);
  min_lat = MIN(entries.latitude);
  min_lon = MIN(entries.longitude);
  max_lat = MAX(entries.latitude);
  max_lon = MAX(entries.longitude);
  GENERATE $0 as uid, COUNT(poi_ids) as num_poi, COUNT(entries) as num_edits, COUNT(changesets) as num_changesets, first_time, last_time, DaysBetween(last_date, first_date) + 1 as lifespan_days, min_lat, min_lon, max_lat, max_lon;
};

store uid_stats into '$output';
