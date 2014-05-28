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
  parser.add_argument('--poi-type-column', help='The column name used for POI type IDs', dest='poitypecol', action='store', default='kind')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--min-poi-edits', help='The minimum number of edits per POI type in each country, POI types below this threshold will not be considered', dest='min_poi_edits', action='store', type=int, default=None)
  parser.add_argument('--num-top-poi', help='The number of top POI to analyse (ranked by popularity)', dest='num_top_poi', action='store', type=int, default=20)
  parser.add_argument('--num-top-poi-scatter', help='The number of top POI to show in scatter plots (ranked by popularity)', dest='num_top_poi_scatter', action='store', type=int, default=20)
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
  
  # dict: group -> poi-type -> dict of measures
  data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    kind = row[args.poitypecol]
    data[group][kind] = {
      measure: row[measure] for measure in measures + aux_measures
    }

  #
  # Filter according to options, if needed
  #
  group_size = lambda data, group: sum([ poidict['num_users'] for poidict in data[group].values() ])
  
  if args.num_groups:
    groups = top_keys(data, args.num_groups, summarise=group_size)
  else:
    groups = data.keys()
  
  print "Found %d groups: %s" % (len(groups), ", ".join(groups))
  print "Computing POI statistics for measures: %s" % ", ".join(measures)

  #
  # Most popular POI
  #
  
  all_kinds = sorted({ 
      kind for groupdict in data.values() 
            for kind in groupdict.keys() })

  if args.min_poi_edits:
    # dict: kind -> num countries below minimum edit threshold
    low_edit_kind = {
      kind: sum([
        1 for group in groups if data[group][kind]['num_edits'] < args.min_poi_edits
      ]) for kind in all_kinds
    }
    skip_kinds = [ kind for kind in low_edit_kind.keys() if low_edit_kind[kind] > 0 ]
    print "Ignoring %d POI types out of %d which fall below minimum edit threshold (%d)" % (len(skip_kinds), len(all_kinds), args.min_poi_edits)
    all_kinds = [kind for kind in all_kinds if kind not in skip_kinds]
    print "Number of remaining POI types: %d" % len(all_kinds)
  
  # dict: kind -> sum of user counts across countries
  all_counts = {
    kind: sum([ data[group][kind]['num_users'] for group in groups ])
      for kind in all_kinds
  }
  
  top_kinds = top_keys(all_counts, args.num_top_poi, 
    summarise=lambda data,key: data[key])

  top_kinds_scatter = top_keys(all_counts, args.num_top_poi_scatter, 
    summarise=lambda data,key: data[key])
  
  print "Selecting %d top POI types: %s" % (len(top_kinds), ", ".join(top_kinds))
  
  # ===================
  # = Feature vectors =
  # ===================
  
  # dict: group -> measure -> ordered vector of values, one per kind
  country_features_all = {
    group: {
      measure: [
        data[group][kind][measure] for kind in all_kinds
      ] for measure in measures
    } for group in groups
  }

  country_features_top = {
    group: {
      measure: [
        data[group][kind][measure] for kind in top_kinds
      ] for measure in measures
    } for group in groups
  }
  
  # dict: kind -> measure -> ordered vector of values, one per group
  poi_features = {
    kind: {
      measure: [
        data[group][kind][measure] for group in groups
      ] for measure in measures
    } for kind in all_kinds
  }
  
  # =================
  # = Compute stats =
  # =================
  
  make_stats = lambda stats_dict: {
    'delta-%pop': distance.cosine(stats_dict['%pop'], stats_dict['%coll_pop']),
    'delta-%edits': distance.cosine(stats_dict['%edits'], stats_dict['%coll_edits'])
  }
  
  # dict: group -> stat_name -> value
  country_all_poi_stats = {
    group: make_stats(country_features_all[group]) for group in groups
  }
  country_top_poi_stats = {
    group: make_stats(country_features_top[group]) for group in groups
  }
  
  # dict: kind -> stat_name -> value
  all_poi_country_stats = {
    kind: make_stats(poi_features[kind]) for kind in all_kinds
  }
  top_poi_country_stats = {
    kind: make_stats(poi_features[kind]) for kind in top_kinds
  }

  # ====================
  # = Reports & charts =
  # ====================

  mkdir_p(args.outdir)

  stat_names = ['delta-%pop', 'delta-%edits']
  
  # summary stats
  groupstat_report(country_all_poi_stats, args.groupcol, stat_names,
    args.outdir, 'country_all_poi_stats')
  
  groupstat_report(country_top_poi_stats, args.groupcol, stat_names,
    args.outdir, 'country_top_poi_stats')
  
  groupstat_report(all_poi_country_stats, args.poitypecol, stat_names,
    args.outdir, 'all_poi_country_stats')
  
  groupstat_report(top_poi_country_stats, args.poitypecol, stat_names,
    args.outdir, 'top_poi_country_stats')

  # boxplots: POI edit activity across countries
  cross_country_stats = {
    stat_name: {
      'top-types': [ country_top_poi_stats[group][stat_name] for group in groups ],
      'all-types': [ country_all_poi_stats[group][stat_name] for group in groups ]
    } for stat_name in stat_names
  }

  boxplot_matrix(cross_country_stats, stat_names, ['top-types', 'all-types'], 
    args.outdir, 'country_stat_boxplot')

  # ============
  # = Features =
  # ============

  features_dir = os.path.join(args.outdir, 'features')
  mkdir_p(features_dir)
  
  for group in groups:

    # all kinds
    groupstat_report(data[group], args.poitypecol, measures, 
      features_dir, 'all_poi_features_%s' % group)

    groupstat_report(data[group], args.poitypecol, aux_measures, 
      features_dir, 'all_poi_popsize_%s' % group)

    # top kinds
    top_poi_features = {
      kind: {
        measure: data[group][kind][measure] for measure in (measures + aux_measures)
      } for kind in top_kinds
    }

    groupstat_report(top_poi_features, args.poitypecol, measures, 
      features_dir, 'top_poi_features_%s' % group)

    groupstat_report(top_poi_features, args.poitypecol, aux_measures, 
      features_dir, 'top_poi_popsize_%s' % group)

  # =================
  # = Scatter plots =
  # =================

  # dict: group -> rel_scale_multiplier
  sizemap = { group: group_size(data, group) for group in groups }
  mean_size = np.mean(sizemap.values())
  sizemap = { group: min(max(0.5, sizemap[group] / mean_size), 5) for group in groups }

  # dict: kind -> <pop|edits> -> group -> dict of coll/all stats
  cross_stats = {
    kind: {
      variant: {
        group: {
          'coll': data[group][kind]['%%coll_%s' % variant],
          'all': data[group][kind]['%%%s' % variant]
        } for group in groups
      } for variant in ['pop', 'edits'] 
    } for kind in top_kinds_scatter
  }
  
  multi_scatter_matrix(cross_stats, top_kinds_scatter, ['pop', 'edits'], groups,
    'all', 'coll',
    args.outdir, 'all_vs_coll_scatter',
    sizemap=sizemap)
  