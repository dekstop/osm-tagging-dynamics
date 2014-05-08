#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
from decimal import Decimal
import gc
import sys

import pandas

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
import numpy.linalg as linalg

from app import *
from shared import *

# =========
# = Plots =
# =========

# data: column -> row -> list of values
# kwargs is passed on to plt.boxplot(...).
def boxplot_matrix(data, columns, rows, outdir, filename_base, min_values=5,
   shared_yscale=True, show_minmax=True, **kwargs):

  for (column, row, ax1) in plot_matrix(columns, rows, shared_yscale=shared_yscale):
    values = data[column][row]
    if len(values) < min_values:
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      mean = np.mean(values)
      norm_values = [v / mean for v in values]
      ax1.boxplot(norm_values, **kwargs)
      
      if show_minmax:
        w = 0.1
        plt.plot([-w, w], [min(values)]*2, 'k-')
        plt.plot([-w, w], [max(values)]*2, 'k-')

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--num-segments', help='The number of segments per group', dest='num_segments', action='store', type=int, default=4)
  parser.add_argument('--threshold-base', help='The "power of x" base when calculating segment thresholds', dest='threshold_base', action='store', type=int, default=10)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  
  # segmentation: powers of ten
  segments = [args.threshold_base**p for p in range(args.num_segments-1)]
  # segments = [2**p for p in range(5)]
  # segments = [5**p for p in range(4)]
  # segments = [10**p for p in range(4)]
  thresholds = zip([None] + segments, segments + [None])
  threshold_label = lambda n1, n2: \
    '%d<n<=%d' % (n1, n2) if (n1 and n2) else \
    'n>%s' % n1 if (not n2) else \
    'n=%d' % n2
  threshold_labels = [threshold_label(min1, max1) for (min1, max1) in thresholds]
  
  # ============================
  # = Load data & transform it =
  # ============================

  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(groupcol)
  
  # dict: group -> list of user dicts
  data = defaultdict(list)
  for idx, row in df.iterrows():
    group = row[groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[group].append(rec)

  #
  # Filter according to options, if needed
  #

  groups = top_keys(data, args.num_groups)
  print "Found %d groups" % len(groups)

  # =================
  # = Compute stats =
  # =================

  #
  # Per group: segment users
  # 

  # dict: group -> metric -> value(s)
  pop = defaultdict(dict)
  for group in groups:
    pop[group]['edits'] = [d['num_edits'] for d in data[group] if d['num_edits']>0]
    pop[group]['pop'] = len(pop[group]['edits'])
    pop[group]['total'] = sum(pop[group]['edits'])

    pop[group]['coll_edits'] = [d['num_coll_edits'] for d in data[group] if d['num_coll_edits']>0]
    pop[group]['coll_pop'] = len(pop[group]['coll_edits'])
    pop[group]['coll_total'] = sum(pop[group]['coll_edits'])
  
  # dict: group -> segment -> list of values
  coll_seg = defaultdict(dict)
  for group in groups:
    for (min1, max1) in thresholds:
      coll_seg[group][threshold_label(min1, max1)] = \
        [v for v in pop[group]['coll_edits'] 
          if (min1==None or v>min1)
          and (max1==None or v<=max1)]
  
  #
  # Per group: compute summary stats
  # 

  # dict: stat -> group -> segment -> value
  stats = defaultdict(lambda: defaultdict(dict))
  for group in groups:
    for label in threshold_labels:
      values = coll_seg[group][label]
      seg_num_users = len(values)
      seg_num_edits = sum(values)
      stats['#users'][group][label] = seg_num_users
      # stats['%coll_pop'][group][label] = seg_num_users / Decimal(pop[group]['coll_pop'])
      stats['%pop'][group][label] = seg_num_users / Decimal(pop[group]['pop'])
      stats['%edits'][group][label] = seg_num_edits / Decimal(pop[group]['total'])
      # stats['cov_coll_edits'][group][label] = np.std(values) / np.mean(values)

  #
  # Segment variances across groups
  #
  
  stat_names = ['#users', '%pop', '%edits']
  
  # dict: segment -> stat -> list of values
  seg_stats = { 
    label: { 
      stat_name: 
        [float(stats[stat_name][group][label]) for group in groups] 
      for stat_name in stat_names }
    for label in threshold_labels }
  
  # dict: stat -> segment -> value
  cov_seg_stats = { 
    stat_name: { 
      label:
        np.std(seg_stats[label][stat_name])/np.mean(seg_stats[label][stat_name]) 
      for label in threshold_labels }
    for stat_name in stat_names }

  # # dict: segment -> stat -> value
  # cov_seg_stats = { 
  #   label: { 
  #     stat_name:
  #       np.std(seg_stats[label][stat_name])/np.mean(seg_stats[label][stat_name]) 
  #       for stat_name in stat_names }
  #   for label in threshold_labels }
  
  # ====================
  # = Reports & charts =
  # ====================
  
  mkdir_p(args.outdir)
  
  #
  # Summary stats
  #
  
  for stat_name in stat_names:
    groupstat_report(stats[stat_name], groupcol, threshold_labels,
      args.outdir, 'stats_%s' % stat_name)
      
    groupstat_plot(stats[stat_name], groups, threshold_labels, 
      args.outdir, 'stats_%s' % stat_name,
      xgroups=[threshold_labels])
  
  boxplot_matrix(seg_stats, threshold_labels, stat_names, 
    args.outdir, 'boxplots')

  groupstat_report(cov_seg_stats, 'CoV(x)', threshold_labels,
    args.outdir, 'cov')
  # groupstat_report(cov_seg_stats, 'segment', stat_names,
  #   args.outdir, 'cov')
  
  groupstat_plot(cov_seg_stats, stat_names, threshold_labels, 
    args.outdir, 'cov', 
    xgroups=[threshold_labels])
  # groupstat_plot(cov_seg_stats, threshold_labels, stat_names, 
  #   args.outdir, 'cov')

