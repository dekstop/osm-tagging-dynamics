-- Compute poi_tag_edit_action data for POI tags.

-- Parameters:
-- $input_poi_tag
-- $input_poi_sequence
-- $output

-- Output columns: {id, version, key, value, action}

SET default_parallel 10;
SET output.compression.enabled true; 
SET output.compression.codec com.hadoop.compression.lzo.LzopCodec;

poi_tag = LOAD '$input_poi_tag' AS (id:long, version:int, key:chararray, value:chararray);
poi_sequence = LOAD '$input_poi_sequence' AS (id:long, version:int, prev_version:int, next_version:int);

-- POI versions that introduced new tags (a new tag key in the set of annotations for this poi)
pt_add_t1 = JOIN poi_tag BY (id, version), poi_sequence BY (id, version);
pt_add_t2 = FOREACH pt_add_t1 GENERATE 
  poi_tag::id as id, 
  poi_tag::version as version, 
  poi_sequence::prev_version as prev_version, 
  poi_tag::key as key,
  poi_tag::value as value;
pt_add_t3 = JOIN
  pt_add_t2 BY (id, prev_version, key) LEFT OUTER, 
  poi_tag BY (id, version, key);
pt_add_t4 = FILTER pt_add_t3 BY poi_tag::id IS NULL;
pt_add = FOREACH pt_add_t4 GENERATE 
  pt_add_t2::id as id, 
  pt_add_t2::version as version, 
  pt_add_t2::key as key, 
  pt_add_t2::value as value,
  'add' as action:chararray;

-- POI versions that removed particular tags (an existing key in the set of poi annotations)
pt_rem_t1 = JOIN poi_tag BY (id, version), poi_sequence BY (id, version);
pt_rem_t2 = FOREACH pt_rem_t1 GENERATE 
  poi_tag::id as id, 
  poi_tag::version as version, 
  poi_sequence::next_version as next_version, 
  poi_tag::key as key,
  poi_tag::value as value;
pt_rem_t3 = JOIN
  pt_rem_t2 BY (id, next_version, key) LEFT OUTER, 
  poi_tag BY (id, version, key);
pt_rem_t4 = FILTER pt_rem_t3 BY pt_rem_t2::next_version IS NOT NULL AND poi_tag::key IS NULL;
pt_rem = FOREACH pt_rem_t4 GENERATE 
  pt_rem_t2::id as id, 
  pt_rem_t2::next_version as version, 
  pt_rem_t2::key as key, 
  pt_rem_t2::value as value,
  'remove' as action:chararray;

-- POI versions that updated existing tags (same key, new value)
pt_up_t1 = JOIN poi_tag BY (id, version), poi_sequence BY (id, version);
pt_up_t2 = FOREACH pt_up_t1 GENERATE 
  poi_tag::id as id, 
  poi_tag::version as version, 
  poi_sequence::next_version as next_version, 
  poi_tag::key as key,
  poi_tag::value as value;
pt_up_t3 = JOIN
  pt_up_t2 BY (id, next_version, key) LEFT OUTER, 
  poi_tag BY (id, version, key);
pt_up_t4 = FILTER pt_up_t3 BY pt_up_t2::value != poi_tag::value;
pt_up = FOREACH pt_up_t4 GENERATE 
  poi_tag::id as id, 
  poi_tag::version as version, 
  poi_tag::key as key, 
  poi_tag::value as value,
  'update' as action:chararray;

-- Full tag editing sequence: add/remove/update
poi_tag_edit_action = UNION pt_add, pt_up, pt_rem;

-- output
-- dump poi_sequence;
STORE poi_tag_edit_action INTO '$output';
