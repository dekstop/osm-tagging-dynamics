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
      JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version)
      JOIN ${table_region_poi_latest} rp ON p.id=rp.poi_id
      JOIN region r ON rp.region_id=r.id
      GROUP BY r.name) t
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
      JOIN poi_tag_edit_action t ON (p2.id=t.poi_id AND p2.version=t.version)
      JOIN ${table_region_poi_latest} rp ON p2.id=rp.poi_id
      JOIN region r ON rp.region_id=r.id
      GROUP BY r.name) t
    ORDER BY num_poi DESC
  " || return 1
}

# ==============
# = Histograms =
# ==============

function getRegionNumEditorsHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_editors, count(*) as num_poi
  FROM (
    SELECT p.id, count(distinct p.username) as num_editors
    FROM poi p 
    JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  JOIN ${table_region_poi_latest} rp ON t.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_editors
  ORDER BY r.name, num_editors ASC" || return 1
}

function getRegionNumTagsHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_tags, count(*) as num_poi
  FROM (
    SELECT p.id, count(distinct t.key) as num_tags
    FROM poi p 
    JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  JOIN ${table_region_poi_latest} rp ON t.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_tags
  ORDER BY r.name, num_tags ASC" || return 1
}

function getRegionNumEditorsPerTagHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_editors_per_tag, count(*) as num_poi
  FROM (
    SELECT p.id, count(distinct p.username) as num_editors_per_tag
    FROM poi p 
    JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id, t.key) t
  JOIN ${table_region_poi_latest} rp ON t.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_editors_per_tag
  ORDER BY r.name, num_editors_per_tag ASC" || return 1
}

function getRegionNumVersionsHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_versions, count(*) as num_poi
  FROM (
    SELECT p.id, count(distinct p.version) as num_versions
    FROM poi p 
    JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version)
    GROUP BY p.id) t
  JOIN ${table_region_poi_latest} rp ON t.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_versions
  ORDER BY r.name, num_versions ASC" || return 1
}

function getRegionEditIntervalHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_days, count(*) as num_poi
  FROM (
    SELECT p2.id, extract('day' FROM avg(p2.timestamp-p1.timestamp)) as num_days
    FROM poi p2
    JOIN poi_sequence ps ON (p2.id=ps.poi_id AND p2.version=ps.version)
    JOIN poi p1 ON (ps.poi_id=p1.id AND ps.prev_version=p1.version)
    JOIN poi_tag_edit_action t ON (p2.id=t.poi_id AND p2.version=t.version)
    GROUP BY p2.id, p2.version) t
  JOIN ${table_region_poi_latest} rp ON t.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_days
  ORDER BY r.name, num_days ASC" || return 1
}

function getRegionTagReversionHistogram() {
  outfile=$1
  echo $outfile
  $TIME $PSQL $DATABASE --no-align --field-separator="	" --pset footer=off --output=${outfile} -c "
  SELECT r.name as region, num_steps, count(distinct t2.id) as num_poi, avg(num_users) as avg_num_users
  FROM (
    SELECT id, max(num_steps) as num_steps, max(num_users) as num_users
    FROM (
      SELECT p.id, key, value, count(*) as num_steps, count(distinct username) as num_users, min(p.version) as start_version
      FROM poi p 
      JOIN poi_tag_edit_action t ON (p.id=t.poi_id AND p.version=t.version) 
      WHERE action IN ('add', 'update') 
      GROUP BY p.id, key, value 
      HAVING count(*)>1
    ) t1
    GROUP BY id, start_version
  ) t2
  JOIN ${table_region_poi_latest} rp ON t2.id=rp.poi_id
  JOIN region r ON rp.region_id=r.id
  GROUP BY r.name, num_steps" || return 1
}

# ========
# = Main =
# ========

DATE=`date +%Y%m%d`
table_region_poi_latest=view_region_poi_latest

outdir=
materialise_views=

while test $# != 0
do
  case "$1" in
    --database) 
      shift
      echo "Querying database: ${1}"
      # Note: this is a global variable, initially set in env.sh
      DATABASE=$1
      ;;
    --materialise-views) echo "Will materialise views."; materialise_views=t ;;
    *) 
      echo "Writing files to: ${1}"
      outdir=$1 
      mkdir -p $outdir || exit 1
      ;;
  esac
  shift
done

echo

if [[ -z "$outdir" ]]
then
  echo "Usage : $0 <output_dir> [--database <db_name>]"
  exit 1
fi

if [ $materialise_views ]
then
  echo "Materialising views..."
  table_region_poi_latest=temp_region_poi_latest_${DATE}
  $TIME $PSQL $DATABASE -e -c "CREATE TABLE ${table_region_poi_latest} AS SELECT * FROM view_region_poi_latest" # || exit 1
  $TIME $PSQL $DATABASE -e -c "CREATE UNIQUE INDEX ${table_region_poi_latest}_region_id_poi_id ON ${table_region_poi_latest}(region_id, poi_id)" # || exit 1
fi

# From a previous run...
table_region_poi_latest=temp_region_poi_latest_20130910

getRegionStats $outdir/regionStats.txt || exit 1
getRegionEditIntervalStats $outdir/regionEditIntervalStats.txt || exit 1

getRegionNumEditorsHistogram $outdir/regionNumEditorsHistogram.txt || exit 1
getRegionNumTagsHistogram $outdir/regionNumTagsHistogram.txt || exit 1
getRegionNumEditorsPerTagHistogram $outdir/regionNumEditorsPerTagHistogram.txt || exit 1
getRegionNumVersionsHistogram $outdir/regionNumVersionsHistogram.txt || exit 1
getRegionEditIntervalHistogram $outdir/regionEditIntervalHistogram.txt || exit 1
getRegionTagReversionHistogram $outdir/regionTagReversionHistogram.txt || exit 1
