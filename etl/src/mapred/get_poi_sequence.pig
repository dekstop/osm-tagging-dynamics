-- Compute poi_sequence data (skip lists) of cleaned POI data.

-- Output columns:
-- ../poi_id_version/: {id, version}
-- ../poi_sequence/: {id, version, prev_version, next_version}

-- Parameters:
-- $input_node
-- $output

SET default_parallel 10;
-- SET output.compression.enabled true; 
-- SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

node = LOAD '$input_node' AS (id:long, version:int, changeset:long, timestamp:chararray, uid:long, username:chararray, latitude:double, longitude:double);

-- extract all versions
poi_id_version_t = FOREACH node GENERATE id, version;
poi_id_version = DISTINCT poi_id_version_t;
-- poi_id_version: {id: long,version: int}

-- Hack. See https://issues.apache.org/jira/browse/PIG-3020
-- Avoids "ERROR 2225: Projection with nothing to reference!"
STORE poi_id_version INTO '$output/poi_id_version';
pv1 = LOAD '$output/poi_id_version' AS (id:long, version:int);
pv2 = LOAD '$output/poi_id_version' AS (id:long, version:int);

-- get upper/lower neighbours
pv_pairs = JOIN pv1 BY id FULL OUTER, pv2 BY id;
pv_pairs_below = FILTER pv_pairs BY pv2::version < pv1::version;
pv_pairs_above = FILTER pv_pairs BY pv2::version > pv1::version;

pv_solo_t1 = FILTER (GROUP pv1 BY id) BY SIZE($1)==1;
pv_solo = FOREACH pv_solo_t1 GENERATE FLATTEN($1), NULL as prev_version:int, NULL as next_version:int;
-- pv_solo: {pv1::id: long,pv1::version: int,prev_version: int,next_version: int}

pv_below_t1 = GROUP pv_pairs_below BY (pv1::id, pv1::version);
pv_below_t2 = FOREACH pv_below_t1 GENERATE group.$0 as id, group.$1 as version, $1.pv2::version;
pv_below = FOREACH pv_below_t2 GENERATE id, version, MAX($2) as prev_version;
-- pv_below: {id: long,version: int,prev_version: int}

pv_above_t1 = GROUP pv_pairs_above BY (pv1::id, pv1::version);
pv_above_t2 = FOREACH pv_above_t1 GENERATE group.$0 as id, group.$1 as version, $1.pv2::version;
pv_above = FOREACH pv_above_t2 GENERATE id, version, MIN($2) as next_version;
-- pv_above: {id: long,version: int,next_version: int}

-- make sequence
poi_sequence_t1 = JOIN pv_below BY (id, version) FULL OUTER, pv_above BY (id, version);
-- poi_sequence_t: {pv_below::id: long,pv_below::version: int,pv_below::prev_version: int,pv_above::id: long,pv_above::version: int,pv_above::next_version: int}
poi_sequence_t2 = FOREACH poi_sequence_t1 {
  GENERATE 
    ($0 IS NULL ? $3 : $0) as id, 
    ($1 IS NULL ? $4 : $1) as version, 
    $2 as prev_version, 
    $5 as next_version;
};
poi_sequence = UNION poi_sequence_t2, pv_solo;

-- output
-- dump poi_sequence;
STORE poi_sequence INTO '$output/poi_sequence';
