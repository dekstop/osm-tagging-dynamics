#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# ===========
# = Prepare =
# ===========

function createSchema() {
  $PSQL --set ON_ERROR_STOP=1 $DATABASE < ${SRCDIR}/sql/schema.sql || return 1
}

function truncate() {
  $PSQL $DATABASE -c "truncate poi" || return 1
  $PSQL $DATABASE -c "truncate poi_tag" || return 1
  $PSQL $DATABASE -c "truncate poi_sequence" || return 1
}

# ===========
# = Indices =
# ===========

function dropIndex() {
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_key_value" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_poi_id_version" || return 1
}

function createIndex() {
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_poi_id_version ON poi_tag(poi_id, version)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value)" || return 1
}

# ========
# = Load =
# ========

# args: table name, list of poi TSV files
function loadTableData() {
  tablename=$1
  shift
  for file in $@
  do
    ls $file || return 1
    if [ ${file: -4} == ".lzo" ]
    then
      $TIME pv "${file}" | lzop -d | $PSQL $DATABASE -c "COPY $tablename FROM STDIN NULL AS ''" || return 1
    elif [ ${file: -4} == ".gz" ]
    then
      $TIME pv "${file}" | gunzip | $PSQL $DATABASE -c "COPY $tablename FROM STDIN NULL AS ''" || return 1
    else
      $TIME $PSQL $DATABASE -c "\\copy $tablename FROM '${file}' NULL AS ''" || return 1
    fi
  done
}

# args: poi TSV files
function loadPoiData() {
  loadTableData poi $@ || return 1
}

# args: poi_tag TSV files
function loadPoiTagData() {
  loadTableData poi_tag $@ || return 1
}

# ======================
# = Load raw node data =
# ======================

function truncateNode() {
  $PSQL $DATABASE -c "truncate node" || return 1
}

# args: node TSV files
function loadNodeData() {
  loadTableData node $@ || return 1
}

function migrateNodeDataToPoiTables() {
  echo "poi_tag: delete created_by tags"
  $TIME $PSQL $DATABASE -c "delete from poi_tag where key='created_by'" || return 1
  echo "poi: all nodes with tags"
  $TIME $PSQL $DATABASE -c "INSERT INTO poi SELECT DISTINCT * FROM node WHERE node.id IN (SELECT DISTINCT poi_id FROM poi_tag) AND latitude IS NOT NULL AND longitude IS NOT NULL" || return 1
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
drop_index=
as_raw_node_data=

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <data_dir> [--database <db_name>] [--schema] [--truncate] [--drop-index] [--as-raw-node-data]"
  echo "data_dir needs to have two subdirectories: \"poi\", and \"poi_tag\"."
  exit 1
fi

while test $# != 0
do
  case "$1" in
    --database) 
      shift
      echo "Loading into database: ${1}"
      # Note: this is a global variable, initially set in env.sh
      DATABASE=$1
      ;;
    --schema) echo "Will recreate database schema before loading."; create_schema=t ;;
    --truncate) echo "Will truncate tables before loading."; do_truncate=t ;;
    --drop-index) echo "Will drop indices before loading."; drop_index=t ;;
    --as-raw-node-data) echo "Will load as raw node data, this involves some basic data cleaning operations."; as_raw_node_data=t ;;
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

if [ $drop_index ]
then
  echo "Dropping indices..."
  dropIndex || exit 1
  echo
fi

if [ $as_raw_node_data ]
then
  echo "Loading node data..."
  truncateNode || exit 1
  loadNodeData "${datadir}/node/"* || exit 1
  echo

  echo "Loading POI tag data..."
  loadPoiTagData "${datadir}/node_tag/"* || exit 1
  echo

  echo "Cleaning node data and migrating to POI table."
  migrateNodeDataToPoiTables || exit 1
  echo
else
  echo "Loading POI data..."
  loadPoiData "${datadir}/poi/"* || exit 1
  echo

  echo "Loading POI tag data..."
  loadPoiTagData "${datadir}/poi_tag/"* || exit 1
  echo
fi

echo "Preparing derivative tables..."
loadPoiSequenceTable || exit 1
echo

if [ $drop_index ]
then
  echo "Creating indices..."
  createIndex || exit 1
  echo
fi
