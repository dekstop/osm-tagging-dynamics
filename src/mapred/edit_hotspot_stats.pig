-- Basic global stats: number of POI, avg num_versions/num_users per POI, etc.
-- Stratified to 0.5 lat/lon granularity.

-- parameters:
-- $input_node
-- $input_node_tag
-- $output

SET default_parallel 4;

node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);
clean_node = FILTER node BY (latitude IS NOT NULL AND longitude IS NOT NULL);

node_tag = LOAD '$input_node_tag' AS (id:long, version:int, key:chararray, value:chararray);
clean_node_tag = FILTER node_tag BY (key!='created_by');

-- stratify
node_stratified = FOREACH clean_node GENERATE id, version, changeset, timestamp, uid, username, ROUND(latitude * 2) / 2.0 + 0.25 AS latitude, ROUND(longitude * 2) / 2.0 + 0.25 AS longitude; 

-- poi/tag join
poi_versions_tags_t = COGROUP node_stratified BY (id, version) INNER, clean_node_tag BY (id, version) INNER;
poi_versions_tags = FOREACH poi_versions_tags_t GENERATE flatten($1.id) as id, flatten($1.version) as version, flatten($1.username) as username, flatten(node_stratified.latitude) as lat, flatten(node_stratified.longitude) as lon, clean_node_tag as node_tag;

-- coint POI
poi_stats_group = GROUP poi_versions_tags BY id;
poi_stats = FOREACH poi_stats_group {
  entries = ORDER $1 BY version DESC;
  latest = LIMIT entries 1;
  lat = latest.lat;
  lon = latest.lon;
  versions = DISTINCT entries.version;
  users = DISTINCT entries.username;
  GENERATE $0 as id, flatten(lat) as lat, flatten(lon) as lon, COUNT(versions) as num_versions, COUNT(users) as num_users;
};

geo_stats_group = GROUP poi_stats BY (lat, lon);
geo_stats = FOREACH geo_stats_group {
  num_poi = COUNT($1);
  mean_versions = AVG($1.num_versions);
  max_versions = MAX($1.num_versions);
  mean_users = AVG($1.num_users);
  max_users = MAX($1.num_users);
  GENERATE flatten($0) as (lat, lon), num_poi as num_poi, mean_versions as mean_versions, max_versions as max_versions, mean_users as mean_users, max_users as max_users;
};

-- output
store geo_stats into '$output';
