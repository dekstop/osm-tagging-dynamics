#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# ===========
# = Queries =
# ===========

function createSchema() {
  echo "Creating schema: ${schema}"
  $TIME $PSQL $DATABASE -c "CREATE SCHEMA ${schema}" || return 1
}

function selectSample() {
  echo "Selecting a POI sample of: ${sample}"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.poi_sample AS SELECT id AS poi_id FROM (SELECT distinct id FROM poi) t WHERE random() <= ${sample}" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.poi_sample" || return 1
}

function loadTables() {
  echo "Table: ${schema}.poi"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.poi AS SELECT p.* FROM poi p JOIN ${schema}.poi_sample ps ON p.id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.poi" || return 1
  echo
  
  echo "Table: ${schema}.poi_tag"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.poi_tag AS SELECT p.* FROM poi_tag p JOIN ${schema}.poi_sample ps ON p.poi_id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.poi_tag" || return 1
  echo
  
  echo "Table: ${schema}.poi_sequence"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.poi_sequence AS SELECT p.* FROM poi_sequence p JOIN ${schema}.poi_sample ps ON p.poi_id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.poi_sequence" || return 1
  echo

  echo "Table: ${schema}.poi_tag_edit_action"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.poi_tag_edit_action AS SELECT p.* FROM poi_tag_edit_action p JOIN ${schema}.poi_sample ps ON p.poi_id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.poi_tag_edit_action" || return 1
  echo

  echo "Table: ${schema}.changeset"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.changeset AS SELECT c.* FROM changeset c JOIN (SELECT distinct changeset FROM ${schema}.poi) t ON c.id=t.changeset" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.changeset" || return 1
  echo
  
  echo "Table: ${schema}.region"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.region AS SELECT * FROM region" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.region" || return 1
  
  echo "Table: ${schema}.region_poi_latest"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.region_poi_latest AS SELECT p.* FROM view_region_poi_latest p JOIN ${schema}.poi_sample ps ON p.poi_id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.region_poi_latest" || return 1
  echo

  echo "Table: ${schema}.region_poi_any"
  $TIME $PSQL $DATABASE -c "CREATE TABLE ${schema}.region_poi_any AS SELECT p.* FROM view_region_poi_any p JOIN ${schema}.poi_sample ps ON p.poi_id=ps.poi_id" || return 1
  $TIME $PSQL $DATABASE -c "VACUUM ANALYZE ${schema}.region_poi_any" || return 1
}

# ========
# = Main =
# ========

schema=
sample=0.1
region_join_latest=view_region_poi_latest
region_join_any=view_region_poi_any

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <target_schema_name> [--sample <fraction>] [--database <db_name>] [--region-join-any <table>] [--region-join-latest <table>]"
  echo "Sample fraction must be a number in the range 0 < fraction < 1."
  echo "The default sample is 0.1 (10%)"
  echo "The default region joins are view_region_poi_any and view_region_poi_latest, it may speed things up to provide materialised views instead."
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
    --sample) 
      shift
      echo "Sample fraction: ${1}"
      sample=$1
      ;;
    --region-join-any) 
      shift
      echo "region_join_any: ${1}"
      region_join_any=$1
      ;;
    --region-join-latest) 
      shift
      echo "region_join_latest: ${1}"
      region_join_latest=$1
      ;;
    *) 
      echo "Loading into target schema: ${1}"
      schema=$1 
      ;;
  esac
  shift
done

if [[ -z "$schema" ]]
then
  echo "Need to specify a target schema!"
  exit 1
fi
echo

echo "Preparing the database..." || exit 1
createSchema || exit 1
selectSample || exit 1
echo

echo "Loading tables..."
loadTables || exit 1
echo
