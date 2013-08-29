#!/bin/sh

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

for continent in africa antarctica asia australia-oceania central-america europe north-america
do 
  echo =============
  echo $continent
  echo =============
  echo
  pig \
    -p input_node=s3://osm-research/tsv-compressed/continents/node/${continent} \
    -p input_node_tag=s3://osm-research/tsv-compressed/continents/node_tag/${continent} \
    -p output=s3://osm-research/poi-regions/hotspot-regions-20130829-01/continents/${continent} \
    ${SRCDIR}/mapred/geofilter.pig || exit 1
done
