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

-- Generated from outputs/20131011-cultures/more_countries-bboxes.geojson with a short Ruby script
-- 2013-10-11 14:07:21
filtered_node = FILTER clean_node BY 
((54.5878846194077 <= latitude) AND (latitude <= 54.8539348336901) AND (8.18705024106041 <= longitude) AND (longitude <= 10.1138987626811)) OR 
((48.3195803283613 <= latitude) AND (latitude <= 49.158041609736) AND (12.8751775018237 <= longitude) AND (longitude <= 13.3589051641553)) OR 
((48.8678050123371 <= latitude) AND (latitude <= 49.5772722504233) AND (12.2302072853817 <= longitude) AND (longitude <= 12.8106804801795)) OR 
((50.5447275750865 <= latitude) AND (latitude <= 51.1574492807064) AND (11.9722191988048 <= longitude) AND (longitude <= 13.1976626100448)) OR 
((47.610113090275 <= latitude) AND (latitude <= 48.7388109690487) AND (7.68316725946504 <= longitude) AND (longitude <= 8.26364045426291)) OR 
((47.610113090275 <= latitude) AND (latitude <= 49.0290475664476) AND (8.1991434326187 <= longitude) AND (longitude <= 13.0364200559342)) OR 
((49.0612960772697 <= latitude) AND (latitude <= 50.9639582157738) AND (6.4577238482251 <= longitude) AND (longitude <= 12.2302072853817)) OR 
((49.8030118261781 <= latitude) AND (latitude <= 51.8669165187927) AND (6.16748725082617 <= longitude) AND (longitude <= 7.13494257548928)) OR 
((50.8994611941296 <= latitude) AND (latitude <= 52.6086322677011) AND (14.0361238914195 <= longitude) AND (longitude <= 14.7778396403278)) OR 
((50.8994611941296 <= latitude) AND (latitude <= 54.6402884494936) AND (7.10269406466717 <= longitude) AND (longitude <= 14.2618634671742)) OR 
((-14.0812881124093 <= latitude) AND (latitude <= -9.95347872718002) AND (129.518041145373 <= longitude) AND (longitude <= 144.545847188473)) OR 
((-44.1369001986099 <= latitude) AND (latitude <= -12.4043655496599) AND (111.84585721486 <= longitude) AND (longitude <= 155.3813468247)) OR 
((56.1149959576048 <= latitude) AND (latitude <= 56.4050386996006) AND (25.0023309578853 <= longitude) AND (longitude <= 26.1401909457149)) OR 
((56.0480630171443 <= latitude) AND (latitude <= 56.7843253622105) AND (27.724270536615 <= longitude) AND (longitude <= 28.0143132786107)) OR 
((55.780331255302 <= latitude) AND (latitude <= 57.5652096675837) AND (25.9840140846403 <= longitude) AND (longitude <= 27.7465815167685)) OR 
((56.3157947789865 <= latitude) AND (latitude <= 57.8998743698865) AND (20.9194215897909 <= longitude) AND (longitude <= 25.9840140846403)) OR 
((41.4566819967413 <= latitude) AND (latitude <= 42.7730298257991) AND (-0.83378405989242 <= longitude) AND (longitude <= 0.683362590547034)) OR 
((38.6678094775511 <= latitude) AND (latitude <= 42.3491212028821) AND (-0.253698575900867 <= longitude) AND (longitude <= 4.34236333572454)) OR 
((41.8582796395047 <= latitude) AND (latitude <= 42.9738286471807) AND (-1.81546718664736 <= longitude) AND (longitude <= -0.744540139278335)) OR 
((36.94986400573 <= latitude) AND (latitude <= 37.976169092792) AND (-7.34859026472066 <= longitude) AND (longitude <= -6.45615105857981)) OR 
((38.1992788943272 <= latitude) AND (latitude <= 38.8016753584723) AND (-7.21472438379953 <= longitude) AND (longitude <= -6.50077301888685)) OR 
((39.1809620210821 <= latitude) AND (latitude <= 39.6494926043061) AND (-7.43783418533475 <= longitude) AND (longitude <= -6.6569498799615)) OR 
((36.8606200851159 <= latitude) AND (latitude <= 41.2112612150526) AND (-6.85774870134319 <= longitude) AND (longitude <= -6.32228517765868)) OR 
((36.1020467598962 <= latitude) AND (latitude <= 41.9029015998117) AND (-6.36690713796572 <= longitude) AND (longitude <= 0.103277106555478)) OR 
((41.8359686593512 <= latitude) AND (latitude <= 43.9332007937822) AND (-9.5796882800728 <= longitude) AND (longitude <= -1.79315620649384)) OR 
((54.3524285254767 <= latitude) AND (latitude <= 55.0886908705429) AND (-7.90636476855871 <= longitude) AND (longitude <= -6.70157184026855)) OR 
((54.1070077437879 <= latitude) AND (latitude <= 54.6424712674724) AND (-6.88005968149673 <= longitude) AND (longitude <= -5.36291303105727)) OR 
((51.3404462047513 <= latitude) AND (latitude <= 53.5492332399499) AND (-5.20673616998262 <= longitude) AND (longitude <= -4.1358091226136)) OR 
((54.6201602873189 <= latitude) AND (latitude <= 55.4902885133062) AND (-6.88005968149673 <= longitude) AND (longitude <= -4.11349814246008)) OR 
((50.4480069986104 <= latitude) AND (latitude <= 51.3850681650583) AND (-2.30630875002485 <= longitude) AND (longitude <= 1.41962493561322)) OR 
((49.9125434749259 <= latitude) AND (latitude <= 51.3850681650583) AND (-5.92068753489531 <= longitude) AND (longitude <= -2.28399776987132)) OR 
((51.3404462047513 <= latitude) AND (latitude <= 55.4902885133062) AND (-4.22505304322768 <= longitude) AND (longitude <= 1.88815551883717)) OR 
((55.4233555728457 <= latitude) AND (latitude <= 61.0903445318401) AND (-7.99560868917279 <= longitude) AND (longitude <= 0.57180768977941));

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
