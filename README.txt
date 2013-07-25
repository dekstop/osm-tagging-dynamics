2013-07-13 10:03:09

 ===========
 = Install =
 ===========

Prerequisites:
- Postgres
- Ruby with libxml-ruby gem
- osmconvert
- ...?

Create a Postgres DB with src/sql/schema.sql
Fetch .osh.pbf OSM history files, see data/_data.txt
$ cp bin/env.sh-example bin/env.sh
$ ./bin/import.sh
