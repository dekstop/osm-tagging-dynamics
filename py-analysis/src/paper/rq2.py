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

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  
  # segmentation: powers of ten
  segments = [10**p for p in range(4)]
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
      seg_num_users = len(coll_seg[group][label])
      stats['#users'][group][label] = seg_num_users
      stats['%coll_pop'][group][label] = seg_num_users / Decimal(pop[group]['coll_pop'])
      stats['%pop'][group][label] = seg_num_users / Decimal(pop[group]['pop'])

  # ====================
  # = Reports & charts =
  # ====================
  
  mkdir_p(args.outdir)
  
  #
  # Summary stats
  #
  
  stat_names = ['#users', '%coll_pop', '%pop']
  
  for stat_name in stat_names:
    groupstat_report(stats[stat_name], groupcol, threshold_labels,
      args.outdir, 'stats_%s' % stat_name)
  
    groupstat_plot(stats[stat_name], groups, threshold_labels, 
      args.outdir, 'stats_%s' % stat_name,
      xgroups=[threshold_labels])
  
  # #
  # # Collab stats
  # #
  # 
  # coll_stat_names = ['coll_user_share', 'coll_edit_share']
  # 
  # groupstat_report(coll_stats, groupcol, coll_stat_names,
  #   args.outdir, 'coll_stats')
  # 
  # groupstat_plot(coll_stats, groups, coll_stat_names, 
  #   args.outdir, 'coll_stats')
  # 
  # #
  # # Lorenz curves
  # #
  # 
  # lorenz_matrix_plot(pop, groups, measures, args.lorenz_steps,
  #   args.outdir, 'lorenz_matrix')
  # 
  # for measure in measures:
  #   combined_lorenz_plot(pop, groups, measure, args.lorenz_steps,
  #     args.outdir, 'lorenz_%s' % measure)
