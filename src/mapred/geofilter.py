#!/usr/bin/python

#
# Filter *-node.txt records based on geo coordinates.
#
# To set the number of splits: 
#   --jobconf mapred.map.tasks=<num_splits>
#
# node.txt file format:
# - id          INTEGER NOT NULL,
# - version     INTEGER NOT NULL,
# - changeset   INTEGER NOT NULL,
# - timestamp   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
# - uid         INTEGER,
# - username    TEXT,
# - latitude    NUMERIC,
# - longitude   NUMERIC
#
# martind 2013-08-05 

from mrjob.job import MRJob
from mrjob.protocol import *

class FilterJob(MRJob):
	INPUT_PROTOCOL = RawValueProtocol
	INTERNAL_PROTOCOL = PickleProtocol
	OUTPUT_PROTOCOL = RawValueProtocol
	
	def configure_options(self):
		super(FilterJob, self).configure_options()
		self.add_passthrough_option('--minlat')
		self.add_passthrough_option('--minlon')
		self.add_passthrough_option('--maxlat')
		self.add_passthrough_option('--maxlon')

	def mapper_init(self):
		self.minlat, self.maxlat = sorted([
			float(self.options.minlat), float(self.options.maxlat)])
		self.minlon, self.maxlon = sorted([
			float(self.options.minlon), float(self.options.maxlon)])
	
	def mapper(self, _, line):
		cols = line.split("\t")

		if len(cols)!=8:
			self.increment_counter('data', 'wrong_column_count', 1)
			return

		if cols[6]=='' or cols[7]=='':
			self.increment_counter('data', 'empty_latlon', 1)
			return

		lat = float(cols[6])
		lon = float(cols[7])
		if ((self.minlat <= lat <= self.maxlat) and 
				(self.minlon <= lon <= self.maxlon)):
			yield None, line
			self.increment_counter('filter', 'include', 1)
		else:
			self.increment_counter('filter', 'exclude', 1)
	
	# def combiner(self, _, line):
	# 	pass
	
	# def reducer(self, _, line):
	# 	pass
	

if __name__ == "__main__":
	FilterJob.run()
