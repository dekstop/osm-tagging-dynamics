-- Extract POI data from raw node/tag data:
-- - remove nodes without key fields: lat/lon, uid/username, timestamp, changeset, ...
-- - remove 'created_by' tag
-- - remove nodes without any tags
-- - ...?

-- parameters:
-- $input_node      directory of node data
-- $input_node_tag  directory of node_tag data
-- $output          output directory

SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

clean_node = FILTER node BY (
    changeset IS NOT NULL AND 
    timestamp IS NOT NULL AND 
    uid IS NOT NULL AND
    username IS NOT NULL AND
    latitude IS NOT NULL AND 
    longitude IS NOT NULL);

node_tag = LOAD '$input_node_tag' AS (id:long, version:int, key:chararray, value:chararray);

clean_node_tag = FILTER node_tag BY (
    key IS NOT NULL AND 
    key!='created_by');

-- IDs for all POI (nodes with tags)
filtered_poi_id_version_group = COGROUP clean_node BY (id, version) INNER, clean_node_tag BY (id, version) INNER;
filtered_poi_id_version = FOREACH filtered_poi_id_version_group GENERATE $0;
store filtered_poi_id_version into '$output/poi_id';

-- poi
poi_join = COGROUP clean_node BY (id, version) INNER, filtered_poi_id_version BY ($0.id, $0.version) INNER;
poi = FOREACH poi_join GENERATE FLATTEN($1);
store poi into '$output/poi';

-- poi_tag
poi_tag_join = COGROUP clean_node_tag BY (id, version) INNER, filtered_poi_id_version BY ($0.id, $0.version) INNER;
poi_tag = FOREACH poi_tag_join GENERATE FLATTEN($1);
store poi_tag into '$output/poi_tag';
