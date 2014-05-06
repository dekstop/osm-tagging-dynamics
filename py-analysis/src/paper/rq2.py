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

# data: row -> column -> list of values
# kwargs is passed on to plt.boxplot(...).
def boxplot_matrix(data, columns, rows, outdir, filename_base, min_values=5, **kwargs):
  for (column, row, ax1) in plot_matrix(columns, rows):
    if len(data[row][column]) < min_values:
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      values = data[row][column]
      mean = np.mean(data[row][column])
      norm_values = [v / mean for v in values]
      ax1.boxplot(norm_values, **kwargs)

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
  segments = [args.threshold_base**p for p in range(args.num_segments)]
  # segments = [2**p for p in range(5)]
  # segments = [5**p for p in range(4)]
  # segments = [10**p for p in range(4)]
  thresholds = zip(segments, segments[1:] + [None])
  threshold_label = lambda n1, n2: \
    '%d<=num_coll_edits<%d' % (n1, n2) if n2 else \
    '%d<=num_coll_edits' % n1
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
    pop[group]['coll_edits'] = [d['num_coll_edits'] for d in data[group] if d['num_coll_edits']>0]
    pop[group]['coll_pop'] = len(pop[group]['coll_edits'])
  
  # dict: group -> segment -> list of values
  coll_seg = defaultdict(dict)
  for group in groups:
    for (min1, max1) in thresholds:
      coll_seg[group][threshold_label(min1, max1)] = \
        [v for v in pop[group]['coll_edits'] 
          if v>=min1 
          and (max1==None or v<max1)]
  
  #
  # Per group: compute summary stats
  # 

  # dict: stat -> group -> segment -> value
  stats = defaultdict(lambda: defaultdict(dict))
  for group in groups:
    for label in threshold_labels:
      values = coll_seg[group][label]
      seg_num_users = len(values)
      stats['#users'][group][label] = seg_num_users
      stats['%coll_pop'][group][label] = seg_num_users / Decimal(pop[group]['coll_pop'])
      stats['%pop'][group][label] = seg_num_users / Decimal(pop[group]['pop'])
      stats['cov_coll_edits'][group][label] = np.std(values) / np.mean(values)

  # ====================
  # = Reports & charts =
  # ====================
  
  mkdir_p(args.outdir)
  
  #
  # Summary stats
  #
  
  stat_names = ['#users', '%coll_pop', '%pop', 'cov_coll_edits']
  
  for stat_name in stat_names:
    groupstat_report(stats[stat_name], groupcol, threshold_labels,
      args.outdir, 'stats_%s' % stat_name)
  
    groupstat_plot(stats[stat_name], groups, threshold_labels, 
      args.outdir, 'stats_%s' % stat_name,
      xgroups=[threshold_labels])
  
  boxplot_matrix(coll_seg, threshold_labels, groups, 
    args.outdir, 'boxplot_coll_edits')
