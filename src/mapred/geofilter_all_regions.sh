#!/bin/sh
SCRIPT_DIR=$( cd "$( dirname "$0" )" && pwd )

echo "Making region parameter files..."
ruby "${SCRIPT_DIR}"/regions/make_param_files.rb

echo "Running Pig jobs..."
for regionfile in "${SCRIPT_DIR}"/regions/region_*.pig
do
  echo $regionfile
  pig -param_file $regionfile "${SCRIPT_DIR}"/geofilter.pig -stop_on_failure || exit 1
done
