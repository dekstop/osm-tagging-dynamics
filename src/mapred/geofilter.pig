-- Extract POI in particular regions from node/node_tag data sets.
-- Pig doesn't allow for easy parametrisation with lists, so regions are hardcoded.

-- parameters:
-- $input_node
-- $input_node_tag
-- $output

SET default_parallel 10;
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

-- Generated from outputs/20130904-cultures/5-country-bounding-boxes.geojson with a short Ruby script
-- 2013-09-05 18:43:28
filtered_node = FILTER node BY 
((7.71249215603978 <= latitude) AND (latitude <= 11.5431186830559) AND (54.8372531446962 <= longitude) AND (longitude <= 57.6682401484525)) OR 
((10.9077503408344 <= latitude) AND (latitude <= 12.6204823937791) AND (54.5896960489239 <= longitude) AND (longitude <= 56.0666945024358)) OR 
((14.5173791835996 <= latitude) AND (latitude <= 15.2908710784778) AND (54.9297392541263 <= longitude) AND (longitude <= 55.3403140317345)) OR 
((26.8011671332136 <= latitude) AND (latitude <= 30.8527913444806) AND (51.5253702014124 <= longitude) AND (longitude <= 55.8501971262602)) OR 
((30.8159583971055 <= latitude) AND (latitude <= 32.4181916079247) AND (53.0689964521429 <= longitude) AND (longitude <= 54.0303216000302)) OR 
((30.8343748707931 <= latitude) AND (latitude <= 31.663116186734) AND (52.0267412085142 <= longitude) AND (longitude <= 53.057129874723)) OR 
((25.7330116593342 <= latitude) AND (latitude <= 26.8195836069012) AND (51.6969180978459 <= longitude) AND (longitude <= 55.182900316583)) OR 
((23.5230348168249 <= latitude) AND (latitude <= 26.1565905541484) AND (51.8336899279967 <= longitude) AND (longitude <= 53.9335495120916)) OR 
((30.7975419234179 <= latitude) AND (latitude <= 31.3316196603577) AND (54.0093759436495 <= longitude) AND (longitude <= 54.4614424769379)) OR 
((24.867437396018 <= latitude) AND (latitude <= 25.696178711959) AND (53.9335495120916 <= longitude) AND (longitude <= 54.1713968940168)) OR 
((27.8877390807807 <= latitude) AND (latitude <= 29.268974607349) AND (55.8191700143212 <= longitude) AND (longitude <= 56.0769737136014)) OR 
((69.7483837726438 <= latitude) AND (latitude <= 79.8037784060611) AND (8.13674725047218 <= longitude) AND (longitude <= 27.4871162706947)) OR 
((79.7301125113108 <= latitude) AND (latitude <= 88.2016904075963) AND (11.4031669337774 <= longitude) AND (longitude <= 26.5354951040776)) OR 
((74.0946715629121 <= latitude) AND (latitude <= 79.2144512480586) AND (26.7330417534582 <= longitude) AND (longitude <= 34.7622261227104)) OR 
((72.1425253520289 <= latitude) AND (latitude <= 81.1297645115666) AND (27.4871162706947 <= longitude) AND (longitude <= 28.94756203086)) OR 
((89.9696718816037 <= latitude) AND (latitude <= 94.8684538824993) AND (25.3431233392835 <= longitude) AND (longitude <= 26.6672308349774)) OR 
((92.2533146188633 <= latitude) AND (latitude <= 96.8206000933825) AND (26.6352883742406 <= longitude) AND (longitude <= 28.4283518818448)) OR 
((92.179648724113 <= latitude) AND (latitude <= 94.0581290402459) AND (22.5477922864279 <= longitude) AND (longitude <= 25.3443107273072)) OR 
((116.268396307464 <= latitude) AND (latitude <= 128.423268941265) AND (7.69896671612785 <= longitude) AND (longitude <= 21.2852292783981)) OR 
((119.509695676478 <= latitude) AND (latitude <= 127.207781677885) AND (4.32948331798473 <= longitude) AND (longitude <= 8.06381632807494)) OR 
((-91.9574634411287 <= latitude) AND (latitude <= -89.7843195459945) AND (13.9185579901049 <= longitude) AND (longitude <= 16.0178314768882)) OR 
((-90.9261409146243 <= latitude) AND (latitude <= -89.1765759143045) AND (16.0355321616719 <= longitude) AND (longitude <= 17.7623354560607)) OR 
((-89.7659030723069 <= latitude) AND (latitude <= -89.0476605984914) AND (14.382345153445 <= longitude) AND (longitude <= 16.0181453961979)) OR 
((-89.1029100195542 <= latitude) AND (latitude <= -88.3846675457387) AND (15.4328374170771 <= longitude) AND (longitude <= 15.9115944522842));

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
