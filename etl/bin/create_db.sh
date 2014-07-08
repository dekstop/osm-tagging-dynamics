#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# Overriding the default command here: stay with default user, don't set a host.
export PSQL=psql

# ===========
# = Queries =
# ===========

function setPermissions() {
  db=$1
  dbuser=$2
  $PSQL $db -c "GRANT CREATE ON DATABASE $db TO $dbuser" || return 1
}

function loadPostGIS() {
  db=$1
  $PSQL --set ON_ERROR_STOP=1 $db < /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql || return 1
  $PSQL --set ON_ERROR_STOP=1 $db < /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql || return 1
  $PSQL $db -c "GRANT ALL ON geometry_columns TO PUBLIC" || return 1
  $PSQL $db -c "GRANT ALL ON spatial_ref_sys TO PUBLIC" || return 1
  $PSQL $db -c "GRANT ALL ON geography_columns TO PUBLIC" || return 1
}

function loadExtensions() {
  db=$1
  $PSQL $db -c "CREATE EXTENSION hstore" || return 1
  $PSQL $db -c "CREATE EXTENSION btree_gist" || return 1
}

function loadFunctions() {
  db=$1
  $PSQL --set ON_ERROR_STOP=1 $db < ${SRCDIR}/sql/functions.sql || return 1
}

# ========
# = Main =
# ========

db=
dbuser=${PSQL_USER}

if [[ $# -ne 1 ]]
then
  echo "Usage : $0 <db_name> [--user <name>]"
  echo "Sets up a new Postgres DB with PostGIS, select extensions, and some pre-defined functions."
  echo "Needs to be run from a DB administrator account."
  exit 1
fi

while test $# != 0
do
  case "$1" in
    --user) 
      shift
      echo "Username: ${1}"
      dbuser=$1
      ;;
    *) 
      echo "DB name: ${1}"
      db=$1 
      ;;
  esac
  shift
done

if [[ -z "$db" ]]
then
  echo "Need to specify a database name!"
  exit 1
fi
echo

echo "Creating the database..."
createdb $db || exit 1
setPermissions $db $dbuser || exit 1

echo "Setting up PostGIS..."
loadPostGIS $db || exit 1

echo "Setting up extensions..."
loadExtensions $db || exit 1

echo "Setting up functions..."
loadFunctions $db || exit 1

echo
