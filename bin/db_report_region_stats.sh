#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# ================
# = Region Stats =
# ================

function getRegionStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
    SELECT region, num_poi, num_editors, num_tags, 
    num_tags::float / num_poi as tags_per_poi,
    num_editors::float / num_poi as editors_per_poi,
    num_editors::float / num_tags as editors_per_tag,
    num_poi_versions::float / num_poi as versions_per_poi,
    num_tag_versions::float / num_tags as versions_per_tag
    FROM (SELECT r.name as region, count(distinct p.id) as num_poi, 
      count(distinct p.username) as num_editors,
      count(distinct (t.poi_id::text || '-' || t.key)) as num_tags,
      count(distinct (p.id::text || '-' || p.version::text)) as num_poi_versions,
      count(distinct (t.poi_id::text || '-' || t.key || '-' || t.version)) as num_tag_versions
      FROM poi p 
      JOIN view_poi_tag_edit_actions t ON (p.id=t.poi_id AND p.version=t.version)
      JOIN view_region_poi_latest rp ON p.id=rp.poi_id
      JOIN region r ON rp.region_id=r.id
      GROUP BY r.name) t
    WHERE num_poi>100 AND num_tags>100
    ORDER BY num_poi DESC
  " || return 1
}

function getRegionEditIntervalStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
    SELECT region, num_poi, num_editors, num_tags, 
    extract('day' FROM avg_delta_t) as avg_num_days
    FROM (SELECT r.name as region, count(distinct p2.id) as num_poi, 
      count(distinct p2.username) as num_editors,
      count(distinct (t.poi_id::text || '-' || t.key)) as num_tags,
      avg(p2.timestamp-p1.timestamp) as avg_delta_t
      FROM poi p2
      JOIN poi_sequence ps ON (p2.id=ps.poi_id AND p2.version=ps.version)
      JOIN poi p1 ON (ps.poi_id=p1.id AND ps.prev_version=p1.version)
      JOIN view_poi_tag_edit_actions t ON (p2.id=t.poi_id AND p2.version=t.version)
      JOIN view_region_poi_latest rp ON p2.id=rp.poi_id
      JOIN region r ON rp.region_id=r.id
      GROUP BY r.name) t
    WHERE num_poi>100 AND num_tags>100
    ORDER BY num_poi DESC
  " || return 1
}

# =============
# = POI Stats =
# =============

function getPoiNumEditorsStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT num_editors, count(*) 
  FROM (
    SELECT count(distinct p.username) as num_editors
    FROM poi p 
    JOIN view_poi_tag_edit_actions t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  GROUP BY num_editors
  ORDER BY num_editors ASC" || return 1
}

function getPoiNumTagsStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT num_tags, count(*) 
  FROM (
    SELECT count(distinct t.key) as num_tags
    FROM poi p 
    JOIN view_poi_tag_edit_actions t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  GROUP BY num_tags
  ORDER BY num_tags ASC" || return 1
}

function getPoiNumEditorsPerTagStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT num_editors_per_tag, count(*) 
  FROM (
    SELECT count(distinct p.username) as num_editors_per_tag
    FROM poi p 
    JOIN view_poi_tag_edit_actions t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id, t.key) t
  GROUP BY num_editors_per_tag
  ORDER BY num_editors_per_tag ASC" || return 1
}

function getPoiNumVersionsStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT num_versions, count(*) 
  FROM (
    SELECT count(distinct p.version) as num_versions
    FROM poi p 
    JOIN view_poi_tag_edit_actions t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  GROUP BY num_versions
  ORDER BY num_versions ASC" || return 1
}

function getPoiEditIntervalStats() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT num_days, count(*) 
  FROM (
    SELECT extract('day' FROM avg(p2.timestamp-p1.timestamp)) as num_days
    FROM poi p2
    JOIN poi_sequence ps ON (p2.id=ps.poi_id AND p2.version=ps.version)
    JOIN poi p1 ON (ps.poi_id=p1.id AND ps.prev_version=p1.version)
    JOIN view_poi_tag_edit_actions t ON (p2.id=t.poi_id AND p2.version=t.version)
    GROUP BY p2.id, p2.version) t
  GROUP BY num_days
  ORDER BY num_days ASC" || return 1
}

# ========
# = Main =
# ========

outdir=

if [[ $# -lt 1 ]]
then
  echo "Usage : $0 <output_dir> [--database <db_name>]"
  exit 1
fi

while test $# != 0
do
  case "$1" in
    --database) 
      shift
      echo "Querying database: ${1}"
      # Note: this is a global variable, initially set in env.sh
      DATABASE=$1
      ;;
    *) 
      echo "Writing files to: ${1}"
      outdir=$1 
      mkdir -p $outdir || exit 1
      ;;
  esac
  shift
done

echo

getRegionStats $outdir/regionStats.txt || exit 1
getRegionEditIntervalStats $outdir/regionEditIntervalStats.txt || exit 1

getPoiNumEditorsStats $outdir/poiNumEditorsStats.txt || exit 1
getPoiNumTagsStats $outdir/poiNumTagsStats.txt || exit 1
getPoiNumEditorsPerTagStats $outdir/poiNumEditorsPerTagStats.txt || exit 1
getPoiNumVersionsStats $outdir/poiNumVersionsStats.txt || exit 1
getPoiEditIntervalStats $outdir/poiEditIntervalStats.txt || exit 1
