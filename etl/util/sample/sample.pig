-- Produce a sampled subset of data based on a given percentage of users.

-- parameters:
-- $input_poi       directory of poi data
-- $input_poi_tag   directory of poi_tag data
-- $sample          [0..1] fraction, size of user subset
-- $output          output root directory

SET default_parallel 15;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
poi_tag = LOAD '$input_poi_tag' AS (id:long, version:int, key:chararray, value:chararray);

-- select users
uids = FOREACH poi GENERATE uid;
uids = DISTINCT uids;
uids = SAMPLE uids $sample;

-- filter
poi_sample = JOIN poi BY uid, uids BY uid;
poi_sample = FOREACH poi_sample GENERATE poi::id, poi::version, poi::changeset, poi::timestamp, poi::uid, poi::username, poi::latitude, poi::longitude;
store poi_sample into '$output/poi';

poi_id_version = FOREACH poi_sample GENERATE id, version;
poi_tag_sample = JOIN poi_tag BY (id, version), poi_id_version BY (id, version);
poi_tag_sample = FOREACH poi_tag_sample GENERATE poi_tag::id, poi_tag::version, poi_tag::key, poi_tag::value;
store poi_tag_sample into '$output/poi_tag';

