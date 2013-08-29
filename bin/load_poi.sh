#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# ===========
# = Prepare =
# ===========

function createSchema() {
  $PSQL $DATABASE < ${SRCDIR}/sql/schema.sql || return 1
}

function truncate() {
  $PSQL $DATABASE -c "truncate poi" || return 1
  $PSQL $DATABASE -c "truncate poi_tag" || return 1
  $PSQL $DATABASE -c "truncate poi_sequence" || return 1
}

# ========
# = Load =
# ========

# args: poi TSV files
function loadPoiData() {
  for file in $@
  do
    ls $file || return 1
    if [ ${file: -4} == ".lzo" ]
    then
      $TIME pv "${file}" | lzop -d | $PSQL $DATABASE -c "COPY poi FROM STDIN NULL AS ''" || return 1
    elif [ ${file: -4} == ".gz" ]
    then
      $TIME pv "${file}" | gunzip | $PSQL $DATABASE -c "COPY poi FROM STDIN NULL AS ''" || return 1
    else
      $TIME $PSQL $DATABASE -c "\\copy poi FROM '${file}' NULL AS ''" || return 1
    fi
  done
}

# args: poi_tag TSV files
function loadPoiTagData() {
  for file in $@
  do
    ls $file || return 1
    if [ ${file: -4} == ".lzo" ]
    then
      $TIME pv "${file}" | lzop -d | $PSQL $DATABASE -c "COPY poi_tag(poi_id, version, key, value) FROM STDIN NULL AS ''" || return 1
    elif [ ${file: -4} == ".gz" ]
    then
      $TIME pv "${file}" | gunzip | $PSQL $DATABASE -c "COPY poi_tag(poi_id, version, key, value) FROM STDIN NULL AS ''" || return 1
    else
      $TIME $PSQL $DATABASE -c "\\copy poi_tag(poi_id, version, key, value) FROM '${file}' NULL AS ''" || return 1
    fi
  done
}

# =====================
# = Derivative Tables =
# =====================

function loadPoiSequenceTable() {
  echo "poi_sequence: poi edit sequence without redactions"
  $TIME $PSQL $DATABASE -c "INSERT INTO poi_sequence (poi_id, version, prev_version, next_version) \
  SELECT p.id, p.version, \
  (SELECT max(version) FROM poi p2 WHERE p.id=p2.id AND p.version>p2.version) as prev_version, \
  (SELECT min(version) FROM poi p3 WHERE p.id=p3.id AND p.version<p3.version) as next_version \
  FROM poi p;" || return 1
}

# ========
# = Main =
# ========

DATABASE=osm_test
datadir=
do_truncate=
create_schema=

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <data_dir> [--truncate] [--database <db_name>] [--schema]"
  echo "data_dir needs to have two subdirectories: \"poi\", and \"poi_tag\"."
  exit 1
fi

while test $# != 0
do
  case "$1" in
    --schema) echo "Will recreate database schema before loading."; create_schema=t ;;
    --truncate) echo "Will truncate tables before loading."; do_truncate=t ;;
    --database) 
      shift
      echo "Loading into database: ${1}"
      # Note: this is a global variable, initially set in env.sh
      DATABASE=$1
      ;;
    *) 
      echo "Loading data from: ${1}"
      datadir=$1 
      if [ ! -d $datadir ]
      then
        echo "Error: directory $datadir does not exist!"
        exit 1
      fi
      ;;
  esac
  shift
done

echo

if [ $create_schema ]
then
  echo "Creating DB schema..."
  createSchema || exit 1
  echo
fi

if [ $do_truncate ]
then
  echo "Truncating tables..."
  truncate || exit 1
  echo
fi

echo "Loading POI data..."
loadPoiData "${datadir}/poi/"* || exit 1
echo

echo "Loading POI tag data..."
loadPoiTagData "${datadir}/poi_tag/"* || exit 1
echo

echo "Preparing derivative tables..."
loadPoiSequenceTable || exit 1
echo

