#!/bin/sh

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# =====================
# = Convert & Extract =
# =====================

# args: <my_file.osh.pbf> <my_file.osh.xml.gz>
function convertToXml() {
  oshfile="$1"
  xmlfile="$2"
  if [ -f "${xmlfile}" ]
  then
    echo "  Found ${xmlfile}"
  else
    echo "  Converting to .xml.gz ..."
    $TIME $OSMCONVERT "${oshfile}" | gzip > "${xmlfile}" || return 1
  fi
}

# args: <my_file.osh.xml.gz> <my_file-node.txt> <my_file-node_tag.txt>
function extractXmlData() {
  if [ -f "${nodefile}" ] && [ -f "${tagfile}" ]
  then
    echo "  Found ${nodefile}"
    echo "  Found ${tagfile}"
  else
    echo "  Extracting tag edit history..."
    $TIME $RUBY ${ETL_SRCDIR}/extract_POI_tag_history.rb "${xmlfile}" "${nodefile}" "${tagfile}" || return 1
  fi
}

# args: *.osh.pbf files
# produces: *.osh.xml.gz, *-node.txt, *-node_tag.txt for each pbf file
function extractAll() {
  for oshfile in $@
  do
    filename="${oshfile%.osh.pbf}"
    name=`basename ${filename}`
    echo $name

    xmlfile="${filename}.osh.xml.gz"
    convertToXml "${oshfile}" "${xmlfile}" || return 1

    nodefile="${ETL_DATADIR}/${name}-node.txt"
    tagfile="${ETL_DATADIR}/${name}-node_tag.txt"
    extractXmlData "${xmlfile}" "${nodefile}" "${tagfile}" || return 1
  done
}

# ========
# = Load =
# ========

function truncate() {
  $PSQL -c "truncate node" || return 1
  $PSQL -c "truncate poi" || return 1
  $PSQL -c "truncate poi_tag" || return 1
}

# args: *-node.txt files
function loadNodeData() {
  for file in $@
  do
    echo $file
    $TIME $PSQL -c "\\copy node FROM '${file}' NULL AS ''" || return 1
  done
}

# args: *-node_tag.txt files
function loadNodeTagData() {
  for file in $@
  do
    echo $file
    $TIME $PSQL -c "\\copy poi_tag(poi_id, version, key, value) FROM '${file}' NULL AS ''" || return 1
  done
}

# =============
# = DB Tables =
# =============

function loadPoiTable() {
  echo "poi: all nodes with tags"
  $PSQL -c "INSERT INTO poi SELECT * FROM node WHERE node.id IN (SELECT DISTINCT poi_id FROM poi_tag) AND latitude IS NOT NULL AND longitude IS NOT NULL" || return 1
}

function loadPoiSequenceTable() {
  echo "poi_sequence: poi edit sequence without redactions"
  $PSQL -c "INSERT INTO poi_sequence (poi_id, version, prev_version, next_version) \
  SELECT p.id, p.version, \
  (SELECT max(version) FROM poi p2 WHERE p.id=p2.id AND p.version>p2.version) prev_version, \
  (SELECT min(version) FROM poi p3 WHERE p.id=p3.id AND p.version<p3.version) next_version \
  FROM poi p;"
}

# ========
# = Main =
# ========

# rm "${OSH_DATADIR}/"*.osh.xml.gz > /dev/null 2>&1
# rm "${ETL_DATADIR}/"*.txt > /dev/null 2>&1

# To prepare all files
echo "Extracting data..."
extractAll ${OSH_DATADIR}/*.osh.pbf || exit 1
# extractAll ${OSH_DATADIR}/berlin.osh.pbf || exit 1

# To prepare a specific file
# name=berlin
# convertToXml "${OSH_DATADIR}/${name}.osh.pbf" "${OSH_DATADIR}/${name}.osh.xml.gz" || exit 1
# extractXmlData "${OSH_DATADIR}/${name}.osh.xml.gz" "${ETL_DATADIR}/${name}-node.txt" "${ETL_DATADIR}/${name}-node_tag.txt" || return 1

echo "Loading data..."
truncate || exit 1

loadNodeData "${ETL_DATADIR}/"*-node.txt || exit 1
loadNodeTagData "${ETL_DATADIR}/"*-node_tag.txt || exit 1

echo "Preparing tables..."
loadPoiTable || exit 1
loadPoiSequenceTable || exit 1
