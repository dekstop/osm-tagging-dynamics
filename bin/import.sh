#!/bin/sh

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# oshfiles="${OSH_DATADIR}/*.osh.pbf"
oshfiles="${OSH_DATADIR}/mainz.osh.pbf"

# =====================
# = Convert & Extract =
# =====================

rm "${ETL_DATADIR}/"*.txt > /dev/null 2>&1

for oshfile in $oshfiles
do
  filename="${oshfile%.osh.pbf}"
  name=`basename ${filename}`
  xmlfile="${filename}.osh.xml.gz"
  
  echo "${name}..."
  echo "  Converting to .xml.gz"
  # $OSMCONVERT "${oshfile}" | gzip > "${xmlfile}" || exit 1
  echo "  Extracting tag edit history"
  time $RUBY ${ETL_SRCDIR}/extract_POI_tag_history.rb "${xmlfile}" "${ETL_DATADIR}/${name}-poi.txt" "${ETL_DATADIR}/${name}-poi_tag.txt" || exit 1
done

# ========
# = Load =
# ========

echo "Loading data..."

$PSQL -c "truncate poi" || exit 1
$PSQL -c "truncate poi_tag" || exit 1

for file in "${ETL_DATADIR}/"*-poi.txt
do
  echo $file
  time $PSQL -c "\\copy poi FROM '${file}' NULL AS ''" || exit 1
done

for file in "${ETL_DATADIR}/"*-poi_tag.txt
do
  echo $file
  time $PSQL -c "\\copy poi_tag FROM '${file}' NULL AS ''" || exit 1
done

