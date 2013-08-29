-- Extract POI in particular regions from node/node_tag data sets.
-- Pig doesn't allow for easy parametrisation with lists, so regions are hardcoded.

-- parameters:
-- $input_node
-- $input_node_tag
-- $output

SET DEFAULT_PARALLEL 20;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
clean_node = FILTER node BY (latitude IS NOT NULL AND longitude IS NOT NULL);

node_tag = LOAD '$input_node_tag' AS (id:long, version:int, key:chararray, value:chararray);
clean_node_tag = FILTER node_tag BY (key!='created_by');

-- POI IDs
-- filtered_node = FILTER clean_node BY 
--   ((51.0 <= latitude) AND (latitude <= 52.0) AND (-5.0 <= longitude) AND (longitude <= 0.0)) OR
--   ((50.0 <= latitude) AND (latitude <= 53.0) AND (8.0 <= longitude) AND (longitude <= 21.0));

-- Generated from data/edit_hotspot_stats-20130829-01.txt
-- Fri Aug 30 00:23:12 +0100 2013
filtered_node = FILTER node BY 
  ((61.5 <= latitude) AND (latitude <= 66.5) AND (13.0 <= longitude) AND (longitude <= 17.5)) OR 
  ((38.5 <= latitude) AND (latitude <= 65.0) AND (4.5 <= longitude) AND (longitude <= 46.5)) OR 
  ((52.0 <= latitude) AND (latitude <= 53.0) AND (107.5 <= longitude) AND (longitude <= 108.5)) OR 
  ((34.5 <= latitude) AND (latitude <= 36.5) AND (33.0 <= longitude) AND (longitude <= 35.0)) OR 
  ((63.5 <= latitude) AND (latitude <= 65.5) AND (40.0 <= longitude) AND (longitude <= 43.0)) OR 
  ((31.5 <= latitude) AND (latitude <= 32.5) AND (118.0 <= longitude) AND (longitude <= 119.0)) OR 
  ((61.5 <= latitude) AND (latitude <= 64.5) AND (66.0 <= longitude) AND (longitude <= 67.5)) OR 
  ((8.0 <= latitude) AND (latitude <= 18.0) AND (120.0 <= longitude) AND (longitude <= 127.0)) OR 
  ((43.0 <= latitude) AND (latitude <= 50.0) AND (4.0 <= longitude) AND (longitude <= 10.0)) OR 
  ((56.5 <= latitude) AND (latitude <= 62.5) AND (-2.0 <= longitude) AND (longitude <= 3.5)) OR 
  ((11.5 <= latitude) AND (latitude <= 18.5) AND (43.0 <= longitude) AND (longitude <= 50.5)) OR 
  ((58.5 <= latitude) AND (latitude <= 59.5) AND (28.0 <= longitude) AND (longitude <= 29.5)) OR 
  ((28.0 <= latitude) AND (latitude <= 29.5) AND (-108.0 <= longitude) AND (longitude <= -106.5)) OR 
  ((60.0 <= latitude) AND (latitude <= 61.5) AND (70.0 <= longitude) AND (longitude <= 71.0)) OR 
  ((45.5 <= latitude) AND (latitude <= 55.0) AND (-5.0 <= longitude) AND (longitude <= 4.0)) OR 
  ((42.0 <= latitude) AND (latitude <= 44.5) AND (1.0 <= longitude) AND (longitude <= 4.5)) OR 
  ((40.0 <= latitude) AND (latitude <= 41.0) AND (-8.0 <= longitude) AND (longitude <= -7.0)) OR 
  ((43.0 <= latitude) AND (latitude <= 44.0) AND (-88.0 <= longitude) AND (longitude <= -87.0)) OR 
  ((9.0 <= latitude) AND (latitude <= 19.5) AND (74.0 <= longitude) AND (longitude <= 81.0)) OR 
  ((52.5 <= latitude) AND (latitude <= 55.0) AND (-10.0 <= longitude) AND (longitude <= -8.5)) OR 
  ((26.0 <= latitude) AND (latitude <= 27.5) AND (56.5 <= longitude) AND (longitude <= 57.5)) OR 
  ((-23.5 <= latitude) AND (latitude <= -22.5) AND (148.0 <= longitude) AND (longitude <= 149.0)) OR 
  ((58.5 <= latitude) AND (latitude <= 60.5) AND (49.0 <= longitude) AND (longitude <= 53.5)) OR 
  ((1.5 <= latitude) AND (latitude <= 3.0) AND (36.5 <= longitude) AND (longitude <= 38.0)) OR 
  ((53.0 <= latitude) AND (latitude <= 57.5) AND (53.5 <= longitude) AND (longitude <= 60.0)) OR 
  ((62.5 <= latitude) AND (latitude <= 63.5) AND (74.5 <= longitude) AND (longitude <= 75.5)) OR 
  ((26.0 <= latitude) AND (latitude <= 27.0) AND (90.5 <= longitude) AND (longitude <= 92.5)) OR 
  ((59.0 <= latitude) AND (latitude <= 60.0) AND (22.5 <= longitude) AND (longitude <= 24.0)) OR 
  ((43.0 <= latitude) AND (latitude <= 45.5) AND (131.5 <= longitude) AND (longitude <= 135.0)) OR 
  ((69.0 <= latitude) AND (latitude <= 72.0) AND (19.0 <= longitude) AND (longitude <= 33.5)) OR 
  ((59.0 <= latitude) AND (latitude <= 60.5) AND (17.5 <= longitude) AND (longitude <= 18.5)) OR 
  ((14.0 <= latitude) AND (latitude <= 17.0) AND (-92.0 <= longitude) AND (longitude <= -86.0)) OR 
  ((40.0 <= latitude) AND (latitude <= 41.0) AND (46.5 <= longitude) AND (longitude <= 48.0)) OR 
  ((32.5 <= latitude) AND (latitude <= 34.0) AND (-117.5 <= longitude) AND (longitude <= -116.0)) OR 
  ((40.0 <= latitude) AND (latitude <= 42.0) AND (25.0 <= longitude) AND (longitude <= 30.0)) OR 
  ((47.0 <= latitude) AND (latitude <= 48.0) AND (142.5 <= longitude) AND (longitude <= 143.5)) OR 
  ((46.0 <= latitude) AND (latitude <= 49.0) AND (46.0 <= longitude) AND (longitude <= 49.5)) OR 
  ((-24.5 <= latitude) AND (latitude <= -23.5) AND (26.0 <= longitude) AND (longitude <= 27.0)) OR 
  ((36.5 <= latitude) AND (latitude <= 37.5) AND (67.0 <= longitude) AND (longitude <= 68.0)) OR 
  ((-14.0 <= latitude) AND (latitude <= -12.5) AND (131.5 <= longitude) AND (longitude <= 133.0)) OR 
  ((25.0 <= latitude) AND (latitude <= 26.0) AND (104.0 <= longitude) AND (longitude <= 105.0)) OR 
  ((40.0 <= latitude) AND (latitude <= 41.0) AND (64.5 <= longitude) AND (longitude <= 65.5)) OR 
  ((42.5 <= latitude) AND (latitude <= 45.0) AND (44.0 <= longitude) AND (longitude <= 45.0)) OR 
  ((37.5 <= latitude) AND (latitude <= 41.5) AND (-0.5 <= longitude) AND (longitude <= 2.0)) OR 
  ((13.5 <= latitude) AND (latitude <= 17.5) AND (144.5 <= longitude) AND (longitude <= 147.0)) OR 
  ((21.5 <= latitude) AND (latitude <= 24.0) AND (59.5 <= longitude) AND (longitude <= 60.5)) OR 
  ((40.5 <= latitude) AND (latitude <= 41.5) AND (71.0 <= longitude) AND (longitude <= 72.0)) OR 
  ((6.0 <= latitude) AND (latitude <= 7.5) AND (-2.5 <= longitude) AND (longitude <= 0.0)) OR 
  ((49.0 <= latitude) AND (latitude <= 50.0) AND (16.5 <= longitude) AND (longitude <= 17.5)) OR 
  ((35.0 <= latitude) AND (latitude <= 38.0) AND (23.0 <= longitude) AND (longitude <= 25.5)) OR 
  ((-27.5 <= latitude) AND (latitude <= -25.0) AND (153.0 <= longitude) AND (longitude <= 154.5)) OR 
  ((-30.5 <= latitude) AND (latitude <= -28.5) AND (135.0 <= longitude) AND (longitude <= 136.5)) OR 
  ((19.5 <= latitude) AND (latitude <= 20.5) AND (166.5 <= longitude) AND (longitude <= 167.5)) OR 
  ((32.5 <= latitude) AND (latitude <= 34.0) AND (-17.0 <= longitude) AND (longitude <= -15.5)) OR 
  ((58.0 <= latitude) AND (latitude <= 59.5) AND (57.0 <= longitude) AND (longitude <= 58.5)) OR 
  ((28.0 <= latitude) AND (latitude <= 29.0) AND (84.0 <= longitude) AND (longitude <= 85.0)) OR 
  ((27.5 <= latitude) AND (latitude <= 30.0) AND (-18.0 <= longitude) AND (longitude <= -13.0)) OR 
  ((16.5 <= latitude) AND (latitude <= 17.5) AND (-95.0 <= longitude) AND (longitude <= -94.0)) OR 
  ((18.0 <= latitude) AND (latitude <= 21.0) AND (-74.0 <= longitude) AND (longitude <= -71.5)) OR 
  ((-27.0 <= latitude) AND (latitude <= -26.0) AND (28.0 <= longitude) AND (longitude <= 29.0)) OR 
  ((-4.0 <= latitude) AND (latitude <= -2.5) AND (38.5 <= longitude) AND (longitude <= 40.0)) OR 
  ((11.5 <= latitude) AND (latitude <= 12.5) AND (92.5 <= longitude) AND (longitude <= 94.0)) OR 
  ((1.5 <= latitude) AND (latitude <= 2.5) AND (103.5 <= longitude) AND (longitude <= 104.5)) OR 
  ((20.0 <= latitude) AND (latitude <= 21.0) AND (92.5 <= longitude) AND (longitude <= 93.5)) OR 
  ((55.0 <= latitude) AND (latitude <= 57.5) AND (-5.5 <= longitude) AND (longitude <= -3.5)) OR 
  ((52.0 <= latitude) AND (latitude <= 53.0) AND (-7.0 <= longitude) AND (longitude <= -6.0)) OR 
  ((8.5 <= latitude) AND (latitude <= 10.5) AND (-84.5 <= longitude) AND (longitude <= -82.0)) OR 
  ((12.0 <= latitude) AND (latitude <= 13.5) AND (-70.0 <= longitude) AND (longitude <= -67.5)) OR 
  ((19.5 <= latitude) AND (latitude <= 20.5) AND (-81.5 <= longitude) AND (longitude <= -80.0)) OR 
  ((-25.5 <= latitude) AND (latitude <= -24.5) AND (131.0 <= longitude) AND (longitude <= 132.0)) OR 
  ((15.0 <= latitude) AND (latitude <= 16.0) AND (39.5 <= longitude) AND (longitude <= 40.5)) OR 
  ((-9.5 <= latitude) AND (latitude <= -8.5) AND (147.0 <= longitude) AND (longitude <= 148.0)) OR 
  ((26.5 <= latitude) AND (latitude <= 27.5) AND (-97.5 <= longitude) AND (longitude <= -96.5)) OR 
  ((63.5 <= latitude) AND (latitude <= 65.5) AND (29.0 <= longitude) AND (longitude <= 31.5)) OR 
  ((12.0 <= latitude) AND (latitude <= 13.0) AND (-62.0 <= longitude) AND (longitude <= -60.5)) OR 
  ((54.5 <= latitude) AND (latitude <= 57.5) AND (49.5 <= longitude) AND (longitude <= 52.0)) OR 
  ((13.0 <= latitude) AND (latitude <= 14.5) AND (-59.5 <= longitude) AND (longitude <= -58.5)) OR 
  ((36.0 <= latitude) AND (latitude <= 37.0) AND (28.0 <= longitude) AND (longitude <= 29.0)) OR 
  ((32.5 <= latitude) AND (latitude <= 33.5) AND (32.5 <= longitude) AND (longitude <= 33.5)) OR 
  ((24.0 <= latitude) AND (latitude <= 25.0) AND (57.0 <= longitude) AND (longitude <= 58.5)) OR 
  ((50.5 <= latitude) AND (latitude <= 51.5) AND (78.5 <= longitude) AND (longitude <= 79.5)) OR 
  ((-10.5 <= latitude) AND (latitude <= -9.5) AND (142.5 <= longitude) AND (longitude <= 143.5)) OR 
  ((41.5 <= latitude) AND (latitude <= 43.5) AND (9.0 <= longitude) AND (longitude <= 10.5)) OR 
  ((61.0 <= latitude) AND (latitude <= 62.5) AND (46.0 <= longitude) AND (longitude <= 49.0)) OR 
  ((63.0 <= latitude) AND (latitude <= 64.0) AND (104.5 <= longitude) AND (longitude <= 105.5)) OR 
  ((18.5 <= latitude) AND (latitude <= 21.0) AND (-70.5 <= longitude) AND (longitude <= -69.0)) OR 
  ((51.5 <= latitude) AND (latitude <= 52.5) AND (75.5 <= longitude) AND (longitude <= 76.5)) OR 
  ((52.5 <= latitude) AND (latitude <= 53.5) AND (-3.5 <= longitude) AND (longitude <= -2.5)) OR 
  ((-13.5 <= latitude) AND (latitude <= -11.5) AND (48.5 <= longitude) AND (longitude <= 50.5)) OR 
  ((31.5 <= latitude) AND (latitude <= 32.5) AND (-10.0 <= longitude) AND (longitude <= -9.0)) OR 
  ((36.0 <= latitude) AND (latitude <= 37.5) AND (-6.5 <= longitude) AND (longitude <= -4.5)) OR 
  ((55.0 <= latitude) AND (latitude <= 56.0) AND (47.5 <= longitude) AND (longitude <= 48.5)) OR 
  ((43.5 <= latitude) AND (latitude <= 44.5) AND (88.0 <= longitude) AND (longitude <= 89.0)) OR 
  ((60.5 <= latitude) AND (latitude <= 61.5) AND (-4.0 <= longitude) AND (longitude <= -3.0)) OR 
  ((52.5 <= latitude) AND (latitude <= 53.5) AND (85.0 <= longitude) AND (longitude <= 86.0)) OR 
  ((54.5 <= latitude) AND (latitude <= 55.5) AND (-3.0 <= longitude) AND (longitude <= -2.0));

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
