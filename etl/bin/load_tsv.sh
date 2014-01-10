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
  for tablename in $@
  do
    $PSQL $DATABASE -c "TRUNCATE ${tablename}" || return 1
  done
}

# ===========
# = Indices =
# ===========

function dropIndex() {
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_id_version" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_key_value" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_poi_id_version" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_poi_tag_edit_action_poi_id_version_key" || return 1
  $PSQL $DATABASE -c "DROP INDEX IF EXISTS idx_shared_poi_poi_id"
}

function createIndex() {
  $TIME $PSQL $DATABASE -c "CREATE UNIQUE INDEX idx_poi_id_version ON poi(id, version)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_poi_id_version ON poi_tag(poi_id, version)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE INDEX idx_poi_tag_key_value ON poi_tag(key, value)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE UNIQUE INDEX idx_poi_tag_edit_action_poi_id_version_key ON poi_tag_edit_action(poi_id, version, key)" || return 1
  $TIME $PSQL $DATABASE -c "CREATE UNIQUE INDEX idx_shared_poi_poi_id ON shared_poi(poi_id)" || return 1
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

# ========
# = Main =
# ========

datadir=
do_truncate=
create_schema=
drop_index=
tablenames="poi poi_tag poi_tag_edit_action shared_poi"

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <data_dir> [--database <db_name>] [--schema] [--truncate] [--drop-index]"
  echo "data_dir should have the subdirectories: ${tablenames}"
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

if [ $drop_index ]
then
  echo "Dropping indices..."
  dropIndex || exit 1
  echo
fi

for tablename in $tablenames
do
  if [ -e ${datadir}/${tablename} ]
  then
    if [ $do_truncate ]
    then
      echo "Truncating: ${tablename}"
      truncate $tablename || exit 1
    fi
    echo "Loading table data: ${tablename}"
    loadTableData $tablename ${datadir}/${tablename}/* || exit 1
    echo
  fi
done

if [ $drop_index ]
then
  echo "Creating indices..."
  createIndex || exit 1
  echo
fi

