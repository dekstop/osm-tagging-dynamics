#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
from decimal import Decimal
import os.path

import matplotlib.pyplot as plt
import pandas
from scipy.spatial import distance

from app import *
from shared import *

# =========
# = Plots =
# =========

# data: row -> column -> group -> dict of stats
# row_keys: list of rows to plot
# col_keys: list of columns to plot
# groups: list of groups to plot
# x_stat: horizontal plot measure
# y_stat: vertical plot measure
# outdir:
# filename_base:
# scale:
# colors:
# size: dot size in points^2
# sizemap: a map from group name to a [0..1] size multiplier
#
# kwargs is passed on to plt.scatter(...).
def multi_scatter_matrix(data, row_keys, col_keys, groups, x_stat, y_stat, 
  outdir, filename_base,  scale='linear', colors=QUALITATIVE_MEDIUM, size=20, 
  sizemap=None, **kwargs):
  
  for (col, row, ax1) in plot_matrix(col_keys, row_keys):
    x = [data[row][col][group][x_stat] for group in groups]
    y = [data[row][col][group][y_stat] for group in groups]

    s = size
    if sizemap!=None:
      s = [sizemap[group] * size for group in groups]

    ax1.scatter(x, y, s=s, edgecolors='none', color=colors[0], **kwargs)

    ax1.margins(0.2, 0.2)
    ax1.set_xscale(scale)
    ax1.set_yscale(scale)
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

  # free memory
  plt.close() # closes current figure
  gc.collect()


# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--group-column', help='The column name used for group IDs', dest='groupcol', action='store', default='country')
  parser.add_argument('--tag-column', help='The column name used for tag IDs', dest='tagcol', action='store', default='key')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--num-top-tags', help='The number of top tags to analyse (ranked by popularity)', dest='num_top_tags', action='store', type=int, default=20)
  parser.add_argument('--num-top-tags-scatter', help='The number of top tags to show in scatter plots (ranked by popularity)', dest='num_top_tags_scatter', action='store', type=int, default=20)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  measures = ['%pop', '%coll_pop', '%edits', '%coll_edits']
  aux_measures = ['num_users', 'num_edits', 'num_coll_users', 'num_coll_edits']

  # ============================
  # = Load data & transform it =
  # ============================

  df = pandas.read_csv(args.datafile, sep="\t", encoding='utf-8')
  
  # dict: group -> tag -> dict of measures
  data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    tag = row[args.tagcol]
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
  
  print "Found %d groups: %s" % (len(groups), ", ".join(groups))
  print "Computing tag statistics for measures: %s" % ", ".join(measures)

  #
  # Most popular tags
  #
  
  all_tags = sorted({ 
      tag for groupdict in data.values() 
            for tag in groupdict.keys() })

  # dict: tag -> sum of user counts across countries
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
    'delta-%edits': distance.cosine(stats_dict['%edits'], stats_dict['%coll_edits'])
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
  groupstat_report(country_all_tag_stats, args.groupcol, stat_names,
    args.outdir, 'country_all_tag_stats')
  
  groupstat_report(country_top_tag_stats, args.groupcol, stat_names,
    args.outdir, 'country_top_tag_stats')
  
  groupstat_report(all_tag_country_stats, args.tagcol, stat_names,
    args.outdir, 'all_tag_country_stats')
  
  groupstat_report(top_tag_country_stats, args.tagcol, stat_names,
    args.outdir, 'top_tag_country_stats')

  # boxplots: tag edit activity across countries
  cross_country_stats = {
    stat_name: {
      'top-tags': [ country_top_tag_stats[group][stat_name] for group in groups ],
      'all-tags': [ country_all_tag_stats[group][stat_name] for group in groups ]
    } for stat_name in stat_names
  }

  boxplot_matrix(cross_country_stats, stat_names, ['top-tags', 'all-tags'], 
    args.outdir, 'country_stat_boxplot')

  # ============
  # = Features =
  # ============

  features_dir = os.path.join(args.outdir, 'features')
  mkdir_p(features_dir)
  
  for group in groups:

    # all tags
    groupstat_report(data[group], args.tagcol, measures, 
      features_dir, 'all_tags_features_%s' % group)

    groupstat_report(data[group], args.tagcol, aux_measures, 
      features_dir, 'all_tags_popsize_%s' % group)

    # top tags
    top_tag_features = {
      tag: {
        measure: data[group][tag][measure] for measure in (measures + aux_measures)
      } for tag in top_tags
    }

    groupstat_report(top_tag_features, args.tagcol, measures, 
      features_dir, 'top_tags_features_%s' % group)

    groupstat_report(top_tag_features, args.tagcol, aux_measures, 
      features_dir, 'top_tags_popsize_%s' % group)

  # =================
  # = Scatter plots =
  # =================

  # dict: group -> rel_scale_multiplier
  sizemap = { group: group_size(data, group) for group in groups }
  mean_size = np.mean(sizemap.values())
  sizemap = { group: min(max(0.5, sizemap[group] / mean_size), 5) for group in groups }

  # dict: tag -> <pop|edits> -> group -> dict of coll/all stats
  cross_stats = {
    tag: {
      kind: {
        group: {
          'coll': data[group][tag]['%%coll_%s' % kind],
          'all': data[group][tag]['%%%s' % kind]
        } for group in groups
      } for kind in ['pop', 'edits'] 
    } for tag in top_tags_scatter
  }
  
  multi_scatter_matrix(cross_stats, top_tags_scatter, ['pop', 'edits'], groups,
    'all', 'coll',
    args.outdir, 'all_vs_coll_scatter',
    sizemap=sizemap)
  