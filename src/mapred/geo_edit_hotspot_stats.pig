-- basic global stats: number of POI, avg num_versions/num_users per POI, etc
-- stratified to 0.5 lat/lon granularity

-- inputs
-- s3://osm-research/tsv-compressed/continents/node
-- data/tsv/test/node
-- data/etl/antarctica-node.txt.gz
-- data/tsv-compressed/node/antarctica
node = LOAD 'data/tsv/test/node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

-- s3://osm-research/tsv-compressed/continents/node_tag
-- data/tsv/test/node_tag
-- data/etl/antarctica-node_tag.txt.gz
-- data/tsv-compressed/node_tag/antarctica
node_tag = LOAD 'data/tsv/test/node_tag' AS (id:long, version:int, key:chararray, value:chararray);

-- stratify
node_geo = FILTER node BY (latitude IS NOT NULL AND longitude IS NOT NULL);
node_stratified = FOREACH node_geo GENERATE id, version, changeset, timestamp, uid, username, ROUND(latitude * 2) / 2.0 AS latitude, ROUND(longitude * 2) / 2.0 AS longitude; 

-- poi/tag join
poi_versions_tags_t = COGROUP node_stratified BY (id, version) INNER, node_tag BY (id, version) INNER;
poi_versions_tags = FOREACH poi_versions_tags_t GENERATE flatten($1.id) as id, flatten($1.version) as version, flatten($1.username) as username, flatten(node_stratified.latitude) as lat, flatten(node_stratified.longitude) as lon, node_tag;

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
-- s3://osm-research/stats/geo_poi_edit_stats-01
-- stats/geo_poi_edit_stats-01
store geo_stats into 'geo_poi_edit_stats-01';
