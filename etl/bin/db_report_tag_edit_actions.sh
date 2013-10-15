#!/bin/sh

BIN=$( cd "$( dirname "$0" )" && pwd )
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

$TIME $PSQL $DATABASE -e -c "CREATE TABLE IF NOT EXISTS temp_edit_actions_${DATE} AS SELECT * FROM view_poi_tag_edit_actions" || exit 1

$TIME $PSQL $DATABASE -e -c "CREATE TABLE temp_edit_actions_3month_${DATE} AS
  SELECT s1.poi_id, s1.key, s2.action, (p2.timestamp-p1.timestamp) as timedelta,
    s1.version as version1, p1.timestamp as timestamp1, p1.username as username1, s1.value as value1, 
    s2.version as version2, p2.username as username2, p2.timestamp as timestamp2, s2.value as value2 
  FROM temp_edit_actions_${DATE} s1 JOIN temp_edit_actions_${DATE} s2
  ON (s1.poi_id=s2.poi_id 
    AND s1.version=(
      SELECT max(version) FROM poi 
      WHERE poi.id=s1.poi_id AND poi.version<s2.version)
    AND s1.key=s2.key)
  JOIN poi p1 ON (p1.id=s1.poi_id AND p1.version=s1.version)
  JOIN poi p2 ON (p2.id=s2.poi_id AND p2.version=s2.version)
  WHERE s2.action IN ('update', 'remove')
  AND s1.key=s2.key
  AND s1.value!=s2.value
  AND p1.username!=p2.username
  AND (p2.timestamp-p1.timestamp) < interval '3 month'
  order by s1.poi_id, s1.key, s1.version" || exit 1

$TIME $PSQL $DATABASE -e -c "CREATE TABLE temp_edit_actions_3month_summary_${DATE} AS
  select poi_id, substr(key, 0, 20) as key, timestamp2, timedelta, action, 
    version1 as ver1, substr(username1, 0, 20) as username1, substr(value1, 0, 30) as value1, 
    version2 as ver2, substr(username2, 0, 20) as username2, substr(value2, 0, 30) as value2
    from temp_edit_actions_3month_${DATE}
    where key!='created_by'
    order by poi_id, key, timestamp2" || exit 1
