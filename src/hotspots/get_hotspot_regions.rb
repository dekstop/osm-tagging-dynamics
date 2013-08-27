#!/usr/bin/env ruby

require 'csv'
require 'fileutils'
require 'set'

# =========
# = Prefs =
# =========

HEADERS = [:lat, :lon, :num_poi, :mean_version, :max_version, :mean_users, :max_users]

LAT_GRID = 0.5
LON_GRID = 0.5

HOTSPOT_SCORE_PERCENTILE = 0.99 # Share of all points considered hotspots

REGION_SEARCH_DEPTH = 3 # bounding box dimensions in number of LAT_GRID/LON_GRID units from current centre
REGION_SEARCH_VECTORS = (-REGION_SEARCH_DEPTH..REGION_SEARCH_DEPTH).map do |x|
  (-REGION_SEARCH_DEPTH..REGION_SEARCH_DEPTH).map do |y| 
    [x * LAT_GRID, y * LON_GRID]
  end
end.flatten(1).select{|v| v!=[0,0] }

REGION_LAT_BORDER = LAT_GRID
REGION_LON_BORDER = LON_GRID

# ========
# = Util =
# ========

# Bugfix: first version of the hotspot script didn't properly attribute centroids
def convert_centroid(lat, lon)
  [lat + LAT_GRID/2, lon + LON_GRID/2]
end

# Transform a raw array of values into a map with column keys
def to_record(row)
  rec = Hash[HEADERS.zip(row)]
  return {
    :lat => rec[:lat].to_f,
    :lon => rec[:lon].to_f,
    :num_poi => rec[:num_poi].to_i,
    :mean_version => rec[:mean_version].to_f,
    :mean_users => rec[:mean_users].to_f
  }
end

def moveBy(loc, distance)
  [loc[0] + distance[0], loc[1] + distance[1]]
end

# Collect all immediately adjacent locations that have score >= min_score
def collect_hotspots(map, min_score, loc, hotspots=Set.new)
  hotspots << loc
  REGION_SEARCH_VECTORS.each do |offset|
    neighbor = moveBy(loc, offset)
    if !hotspots.include?(neighbor) then
      if !map[neighbor].nil? && map[neighbor][:score] >= min_score then
        hotspots.merge(collect_hotspots(map, min_score, neighbor, hotspots))
      end
    end
  end
  return hotspots
end

# ========
# = Main =
# ========

if (ARGV.size!=2) then
  puts "<geo_edit_hotspots_stats.txt> <result dirname>"
  exit 1
end

filename = ARGV[0]
outdir = ARGV[1]

# Prepare
if File.directory?(outdir) then
  puts "Directory exists, will overwrite files: #{outdir}"
  # exit 1
end

FileUtils.mkdir_p(outdir)

map = Hash.new
latitudes = Set.new
longitudes = Set.new
locations = []

# Load and transform
puts 'Loading...'
CSV::IOReader.new(open(filename), "\t").each do |row|
  record = to_record(row)
  (record[:lat], record[:lon]) = convert_centroid(record[:lat], record[:lon])
  latitudes << record[:lat]
  longitudes << record[:lon]
  loc = [record[:lat], record[:lon]]
  locations << loc
  map[loc] = record
end

# Score
puts 'Scoring...'
locations.each do |loc|
  if !map[loc].nil?
    if (map[loc][:num_poi] >= 100)
      map[loc][:score] = 
        Math.log(map[loc][:mean_version] + 1) *
        Math.log(map[loc][:mean_users] + 1)
    else
      map[loc][:score] = 0
    end
  end
end

# Hotspot score cutoff
scores = map.values.map{|rec| rec[:score]}.sort
score_cutoff = scores[(scores.size * HOTSPOT_SCORE_PERCENTILE).to_i]
# score_cutoff = 1.0
puts "Cutoff score for top #{HOTSPOT_SCORE_PERCENTILE * 100}%: #{score_cutoff}"

File.open("#{outdir}/scores.txt", 'wb') do |f|
  fields = [:lat, :lon, :mean_version, :mean_users, :score]
  f << fields.join("\t") + "\n"
  locations.each do |loc|
    f << fields.map{|col| map[loc][col] }.join("\t") + "\n"
  end
end

# Hotspots
puts 'Finding hotspots...'
hotspots = Set.new
locations.each do |loc|
  if !map[loc].nil?
    if (map[loc][:score] >= score_cutoff)
      hotspots << loc
    end
  end
end

File.open("#{outdir}/hotspots.txt", 'wb') do |f|
  fields = [:lat, :lon, :mean_version, :mean_users, :score]
  f << fields.join("\t") + "\n"
  hotspots.each do |loc|
    f << fields.map{|col| map[loc][col] }.join("\t") + "\n"
  end
end

