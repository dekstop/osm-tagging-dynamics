#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import gc
import sys

import pandas

import matplotlib.pyplot as plt
import numpy as np

from app import *
from shared import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('groupcol', help='Column name used to group population subsets')
  parser.add_argument('measures', help='Column names of population measures', nargs='+')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--num-bands', help='Number of population bands', dest='num_bands', action='store', type=int, default=5)
  args = parser.parse_args()

  #
  # Get data and transform it
  #
  
  df = pandas.read_csv(args.datafile, sep="\t")
  
  # measure -> group -> list of values
  data = defaultdict(lambda: defaultdict(list))
  
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    for measure in args.measures:
      data[measure][group].append(row[measure])

  #
  # Filter according to options, if needed
  #
  groups = top_keys(data[args.measures[0]], args.num_groups)

  print "Group column: %s" % args.groupcol
  print "Found %d groups" % len(groups)
  print "Computing population statistics for measures: %s" % ", ".join(args.measures)

  #
  # Per measure: band variance stats
  # 
  
  # dict: measure -> group -> stats_name -> value
  group_bands = defaultdict(lambda: defaultdict(dict))
  group_band_colnames = set()

  # dict: measure -> band -> value
  band_cv = defaultdict(dict)
  band_names = set()

  for measure in args.measures:
    for segmin, segmax in zip(range(args.num_bands), range(1, args.num_bands+1)):

      band = 'band_%d' % segmin
      band_names.add(band)
      min_perc = Decimal(segmin) / args.num_bands * 100
      max_perc = Decimal(segmax) / args.num_bands * 100
      
      for group in groups:
        all_values = [val for val in data[measure][group] if val>0]
        band_values = percentile_range(all_values, min_perc, max_perc)

        group_bands[measure][group]['%s_pop' % band] = len(band_values)
        group_band_colnames.add('%s_pop' % band)

        group_bands[measure][group]['%s_share' % band] = \
          float(sum(band_values)) / sum(all_values)
        group_band_colnames.add('%s_share' % band)
      
      band_shares = [group_bands[measure][group]['%s_share' % band] for group in groups]
      band_cv[measure][band] = np.std(band_shares) / np.mean(band_shares)
      
  #
  # Report: country profiles
  #
  
  mkdir_p(args.outdir)
  
  for measure in args.measures:
    segment_report(group_bands[measure], 'country', sorted(group_band_colnames), 
      args.outdir, 'country_bands_%s' % measure)

  segment_report(band_cv, 'measure', sorted(band_names), 
    args.outdir, 'band_cv_scores')

  # 
  # #
  # # Graphs: country profiles
  # #
  # 
  # # Countries are ranked by number of users, descending
  # iso2s = sorted(stats.keys(), key=lambda iso2: stats[iso2]['num_users'], reverse=True)
  # 
  # group_share_plot(stats, iso2s, 
  #   ['p_top_users', 
  #   'p_coll_users', 'p_top_coll_users', 
  #   'coll_users_gini',
  #   'coll_users_theil'], 
  #   args.outdir, 'country_profiles_users')
  # 
  # group_share_plot(stats, iso2s, 
  #   ['p_coll_edits', 
  #   'p_coll_tag_add', 'p_coll_tag_update', 'p_coll_tag_remove'], 
  #   args.outdir, 'country_profiles_edits')
