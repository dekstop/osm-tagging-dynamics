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
  # $PSQL $DATABASE -c "truncate poi_sequence" || return 1
  # $PSQL $DATABASE -c "truncate poi_tag_edit_action" || return 1
  # $PSQL $DATABASE -c "truncate changeset" || return 1
}

# ===========
# = Indices =
# ===========

function dropIndex() {
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_key_value" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_poi_id_version" || return 1
  # $PSQL $DATABASE -c "DROP INDEX IF EXISTS poi_sequence_poi_id_version" || return 1
  # $PSQL $DATABASE -c "DROP INDEX IF EXISTS poi_tag_edit_action_poi_id_version_key" || return 1
}

function createIndex() {
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_poi_id_version ON poi_tag(poi_id, version)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value)" || return 1
  # $TIME $PSQL $DATABASE -c "CREATE UNIQUE INDEX poi_sequence_poi_id_version ON poi_sequence(poi_id, version)" || return 1
  # $TIME $PSQL $DATABASE -c "CREATE UNIQUE INDEX poi_tag_edit_action_poi_id_version_key ON poi_tag_edit_action(poi_id, version, key)" || return 1
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
    if [ ${file: -5} == ".skip" ] || [ ${file: -6} == ".index" ] || [ $file == "_SUCCESS" ]
    then
      echo "Skipping: ${file}"
    else
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
    fi
  done
  $PSQL $DATABASE -c "VACUUM ANALYZE $tablename" || return 1
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

# ======================
# = Materialised views =
# ======================

function materialisePoiSequenceTableView() {
  echo "poi_sequence: poi edit sequence without redactions"
  $TIME $PSQL $DATABASE -c "INSERT INTO poi_sequence SELECT * FROM view_poi_sequence" || return 1
}

function materialisePoiTagEditActionView() {
  echo "poi_tag_edit_action: tag versions that introduce changes"
  $TIME $PSQL $DATABASE -c "INSERT INTO poi_tag_edit_action SELECT * FROM view_poi_tag_edit_action" || return 1
}

# ========
# = Main =
# ========

datadir=
do_truncate=
create_schema=
drop_index=
as_raw_node_data=
materialise_views=
tablenames=

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <data_dir> [--database <db_name>] [--schema] [--truncate] [--drop-index] [--as-raw-node-data] [--views]"
  echo "data_dir needs to have two subdirectories: \"poi\", and \"poi_tag\"."
  echo "The following optional subdirs will also be loaded: \"poi_sequence\", \"poi_tag_edit_action\", \"changeset\""
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
    --views) echo "Will materialise select views."; materialise_views=t ;;
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

# # Special case: has subdirs
# loadTableData poi_sequence ${datadir}/poi_sequence/poi_sequence/* || exit 1
# 
# for tablename in poi_tag_edit_action changeset $tablenames
# do
#   if [ -e ${datadir}/${tablename} ]
#   then
#     echo "Loading table data: ${tablename}"
#     loadTableData $tablename ${datadir}/${tablename}/* || exit 1
#     echo
#   fi
# done

if [ $materialise_views ]
then
  echo "Materialised views..."
  materialisePoiSequenceTableView || exit 1
  materialisePoiTagEditActionView || exit 1
  echo
fi

if [ $drop_index ]
then
  echo "Creating indices..."
  createIndex || exit 1
  echo
fi

echo "Next Steps:"
echo "- populate the region table"
echo "- populate the changesets table"
