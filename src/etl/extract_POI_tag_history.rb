#!/usr/bin/env ruby

# Extract POI/tag history data from .osh.xml[.gz] files.
# Produces a set of TSV files that can be loaded into a postgres DB.
# 
# martind 2013-07-12 14:58:09
# 
# Input format:
#   <?xml version='1.0' encoding='UTF-8'?>
#   <osm version="0.6" generator="osmconvert 0.7Q">
#     <bounds minlat="49.9507" minlon="8.2051" 
#       maxlat="50.0385" maxlon="8.3349"/>
#     <node id="162809" lat="49.9997359" lon="8.1757629" version="2"
#       timestamp="2008-04-20T18:18:33Z" changeset="201924" uid="20751"
#       user="Christian Karrié">
#       <tag k="created_by" v="YahooApplet 1.0"/>
#     </node>
#     <node id="162809" lat="49.9997359" lon="8.1757629" version="3"
#       timestamp="2009-08-11T16:26:31Z" changeset="2109911" uid="109925"
#       user="WanMil"/>
#   ...


require 'rubygems'
require 'xml'
require 'zlib'

# =========
# = Tools =
# =========

def is_a(xml, tag_name)
  (xml.node_type == XML::Reader::TYPE_ELEMENT && xml.name == tag_name)
end

require 'pp'

# returns false when at end of file
def seek_to_tag(xml, tag_name)
  ret = true
  while ret==true && !is_a(xml, tag_name)
    ret = xml.read
  end
  ret
end

# returns false when at end of file
def seek_to_next_tag(xml)
  ret = true
  begin
    ret = xml.read
  end while (ret==true && xml.node_type != XML::Reader::TYPE_ELEMENT)
  ret
end

# returns false when at end of file
def skip_next(xml, tag_name)
  seek_to_tag(xml, tag_name) or return false
  xml.read
end

def each_child(xml, tag_name)
  xml.node.each_element do |node|
    # if is_a(node, tag_name)
      yield node
    # end
  end
end

def get_attributes(xml)
  attrs = {}
  xml.attribute_count.times do |i|
    xml.move_to_attribute_no(i)
    attrs[xml.name] = xml.value
  end
  attrs
end

def escape(str)
  str.nil? ? str : str.
    gsub(/\\/,'\\\\\\'). # escape backslashes
    gsub(/\r/, '\\r').
    gsub(/\t/, '\\t').
    gsub(/\n/, '\\n')
end

# http://stackoverflow.com/questions/1034418/determine-if-a-string-is-a-valid-float-value
class String
  def valid_float?
    !!Float(self) rescue false
  end
  def valid_int?
    !!Integer(self) rescue false
  end
end

def parse_float(str)
  str.nil? ? str : (str.valid_float? ? str.to_f : nil)
end

def parse_int(str)
  str.nil? ? str : (str.valid_int? ? str.to_i : nil)
end

# ========
# = Main =
# ========

if ARGV.size!=3
  puts '<OSM *.osh.xml.gz file> <output POI file> <output tag file>'
  puts 'Produces a set of TSV files that can be loaded into a DB.'
  exit 1
end

if (ARGV[0].end_with?('.gz'))
  xml = XML::Reader.io(Zlib::GzipReader.new(File.new(ARGV[0])))
else
  xml = XML::Reader.file(ARGV[0])
end

nodefile = File.new(ARGV[1], 'w')
tagfile = File.new(ARGV[2], 'w')

# 240000.times { |n| skip_next(xml, 'node') }
# seek_to_tag(xml, 'does_not_exist') or exit

keep_scanning = true
while keep_scanning
  seek_to_tag(xml, 'node') or break
  node = get_attributes(xml)

  id = parse_int(node['id'])
  version = parse_int(node['version'])
  changeset = parse_int(node['changeset'])
  timestamp = escape(node['timestamp'])
  uid = parse_int(node['uid'])
  username = escape(node['user'])
  lat = parse_float(node['lat'])
  lon = parse_float(node['lon'])

  nodefile.write("#{id}\t#{version}\t#{changeset}\t#{timestamp}\t#{uid}\t" +
    "#{username}\t#{lat}\t#{lon}\n")
  
  seek_to_next_tag(xml) or keep_scanning=false
  if keep_scanning
    if is_a(xml, 'tag')
      while is_a(xml, 'tag')
        tag = get_attributes(xml)
        tagfile.write("#{id}\t#{version}\t#{escape(tag['k'])}\t#{escape(tag['v'])}\n")
        seek_to_next_tag(xml) # or puts "done"
      end
    else
      # No tags for this node & version
    end
  end
end

nodefile.close
tagfile.close
