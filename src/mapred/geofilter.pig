-- Extract POI in particular regions from node/node_tag data sets.
-- Pig doesn't allow for easy parametrisation with lists, so regions are hardcoded.

-- parameters:
-- $input_node
-- $input_node_tag
-- $output

SET DEFAULT_PARALLEL 20;
SET output.compression.enabled true; 
SET output.compression.codec org.apache.hadoop.io.compress.LzopCodec;

node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
clean_node = FILTER node BY (latitude IS NOT NULL AND longitude IS NOT NULL);

node_tag = LOAD '$input_node_tag' AS (id:long, version:int, key:chararray, value:chararray);
clean_node_tag = FILTER node_tag BY (key!='created_by');

-- POI IDs
-- filtered_node = FILTER clean_node BY 
--   ((51.0 <= latitude) AND (latitude <= 52.0) AND (-5.0 <= longitude) AND (longitude <= 0.0)) OR
--   ((50.0 <= latitude) AND (latitude <= 53.0) AND (8.0 <= longitude) AND (longitude <= 21.0));

-- Generated from ../outputs/20130822 global/data/geo_poi_edit_stats-03.txt
-- Tue Aug 27 18:45:57 +0100 2013
filtered_node = FILTER clean_node BY 
  ((-30.75 <= latitude) AND (latitude <= -28.75) AND (134.75 <= longitude) AND (longitude <= 136.25)) OR 
  ((12.75 <= latitude) AND (latitude <= 18.25) AND (42.75 <= longitude) AND (longitude <= 50.25)) OR 
  ((12.75 <= latitude) AND (latitude <= 14.25) AND (-59.75 <= longitude) AND (longitude <= -58.75)) OR 
  ((44.25 <= latitude) AND (latitude <= 61.75) AND (19.25 <= longitude) AND (longitude <= 44.25)) OR 
  ((61.25 <= latitude) AND (latitude <= 64.25) AND (65.75 <= longitude) AND (longitude <= 67.25)) OR 
  ((39.75 <= latitude) AND (latitude <= 45.25) AND (18.75 <= longitude) AND (longitude <= 22.75)) OR 
  ((59.75 <= latitude) AND (latitude <= 61.25) AND (69.75 <= longitude) AND (longitude <= 70.75)) OR 
  ((66.75 <= latitude) AND (latitude <= 68.25) AND (24.75 <= longitude) AND (longitude <= 26.25)) OR 
  ((9.25 <= latitude) AND (latitude <= 18.25) AND (119.75 <= longitude) AND (longitude <= 126.75)) OR 
  ((24.25 <= latitude) AND (latitude <= 25.25) AND (-82.25 <= longitude) AND (longitude <= -80.75)) OR 
  ((42.75 <= latitude) AND (latitude <= 43.75) AND (133.25 <= longitude) AND (longitude <= 134.75)) OR 
  ((55.25 <= latitude) AND (latitude <= 60.75) AND (6.75 <= longitude) AND (longitude <= 13.25)) OR 
  ((56.25 <= latitude) AND (latitude <= 62.25) AND (-0.75 <= longitude) AND (longitude <= 3.25)) OR 
  ((-18.25 <= latitude) AND (latitude <= -16.75) AND (139.25 <= longitude) AND (longitude <= 141.25)) OR 
  ((68.75 <= latitude) AND (latitude <= 71.75) AND (19.25 <= longitude) AND (longitude <= 33.25)) OR 
  ((32.25 <= latitude) AND (latitude <= 33.25) AND (32.25 <= longitude) AND (longitude <= 33.25)) OR 
  ((62.25 <= latitude) AND (latitude <= 63.25) AND (74.25 <= longitude) AND (longitude <= 75.25)) OR 
  ((12.75 <= latitude) AND (latitude <= 17.25) AND (144.25 <= longitude) AND (longitude <= 146.75)) OR 
  ((65.75 <= latitude) AND (latitude <= 66.75) AND (-150.25 <= longitude) AND (longitude <= -149.25)) OR 
  ((59.25 <= latitude) AND (latitude <= 60.25) AND (51.75 <= longitude) AND (longitude <= 52.75)) OR 
  ((43.25 <= latitude) AND (latitude <= 44.25) AND (87.75 <= longitude) AND (longitude <= 88.75)) OR 
  ((-22.25 <= latitude) AND (latitude <= -19.25) AND (163.25 <= longitude) AND (longitude <= 166.25)) OR 
  ((63.25 <= latitude) AND (latitude <= 64.25) AND (-150.25 <= longitude) AND (longitude <= -148.75)) OR 
  ((52.75 <= latitude) AND (latitude <= 57.25) AND (49.25 <= longitude) AND (longitude <= 59.75)) OR 
  ((-26.25 <= latitude) AND (latitude <= -22.75) AND (22.75 <= longitude) AND (longitude <= 27.75)) OR 
  ((-28.25 <= latitude) AND (latitude <= -26.25) AND (29.25 <= longitude) AND (longitude <= 31.75)) OR 
  ((60.25 <= latitude) AND (latitude <= 61.25) AND (-4.25 <= longitude) AND (longitude <= -3.25)) OR 
  ((43.25 <= latitude) AND (latitude <= 49.75) AND (4.25 <= longitude) AND (longitude <= 7.75)) OR 
  ((59.25 <= latitude) AND (latitude <= 60.25) AND (17.25 <= longitude) AND (longitude <= 18.25)) OR 
  ((45.75 <= latitude) AND (latitude <= 48.75) AND (45.75 <= longitude) AND (longitude <= 49.25)) OR 
  ((19.25 <= latitude) AND (latitude <= 20.25) AND (-80.25 <= longitude) AND (longitude <= -79.25)) OR 
  ((54.25 <= latitude) AND (latitude <= 55.25) AND (-163.75 <= longitude) AND (longitude <= -162.75)) OR 
  ((52.25 <= latitude) AND (latitude <= 54.75) AND (0.25 <= longitude) AND (longitude <= 3.25)) OR 
  ((9.25 <= latitude) AND (latitude <= 19.25) AND (73.75 <= longitude) AND (longitude <= 80.75)) OR 
  ((64.25 <= latitude) AND (latitude <= 65.25) AND (30.25 <= longitude) AND (longitude <= 31.25)) OR 
  ((50.25 <= latitude) AND (latitude <= 51.75) AND (78.25 <= longitude) AND (longitude <= 79.25)) OR 
  ((-17.25 <= latitude) AND (latitude <= -15.25) AND (178.75 <= longitude) AND (longitude <= 180.75)) OR 
  ((27.25 <= latitude) AND (latitude <= 28.75) AND (-16.25 <= longitude) AND (longitude <= -14.75)) OR 
  ((50.25 <= latitude) AND (latitude <= 51.25) AND (-110.75 <= longitude) AND (longitude <= -109.75)) OR 
  ((11.75 <= latitude) AND (latitude <= 12.75) AND (-62.25 <= longitude) AND (longitude <= -60.75)) OR 
  ((51.25 <= latitude) AND (latitude <= 52.25) AND (75.25 <= longitude) AND (longitude <= 76.25)) OR 
  ((42.25 <= latitude) AND (latitude <= 46.25) AND (38.75 <= longitude) AND (longitude <= 44.75)) OR 
  ((-17.25 <= latitude) AND (latitude <= -15.75) AND (127.75 <= longitude) AND (longitude <= 129.25)) OR 
  ((58.25 <= latitude) AND (latitude <= 59.25) AND (27.75 <= longitude) AND (longitude <= 29.25)) OR 
  ((38.25 <= latitude) AND (latitude <= 40.25) AND (-0.75 <= longitude) AND (longitude <= 2.25)) OR 
  ((56.25 <= latitude) AND (latitude <= 57.75) AND (-111.75 <= longitude) AND (longitude <= -110.75)) OR 
  ((25.75 <= latitude) AND (latitude <= 30.25) AND (98.25 <= longitude) AND (longitude <= 100.75)) OR 
  ((63.75 <= latitude) AND (latitude <= 64.75) AND (8.25 <= longitude) AND (longitude <= 9.75)) OR 
  ((27.75 <= latitude) AND (latitude <= 29.25) AND (-108.25 <= longitude) AND (longitude <= -106.75)) OR 
  ((56.25 <= latitude) AND (latitude <= 57.25) AND (47.25 <= longitude) AND (longitude <= 48.25)) OR 
  ((60.75 <= latitude) AND (latitude <= 62.75) AND (44.75 <= longitude) AND (longitude <= 48.75)) OR 
  ((65.75 <= latitude) AND (latitude <= 66.75) AND (-170.25 <= longitude) AND (longitude <= -168.75)) OR 
  ((54.75 <= latitude) AND (latitude <= 56.75) AND (45.25 <= longitude) AND (longitude <= 46.25)) OR 
  ((58.25 <= latitude) AND (latitude <= 59.25) AND (48.75 <= longitude) AND (longitude <= 49.75)) OR 
  ((39.75 <= latitude) AND (latitude <= 40.75) AND (64.25 <= longitude) AND (longitude <= 65.25)) OR 
  ((19.25 <= latitude) AND (latitude <= 20.25) AND (166.25 <= longitude) AND (longitude <= 167.25)) OR 
  ((46.75 <= latitude) AND (latitude <= 47.75) AND (142.25 <= longitude) AND (longitude <= 143.25)) OR 
  ((38.75 <= latitude) AND (latitude <= 41.25) AND (44.25 <= longitude) AND (longitude <= 47.75)) OR 
  ((14.25 <= latitude) AND (latitude <= 16.25) AND (-91.75 <= longitude) AND (longitude <= -88.75)) OR 
  ((-13.25 <= latitude) AND (latitude <= -12.25) AND (14.25 <= longitude) AND (longitude <= 15.25)) OR 
  ((54.75 <= latitude) AND (latitude <= 55.75) AND (-5.75 <= longitude) AND (longitude <= -4.75)) OR 
  ((49.25 <= latitude) AND (latitude <= 50.75) AND (0.25 <= longitude) AND (longitude <= 3.25)) OR 
  ((52.25 <= latitude) AND (latitude <= 53.75) AND (-10.25 <= longitude) AND (longitude <= -8.75)) OR 
  ((14.75 <= latitude) AND (latitude <= 15.75) AND (39.25 <= longitude) AND (longitude <= 40.25)) OR 
  ((-4.25 <= latitude) AND (latitude <= -2.75) AND (38.25 <= longitude) AND (longitude <= 39.75)) OR 
  ((25.75 <= latitude) AND (latitude <= 26.75) AND (90.25 <= longitude) AND (longitude <= 92.25)) OR 
  ((-22.75 <= latitude) AND (latitude <= -21.75) AND (167.25 <= longitude) AND (longitude <= 168.25)) OR 
  ((62.75 <= latitude) AND (latitude <= 63.75) AND (104.25 <= longitude) AND (longitude <= 105.25)) OR 
  ((34.75 <= latitude) AND (latitude <= 36.25) AND (23.75 <= longitude) AND (longitude <= 26.75)) OR 
  ((61.25 <= latitude) AND (latitude <= 63.25) AND (4.25 <= longitude) AND (longitude <= 7.75)) OR 
  ((12.25 <= latitude) AND (latitude <= 13.25) AND (-70.25 <= longitude) AND (longitude <= -67.75)) OR 
  ((-18.25 <= latitude) AND (latitude <= -17.25) AND (145.25 <= longitude) AND (longitude <= 146.25)) OR 
  ((6.75 <= latitude) AND (latitude <= 7.75) AND (20.75 <= longitude) AND (longitude <= 21.75)) OR 
  ((57.75 <= latitude) AND (latitude <= 59.25) AND (56.75 <= longitude) AND (longitude <= 58.25)) OR 
  ((-40.75 <= latitude) AND (latitude <= -39.25) AND (147.25 <= longitude) AND (longitude <= 149.25)) OR 
  ((5.75 <= latitude) AND (latitude <= 7.25) AND (-2.75 <= longitude) AND (longitude <= -0.25)) OR 
  ((32.75 <= latitude) AND (latitude <= 33.75) AND (-16.75 <= longitude) AND (longitude <= -15.75)) OR 
  ((27.25 <= latitude) AND (latitude <= 28.75) AND (-18.25 <= longitude) AND (longitude <= -17.25)) OR 
  ((22.75 <= latitude) AND (latitude <= 23.75) AND (59.25 <= longitude) AND (longitude <= 60.25)) OR 
  ((19.75 <= latitude) AND (latitude <= 20.75) AND (92.25 <= longitude) AND (longitude <= 93.25)) OR 
  ((63.75 <= latitude) AND (latitude <= 66.25) AND (14.75 <= longitude) AND (longitude <= 17.25)) OR 
  ((41.75 <= latitude) AND (latitude <= 44.25) AND (0.75 <= longitude) AND (longitude <= 4.25)) OR 
  ((18.25 <= latitude) AND (latitude <= 19.25) AND (-70.25 <= longitude) AND (longitude <= -69.25)) OR 
  ((63.25 <= latitude) AND (latitude <= 64.25) AND (-144.25 <= longitude) AND (longitude <= -142.25)) OR 
  ((11.25 <= latitude) AND (latitude <= 12.25) AND (92.25 <= longitude) AND (longitude <= 93.75)) OR 
  ((51.75 <= latitude) AND (latitude <= 52.75) AND (-7.25 <= longitude) AND (longitude <= -6.25));

-- ID whitelists: all nodes, and POI (nodes with tags)
filtered_node_group = GROUP filtered_node BY id;
filtered_node_id = FOREACH filtered_node_group GENERATE $0;
store filtered_node_id into '$output/node_id';

filtered_poi_id_group = COGROUP filtered_node_id BY $0 INNER, clean_node_tag BY id INNER;
filtered_poi_id = FOREACH filtered_poi_id_group GENERATE $0;
store filtered_poi_id into '$output/poi_id';

-- node
region_node_join = COGROUP clean_node BY id INNER, filtered_poi_id BY $0 INNER;
region_node = FOREACH region_node_join GENERATE FLATTEN($1);
store region_node into '$output/poi';

-- node_tag
region_tag_join = COGROUP clean_node_tag BY id INNER, filtered_poi_id BY $0 INNER;
region_tag = FOREACH region_tag_join GENERATE FLATTEN($1);
store region_tag into '$output/poi_tag';
