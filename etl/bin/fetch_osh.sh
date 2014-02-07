#!/bin/bash

BIN=$( cd "$( dirname "$0" )" && pwd )
. ${BIN}/env.sh

# ========
# = Main =
# ========

year=2014
tag=2014-01-06
rootUrl=http://osm.personalwerk.de/full-history-extracts/${year}/${tag}/continents
files="africa antarctica asia australia-oceania central-america europe north-america south-america"

oshDir=${OSH_DATADIR}/continents-${tag}
echo "Storing files in ${oshDir}"
mkdir -p ${oshDir} > /dev/null 2>&1

for name in ${files}
do
  url=${rootUrl}/${name}.osh.pbf
  dest=${oshDir}/${name}.osh.pbf
  echo "Fetching ${url} ..."
  curl ${url} -o ${dest} || exit 1
done
