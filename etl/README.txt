2013-07-13 10:03:09

 =================
 = Prerequisites =
 =================

Prerequisites for ETL tools:
- Postgres 8+
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

Optionally:
- compress with lzop
- index with com.hadoop.compression.lzo.LzoIndexer
- clean raw node data with src/mapred/clean_poi.pig to extract POI data

To load:
$ ./bin/load_tsv.sh <tsv files>
