-- Make a timeline of OSM activity over time. A monthly breakdown of misc summary stats, projected on a stratified grid.

-- parameters:
-- $input_poi       directory of poi data
-- $input_poi_tag   directory of poi_tag data
-- $output          output directory

SET default_parallel 15;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

-- filter
-- this won't be needed when processing cleaned data.
clean_poi = FILTER poi BY (
    id IS NOT NULL AND
    version IS NOT NULL AND
    changeset IS NOT NULL AND
    timestamp IS NOT NULL AND timestamp!='' AND
    uid IS NOT NULL AND
    username IS NOT NULL AND username!='' AND
    latitude IS NOT NULL AND
    longitude IS NOT NULL);

poi_tag = LOAD '$input_poi_tag' AS (id:long, version:int, key:chararray, value:chararray);

clean_poi_tag = FILTER poi_tag BY (
    id IS NOT NULL AND
    version IS NOT NULL AND
    key IS NOT NULL AND key!='' AND
    key!='created_by');

-- transform and project
poi_3 = FOREACH clean_poi GENERATE 
    SUBSTRING(timestamp, 0, 7) as month,
    CONCAT((chararray)id, CONCAT('-', (chararray)version)) as id_version,
    id as id, version, changeset, uid,
    ROUND(latitude * 2) / 2.0 + 0.25 AS latitude, 
    ROUND(longitude * 2) / 2.0 + 0.25 AS longitude;

-- aggregate
poi_join = JOIN poi_3 BY (id, version), clean_poi_tag BY (id, version);

-- monthly global stats
month_id = FOREACH poi_join GENERATE month, poi_3::id;
month_id = DISTINCT month_id;
month_id_count = GROUP month_id BY month;
month_id_count = FOREACH month_id_count GENERATE FLATTEN(group) as month, COUNT(month_id) as num_ids;

month_edits = FOREACH poi_join GENERATE month, id_version;
month_edits = DISTINCT month_edits;
month_edits_count = GROUP month_edits BY month;
month_edits_count = FOREACH month_edits_count GENERATE FLATTEN(group) as month, COUNT(month_edits) as num_edits;

month_uids = FOREACH poi_join GENERATE month, uid;
month_uids = DISTINCT month_uids;
month_uids_count = GROUP month_uids BY month;
month_uids_count = FOREACH month_uids_count GENERATE FLATTEN(group) as month, COUNT(month_uids) as num_uids;

month_changesets = FOREACH poi_join GENERATE month, changeset;
month_changesets = DISTINCT month_changesets;
month_changesets_count = GROUP month_changesets BY month;
month_changesets_count = FOREACH month_changesets_count GENERATE FLATTEN(group) as month, COUNT(month_changesets) as num_changesets;

month_stats_join = JOIN month_id_count BY month, month_edits_count BY month, month_uids_count BY month, month_changesets_count BY month;
month_stats = FOREACH month_stats_join GENERATE month_id_count::month, month_id_count::num_ids, month_edits_count::num_edits, month_uids_count::num_uids, month_changesets_count::num_changesets;
store month_stats into '$output/monthly-global';


-- overall stratified grid stats
geo_id = FOREACH poi_join GENERATE latitude, longitude, poi_3::id;
geo_id = DISTINCT geo_id;
geo_id_count = GROUP geo_id BY (latitude, longitude);
geo_id_count = FOREACH geo_id_count GENERATE FLATTEN(group) as (latitude, longitude), COUNT(geo_id) as num_ids;

geo_edits = FOREACH poi_join GENERATE latitude, longitude, id_version;
geo_edits = DISTINCT geo_edits;
geo_edits_count = GROUP geo_edits BY (latitude, longitude);
geo_edits_count = FOREACH geo_edits_count GENERATE FLATTEN(group) as (latitude, longitude), COUNT(geo_edits) as num_edits;

geo_uids = FOREACH poi_join GENERATE latitude, longitude, uid;
geo_uids = DISTINCT geo_uids;
geo_uids_count = GROUP geo_uids BY (latitude, longitude);
geo_uids_count = FOREACH geo_uids_count GENERATE FLATTEN(group) as (latitude, longitude), COUNT(geo_uids) as num_uids;

geo_changesets = FOREACH poi_join GENERATE latitude, longitude, changeset;
geo_changesets = DISTINCT geo_changesets;
geo_changesets_count = GROUP geo_changesets BY (latitude, longitude);
geo_changesets_count = FOREACH geo_changesets_count GENERATE FLATTEN(group) as (latitude, longitude), COUNT(geo_changesets) as num_changesets;

geo_stats_join = JOIN geo_id_count BY (latitude, longitude), geo_edits_count BY (latitude, longitude), geo_uids_count BY (latitude, longitude), geo_changesets_count BY (latitude, longitude);
geo_stats = FOREACH geo_stats_join GENERATE geo_id_count::latitude, geo_id_count::longitude, geo_id_count::num_ids, geo_edits_count::num_edits, geo_uids_count::num_uids, geo_changesets_count::num_changesets;
store geo_stats into '$output/geo';

