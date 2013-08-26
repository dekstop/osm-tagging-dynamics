#!/usr/bin/env ruby

SCRIPT_DIR = File.dirname(__FILE__)
TEMPLATE = File.read("#{SCRIPT_DIR}/TEMPLATE.pig")

File.read("#{SCRIPT_DIR}/regions.txt").each_line do |line|
  cols = line.chomp.split("\t")
  name = cols[0]
  puts "#{name}..."
  File.open("#{SCRIPT_DIR}/region_#{name}.pig", 'w') do |f|
    TEMPLATE.each_line do |tl|
      cols.each_index do |idx|
        tl = tl.gsub("{{#{idx}}}", cols[idx])
      end
      f << tl
    end
  end
end
