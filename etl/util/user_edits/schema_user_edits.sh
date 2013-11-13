#!/bin/sh

BIN=$( cd "$( dirname "$0" )" && cd ../../bin && pwd )
. ${BIN}/env.sh

# ========
# = Main =
# ========

DATE=`date +%Y%m%d`

while test $# != 0
do
  case "$1" in
    --database) 
      shift
      echo "Loading into database: ${1}"
      # Note: this is a global variable, initially set in env.sh
      DATABASE=$1
      ;;
    *) 
      echo "Unknown parameter: ${1}"
      exit 1
      ;;
  esac
  shift
done

echo

echo "Creating user_edits schema: creators, editors, and their edit actions."
$TIME $PSQL $DATABASE -c "CREATE SCHEMA user_edits;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_all_edits AS SELECT p.uid, p.id as poi_id, p.version FROM poi p JOIN poi_tag_edit_action a ON (p.id=a.poi_id AND p.version=a.version) GROUP BY p.uid, p.id, p.version;" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_all_edits;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_edits_creators AS SELECT uid, poi_id, 1 as version FROM user_edits.poi_all_edits e WHERE version=1 GROUP BY uid, poi_id;" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_edits_creators;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_edits_editors AS SELECT uid, poi_id, version FROM user_edits.poi_all_edits e WHERE version>1 GROUP BY uid, poi_id, version;" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_edits_editors;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_edits_only_creators AS SELECT c.uid, c.poi_id, 1 as version FROM user_edits.poi_edits_creators c LEFT OUTER JOIN (SELECT distinct uid FROM user_edits.poi_edits_editors) e ON (c.uid=e.uid) WHERE e.uid IS NULL GROUP BY c.uid, c.poi_id;" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_edits_only_creators;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_edits_creators_and_editors AS SELECT a.uid, a.poi_id, a.version FROM user_edits.poi_all_edits a JOIN (SELECT c.uid FROM (SELECT DISTINCT uid FROM user_edits.poi_edits_creators) c JOIN (SELECT DISTINCT uid FROM user_edits.poi_edits_editors) e ON c.uid=e.uid) t ON (a.uid=t.uid);" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_edits_creators_and_editors;" || exit 1
$TIME $PSQL $DATABASE -c "CREATE TABLE user_edits.poi_edits_only_editors AS SELECT e.uid, e.poi_id, e.version FROM user_edits.poi_edits_editors e LEFT OUTER JOIN (SELECT distinct uid FROM user_edits.poi_edits_creators) c ON (c.uid=e.uid) WHERE c.uid IS NULL GROUP BY e.uid, e.poi_id, e.version;" || exit 1
$TIME $PSQL $DATABASE -c "VACUUM ANALYZE user_edits.poi_edits_only_editors;" || exit 1
