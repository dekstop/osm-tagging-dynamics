#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
from decimal import Decimal

import pandas
from scipy.spatial import distance

from app import *
from shared import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--num-top-tags', help='The number of top tags to analyse (ranked by popularity)', dest='num_top_tags', action='store', type=int, default=20)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  tagcol = 'key'
  measures = ['%pop', '%coll_pop', '%edits', '%coll_edits']
  aux_measures = ['num_users', 'num_edits', 'num_coll_users', 'num_coll_edits']

  # ============================
  # = Load data & transform it =
  # ============================

  df = pandas.read_csv(args.datafile, sep="\t", encoding='utf-8')
  
  # dict: group -> tag -> dict of measures
  data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))
  for idx, row in df.iterrows():
    group = row[groupcol]
    tag = row[tagcol]
    data[group][tag] = {
      measure: row[measure] for measure in measures + aux_measures
    }

  #
  # Filter according to options, if needed
  #
  if args.num_groups:
    groups = top_keys(data, args.num_groups,
      summarise=lambda data, key: 
        sum([ tagdict['num_users'] for tagdict in data[key].values() ]))
  else:
    groups = data.keys()
  
  print "Found %d groups" % len(groups)
  print "Computing tag statistics for measures: %s" % ", ".join(measures)

  #
  # Most popular tags
  #
  all_tags = sorted({ 
      tag for groupdict in data.values() 
            for tag in groupdict.keys() })

  all_tag_counts = {
    tag: sum([ data[group][tag]['num_users'] for group in groups ])
    for tag in all_tags
  }

  top_tags = top_keys(all_tag_counts, args.num_top_tags, 
    summarise=lambda data,key: data[key])
  
  print "Selecting %d top tags: %s" % (len(top_tags), ", ".join(top_tags))
  
  # ===================
  # = Feature vectors =
  # ===================
  
  # dict: group -> measure -> ordered vector of values
  country_features_all = {
    group: {
      measure: [
        data[group][tag][measure] for tag in all_tags
      ] for measure in measures
    } for group in groups
  }

  country_features_top = {
    group: {
      measure: [
        data[group][tag][measure] for tag in top_tags
      ] for measure in measures
    } for group in groups
  }
  
  # dict: tag -> measure -> ordered vector of values
  tag_features = {
    tag: {
      measure: [
        data[group][tag][measure] for group in groups
      ] for measure in measures
    } for tag in all_tags
  }
  
  # =================
  # = Compute stats =
  # =================
  
  stat_names = ['delta-%pop', 'delta-%edits']
  
  make_stats = lambda stats_dict: {
    'delta-%pop': distance.cosine(stats_dict['%pop'], stats_dict['%coll_pop']),
    'delta-%edits': distance.cosine(stats_dict['%edits'], stats_dict['%coll_edits']),
  }
  
  # dict: group -> stat_name -> value
  country_all_tag_stats = {
    group: make_stats(country_features_all[group]) for group in groups
  }
  country_top_tag_stats = {
    group: make_stats(country_features_top[group]) for group in groups
  }
  
  # dict: tag -> stat_name -> value
  all_tag_country_stats = {
    tag: make_stats(tag_features[tag]) for tag in all_tags
  }
  top_tag_country_stats = {
    tag: make_stats(tag_features[tag]) for tag in top_tags
  }

  # ====================
  # = Reports & charts =
  # ====================

  mkdir_p(args.outdir)

  groupstat_report(country_all_tag_stats, groupcol, stat_names,
    args.outdir, 'country_all_tag_stats')

  groupstat_report(country_top_tag_stats, groupcol, stat_names,
    args.outdir, 'country_top_tag_stats')

  groupstat_report(all_tag_country_stats, tagcol, stat_names,
    args.outdir, 'all_tag_country_stats')

  groupstat_report(top_tag_country_stats, tagcol, stat_names,
    args.outdir, 'top_tag_country_stats')
