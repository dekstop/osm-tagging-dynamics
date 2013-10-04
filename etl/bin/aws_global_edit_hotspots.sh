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
    -p output=s3://osm-research/stats/edit_hotspot_stats-20130829-01/continents/${continent} \
    ${SRCDIR}/mapred/edit_hotspot_stats.pig || exit 1
done
