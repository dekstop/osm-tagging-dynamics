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
  parser.add_argument('--num-top-tags-scatter', help='The number of top tags to show in scatter plots (ranked by popularity)', dest='num_top_tags_scatter', action='store', type=int, default=20)
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
  group_size = lambda data, group: sum([ tagdict['num_users'] for tagdict in data[group].values() ])
  
  if args.num_groups:
    groups = top_keys(data, args.num_groups, summarise=group_size)
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

  top_tags_scatter = top_keys(all_tag_counts, args.num_top_tags_scatter, 
    summarise=lambda data,key: data[key])
  
  print "Selecting %d top tags: %s" % (len(top_tags), ", ".join(top_tags))
  
  # ===================
  # = Feature vectors =
  # ===================
  
  # dict: group -> measure -> ordered vector of values, one per tag
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
  
  # dict: tag -> measure -> ordered vector of values, one per group
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

  stat_names = ['delta-%pop', 'delta-%edits']
  
  # summary stats
  groupstat_report(country_all_tag_stats, groupcol, stat_names,
    args.outdir, 'country_all_tag_stats')
  
  groupstat_report(country_top_tag_stats, groupcol, stat_names,
    args.outdir, 'country_top_tag_stats')
  
  groupstat_report(all_tag_country_stats, tagcol, stat_names,
    args.outdir, 'all_tag_country_stats')
  
  groupstat_report(top_tag_country_stats, tagcol, stat_names,
    args.outdir, 'top_tag_country_stats')

  # boxplots: tag edit activity across countries
  cross_country_stats = {
    'top-tags': {
      stat_name: [ country_top_tag_stats[group][stat_name] for group in groups ]
        for stat_name in stat_names
    },
    'all-tags': {
      stat_name: [ country_all_tag_stats[group][stat_name] for group in groups ]
        for stat_name in stat_names
    },
  }

  boxplot_matrix(cross_country_stats, ['top-tags', 'all-tags'], stat_names,
    args.outdir, 'country_stat_boxplot')

  # =================
  # = Scatter plots =
  # =================

  # tag edit activity across countries
  # dict: <pop|edits> -> group -> <tag-label> -> value

  coll_stats = {
    kind: {
      group: {
        '%s-coll' % tag: data[group][tag]['%%coll_%s' % kind]
          for tag in top_tags_scatter
      } for group in groups
    } for kind in ['pop', 'edits'] 
  }
  all_stats = {
    kind: {
      group: {
        '%s-all' % tag: data[group][tag]['%%%s' % kind]
          for tag in top_tags_scatter
      } for group in groups
    } for kind in ['pop', 'edits'] 
  }
  
  coll_keys = ['%s-coll' % tag for tag in top_tags_scatter]
  all_keys = ['%s-all' % tag for tag in top_tags_scatter]
  
  sizemap = { group: group_size(data, group) for group in groups }
  mean_size = np.mean(sizemap.values())
  sizemap = { group: min(max(0.5, sizemap[group] / mean_size), 5) for group in groups }

  # (this is super memory-hungry!)

  scatter_matrix(coll_stats['pop'], all_stats['pop'], groups, coll_keys, all_keys, 
    args.outdir, '%pop_coll_vs_all_scatter',
    sizemap=sizemap)
  
  scatter_matrix(coll_stats['edits'], all_stats['edits'], groups, coll_keys, all_keys, 
    args.outdir, '%edits_coll_vs_all_scatter',
    sizemap=sizemap)
  