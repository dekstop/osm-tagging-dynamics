node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
node_tag = LOAD '$input_node_tag' AS (id:long, version:int, key:chararray, value:chararray);

filtered_node = FILTER node BY 
  ($minlat <= latitude) AND (latitude <= $maxlat) AND
  ($minlon <= longitude) AND (longitude <= $maxlon);
filtered_node_group = GROUP filtered_node BY id;
filtered_id = FOREACH filtered_node_group GENERATE $0;
-- dump filtered_id;

-- region_node_join = JOIN node BY id, filtered_id BY $0 USING 'replicated';
region_node_join = COGROUP node BY id, filtered_id BY $0;
region_node = FOREACH region_node_join GENERATE FLATTEN($1);
store region_node into '$output_node';
-- dump region_nodel

-- region_tag_join = JOIN node_tag BY id, filtered_id BY $0 USING 'replicated';
region_tag_join = COGROUP node_tag BY id, filtered_id BY $0;
region_tag = FOREACH region_tag_join GENERATE FLATTEN($1);
store region_tag into '$output_node_tag';
-- dump region_tag;
