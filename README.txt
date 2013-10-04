2013-07-13 10:03:09

 ===========
 = Install =
 ===========

Prerequisites for ETL tools:
- Postgres
- Ruby with libxml-ruby gem (and optionally: bzip2-ruby)
- osmconvert
- ...?

Create a Postgres DB with src/sql/schema.sql
Fetch .osh.pbf OSM history files, see data/_data.txt
$ cp bin/env.sh-example bin/env.sh
$ ./bin/extract_osh.sh <osh file>
$ ./bin/load_tsv.sh <tsv files>

Further modules may have additional requirements.
