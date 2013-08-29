#!/bin/bash

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
  xmlfile="$1"
  nodefile="$2"
  tagfile="$3"
  if [ -f "${nodefile}" ] && [ -f "${tagfile}" ]
  then
    echo "  Found ${nodefile}"
    echo "  Found ${tagfile}"
  elif [ -f "${nodefile}.gz" ] && [ -f "${tagfile}.gz" ]
  then
    echo "  Found ${nodefile}.gz"
    echo "  Found ${tagfile}.gz"
  else
    echo "  Extracting tag edit history..."
    $TIME $RUBY ${ETL_SRCDIR}/extract_POI_tag_history.rb "${xmlfile}" "${nodefile}.gz" "${tagfile}.gz" || return 1
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
# = Main =
# ========

rm "${OSH_DATADIR}/"*.osh.xml.gz > /dev/null 2>&1
rm "${ETL_DATADIR}/"*.txt > /dev/null 2>&1

# To prepare all files
echo "Extracting data..."
extractAll ${OSH_DATADIR}/*.osh.pbf || exit 1
# extractAll ${OSH_DATADIR}/berlin.osh.pbf || exit 1

# To prepare a specific file
# name=berlin
# convertToXml "${OSH_DATADIR}/${name}.osh.pbf" "${OSH_DATADIR}/${name}.osh.xml.gz" || exit 1
# extractXmlData "${OSH_DATADIR}/${name}.osh.xml.gz" "${ETL_DATADIR}/${name}-node.txt.gz" "${ETL_DATADIR}/${name}-node_tag.txt.gz" || exit 1

