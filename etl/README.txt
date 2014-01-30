2013-07-13 10:03:09

 =================
 = Prerequisites =
 =================

Prerequisites for ETL tools:
- Postgres 9+ with PostGIS
- Ruby with libxml-ruby gem (and optionally: bzip2-ruby)
- osmconvert
- ...?

Optionally:
- access to a Hadoop cluster with Pig and LZO compression set up
- lzop

 ===========
 = Install =
 ===========

Create a Postgres DB with src/sql/schema.sql
(Your Postgres user needs CREATE permissions on the respective DB.)

Fetch/extract history data:
$ cp bin/env.sh-example bin/env.sh
$ ./bin/fetch_osh.sh
$ ./bin/extract_osh.sh <.osh.pbf files>

Recommended but optional:
- compress with lzop
  $ lzop --delete -v data/etl/*.txt
- index with com.hadoop.compression.lzo.LzoIndexer
  $ hadoop jar .../hadoop-lzo.jar com.hadoop.compression.lzo.LzoIndexer data/etl/
- clean/filter raw node data to extract POI data
  - upload to a Hadoop cluster
  $ pig <...> src/mapred/clean_poi.pig

To load:
$ ./bin/load_tsv.sh <tsv files>

The SQL scripts in src/sql/* provide some further aggregations etc.

Some key derivative data sets may be too expensive to compute in DB. 
You can compute these in Hadoop instead, then load into your DB manually.
- poi_sequence: src/mapred/deriv_poi_sequence.pig
- tag_edit_action: src/mapred/deriv_poi_tag_edit_action.pig
- changeset: src/mapred/deriv_changeset.pig
