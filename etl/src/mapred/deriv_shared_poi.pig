-- Compute shared_poi data: a list of POI with multiple editors.

-- Parameters:
-- $input_poi
-- $output

-- Output columns: 
-- ../poi_id_version_uid/: {id, version, uid}
-- ../shared_poi/: {id, creator_uid, first_shared_version}

SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi = LOAD '$input_poi' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

-- extract all versions
poi_id_version_uid = FOREACH poi GENERATE id, version, uid;
poi_id_version_uid = DISTINCT poi_id_version_uid;
-- poi_id_version_uid: {id: long,version: int,uid:long}

-- Hack. See https://issues.apache.org/jira/browse/PIG-3020
-- Avoids "ERROR 2225: Projection with nothing to reference!"
STORE poi_id_version_uid INTO '$output/poi_id_version_uid';
pv1 = LOAD '$output/poi_id_version_uid' AS (id:long, version:int, uid:long);
pv2 = LOAD '$output/poi_id_version_uid' AS (id:long, version:int, uid:long);

-- extract first and subsequent edits
pv1 = FILTER pv1 BY version==1 AND uid IS NOT NULL;
pv2 = FILTER pv2 BY version>=2 AND uid IS NOT NULL;

-- join
pv_join = JOIN pv1 BY (id), pv2 BY (id);
-- {pv1::id: long,pv1::version: int,pv1::uid: long,pv2::id: long,pv2::version: int,pv2::uid: long}
pv_join = FILTER pv_join BY (pv1::uid!=pv2::uid);
pv_group = GROUP pv_join BY pv1::id;
-- {group: long,pv_join: {(pv1::id: long,pv1::version: int,pv1::uid: long,pv2::id: long,pv2::version: int,pv2::uid: long)}}
shared_poi = FOREACH pv_group {
  versions = DISTINCT $1.pv2::version;
  GENERATE 
    $0 as id, 
    MIN($1.pv1::uid) as creator_uid, 
    MIN(versions) AS first_shared_version;
};

-- output
-- dump shared_poi;
STORE shared_poi INTO '$output/shared_poi';