# Regions
puts 'Merging regions...'
regions = []
region_points = []
to_visit = hotspots.to_a
while !to_visit.empty? 
  loc = to_visit.shift
  # puts "Next centre: #{loc}"
  hs_locations = collect_hotspots(map, HOTSPOT_SCORE_PERCENTILE, loc)
  hs_locations.each {|loc| to_visit.delete(loc) }
  region_points << hs_locations

  hs_latitudes = hs_locations.map {|loc| loc[0] }
  hs_longitudes = hs_locations.map {|loc| loc[1] }

  region = {
    :minlat => hs_latitudes.min - REGION_LAT_BORDER,
    :maxlat => hs_latitudes.max + REGION_LAT_BORDER,
    :minlon => hs_longitudes.min - REGION_LON_BORDER,
    :maxlon => hs_longitudes.max + REGION_LON_BORDER
  }
  regions << region
end

# As TSV
File.open("#{outdir}/regions.txt", 'wb') do |f|
  idx = 0
  regions.each do |region|
    f << ["region_#{idx}", 
      region[:minlat], region[:minlon], 
      region[:maxlat], region[:maxlon]].join("\t") + "\n"
    idx += 1
  end
end

# As Pig filter
File.open("#{outdir}/region_filter.pig", 'wb') do |f|
  f << "-- Generated from #{filename}\n"
  f << "-- #{Time.now}\n"
  f << "filtered_node = FILTER node BY \n"
  regions.each_with_index do |region, idx|
    f << "  ((#{region[:minlat]} <= latitude) AND (latitude <= #{region[:maxlat]}) AND (#{region[:minlon]} <= longitude) AND (longitude <= #{region[:maxlon]}))"
    ["region_#{idx}", 
      region[:minlat], region[:minlon], 
      region[:maxlat], region[:maxlon]].join("\t") + "\n"
    if idx < (regions.size-1)
      f << " OR " 
    else
      f << ";"
    end
    f << "\n"
  end
end

# As GeoJSON
File.open("#{outdir}/regions.geojson", 'wb') do |f|
  cur_id = 1
  
  f << "{\n"
  f << "\"type\": \"FeatureCollection\",\n"
  f << "\"crs\": { \"type\": \"name\", \"properties\": { \"name\": \"urn:ogc:def:crs:OGC:1.3:CRS84\" } },\n"
  f << "\"features\": [\n"

  # # Hotspot points
  # f << "  { \n"
  # f << "    \"type\": \"Feature\", \n"
  # f << "    \"properties\": { \"id\": #{cur_id}, \"name\": \"hotspots\" },\n"
  # cur_id += 1
  # f << "    \"geometry\": { \"type\": \"MultiPoint\", \"coordinates\": [ \n"
  #   hotspots.each_with_index do |loc,idx|
  #   f << "      [ #{loc[1]}, #{loc[0]} ]"
  #   f << "," if idx < (hotspots.size-1)
  #   f << "\n"
  # end
  # f << "    ] }\n"
  # f << "  }"
  # f << "," if region_points.size>0 || regions.size > 0
  # f << "\n"

  # Region points
  region_points.each_with_index do |points, idx|
    f << "  { \n"
    f << "    \"type\": \"Feature\", \n"
    f << "    \"properties\": { \"id\": #{cur_id}, \"name\": \"region_point_#{cur_id}\" },\n"
    cur_id += 1
    f << "    \"geometry\": { \"type\": \"MultiPoint\", \"coordinates\": [ \n"
      points.each_with_index do |loc,idx|
      f << "      [ #{loc[1]}, #{loc[0]} ]"
      f << "," if idx < (points.size-1)
      f << "\n"
    end
    f << "    ] }\n"
    f << "  }"
    f << "," if idx < (region_points.size-1) || regions.size > 0
    f << "\n"
  end

  # Merged regions
  regions.each_with_index do |region, idx|
    f << "  { \n"
    f << "    \"type\": \"Feature\", \n"
    f << "    \"properties\": { \"id\": #{cur_id}, \"name\": \"region_#{cur_id}\" },\n"
    cur_id += 1
    f << "    \"geometry\": { \"type\": \"Polygon\", \"coordinates\": [[ \n"
    f << "      [ #{region[:minlon]}, #{region[:minlat]} ],\n"
    f << "      [ #{region[:maxlon]}, #{region[:minlat]} ],\n"
    f << "      [ #{region[:maxlon]}, #{region[:maxlat]} ],\n"
    f << "      [ #{region[:minlon]}, #{region[:maxlat]} ],\n"
    f << "      [ #{region[:minlon]}, #{region[:minlat]} ]\n"
    f << "    ]] }\n"
    f << "  }"
    f << "," if idx < (regions.size-1)
    f << "\n"
  end

  f << "]}"
end

# Done.
puts "Map size: #{locations.size} grid centroids."
puts "Found #{hotspots.size} hotspots, merged into #{regions.size} regions."
