2013-07-13 10:03:09

 ===========
 = Install =
 ===========

Prerequisites for ETL tools:
- Postgres 8+
- Ruby with libxml-ruby gem (and optionally: bzip2-ruby)
- osmconvert
- ...?

Further modules may have additional requirements.

Create a Postgres DB with src/sql/schema.sql
(Your Postgres user needs CREATE permissions on the respective DB.)

Fetch .osh.pbf OSM history files, see data/_data.txt

Convert/load data:
$ cp bin/env.sh-example bin/env.sh
$ ./bin/extract_osh.sh <osh file>
$ ./bin/load_tsv.sh <tsv files>
