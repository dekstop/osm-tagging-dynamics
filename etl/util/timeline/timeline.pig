-- Make a timeline of OSM activity over time. A monthly breakdown of misc summary stats, projected on a stratified grid.

-- parameters:
-- $input_poi       directory of poi data
-- $input_poi_tag   directory of poi_tag data
-- $output          output directory

SET default_parallel 10;
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
group_month = GROUP poi_join BY (month);
group_month_geo = GROUP poi_join BY (month, latitude, longitude);
group_geo = GROUP poi_join BY (latitude, longitude);

timeline_global = FOREACH group_month {
    group_ = $0;
    entries = $1;
    poi_ids = DISTINCT entries.poi_3::id;
    edits = DISTINCT entries.id_version;
    users = DISTINCT entries.uid;
    changesets = DISTINCT entries.changeset;
    tag_keys = DISTINCT entries.key;
   GENERATE flatten(group_) as (month), COUNT(poi_ids), COUNT(edits), COUNT(users), COUNT(changesets), COUNT(tag_keys);
};

store timeline_global into '$output/timeline-global';

timeline_stratified = FOREACH group_month_geo {
    group_ = $0;
    entries = $1;
    poi_ids = DISTINCT entries.poi_3::id;
    edits = DISTINCT entries.id_version;
    users = DISTINCT entries.uid;
    changesets = DISTINCT entries.changeset;
    tag_keys = DISTINCT entries.key;
   GENERATE flatten(group_) as (month, latitude, longitude), COUNT(poi_ids), COUNT(edits), COUNT(users), COUNT(changesets), COUNT(tag_keys);
};

store timeline_stratified into '$output/timeline-stratified';

stratified = FOREACH group_geo {
    group_ = $0;
    entries = $1;
    poi_ids = DISTINCT entries.poi_3::id;
    edits = DISTINCT entries.id_version;
    users = DISTINCT entries.uid;
    changesets = DISTINCT entries.changeset;
    tag_keys = DISTINCT entries.key;
   GENERATE flatten(group_) as (latitude, longitude), COUNT(poi_ids), COUNT(edits), COUNT(users), COUNT(changesets), COUNT(tag_keys);
};

store stratified into '$output/stratified';

