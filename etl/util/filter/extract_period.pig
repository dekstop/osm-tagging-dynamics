-- Extract a subset of POI/tag data: only include edits within a given timeframe.

-- parameters:
-- $input_poi       directory of poi data
-- $input_poi_tag   directory of poi_tag data
-- $fromdate        YYYY-MM-DDThh:mm:ss
-- $todate          YYYY-MM-DDThh:mm:ss
-- $output          output directory

SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

poi_tag = LOAD '$input_poi_tag' AS (id:long, version:int, key:chararray, value:chararray);

-- poi
poi_subset = FILTER poi BY (
    ToDate(timestamp) >= ToDate('$fromdate') AND
    ToDate(timestamp) < ToDate('$todate'));
store poi_subset into '$output/poi';

poi_id_version = FOREACH poi_subset GENERATE id, version;

-- poi_tag
poi_tag_subset = COGROUP poi_tag BY (id, version) INNER, poi_id_version BY (id, version) INNER;
DESCRIBE poi_tag_subset;
poi_tag_subset = FOREACH poi_tag_subset GENERATE FLATTEN($1);
store poi_tag_subset into '$output/poi_tag';
