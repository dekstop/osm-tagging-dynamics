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

 =========
 = Fetch =
 =========

Configure local paths etc:
$ cp bin/env.sh-example bin/env.sh
Edit bin/env.sh

To update the hard-coded OSM history source dir (lame, I know):
Edit bin/fetch_osh.sh

Fetch/extract history data:
$ ./bin/fetch_osh.sh
$ ./bin/extract_osh.sh [*.osh.pbf files]

Recommended but optional:
- compress with lzop
  $ lzop --delete -v data/etl/*.txt
- index with com.hadoop.compression.lzo.LzoIndexer
  $ hadoop jar .../hadoop-lzo.jar com.hadoop.compression.lzo.LzoIndexer data/etl/

Then upload all this to a Hadoop cluster.
A range of Pig scripts in src/mapred help with data cleaning etc.

Clean the node history to extract pure POI data:
$ pig <...> src/mapred/clean_poi.pig

Some (optional) derivative data sets are too expensive to compute in DB. 
You can compute these in Hadoop instead, then load into your DB manually.
-> have a look at src/mapred/deriv_*.pig

Then copy it all to a local drive to it into Postgres.

========
= Load =
========

Create a Postgres DB with src/sql/schema.sql
Your Postgres user needs CREATE permissions on the respective DB.

To load a segment:
$ ./bin/load_tsv.sh <root_dir>

SQL scripts in src/sql/* can provide some further aggregations etc.

