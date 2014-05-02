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

# ==========
# = Graphs =
# ==========

# data: group -> measure -> list of values
# steps: the percentages for which cumulative "income" is computed
# Converts to relative values and draws a Lorenz curve per group and measure.
# kwargs is passed on to plt.fill(...).
def lorenz_matrix_plot(data, groups, measures, steps, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):
  
  for (measure, group, ax1) in plot_matrix(measures, groups, cellwidth=4, cellheight=4):
    colgen = looping_generator(colors)
    y = [ranked_percentile_share(data[group][measure], perc) for perc in steps]
    ax1.fill(steps, y, color=colgen.next(), **kwargs)

    ax1.margins(0.1, 0.1)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: group -> measure -> list of values
# steps: the percentages for which cumulative "income" is computed
# Converts to relative values and draws a Lorenz curve per group.
# kwargs is passed on to plt.plot(...).
def combined_lorenz_plot(data, groups, measure, steps, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, alpha=0.4, **kwargs):
  
  fig = plt.figure(figsize=(4, 4))
  fig.patch.set_facecolor('white')
  plt.margins(0.1, 0.1)
  
  colgen = looping_generator(colors)
  color = colgen.next()
  
  for group in groups:
    y = [ranked_percentile_share(data[group][measure], perc) for perc in steps]
    plt.plot(steps, y, color=color, alpha=alpha, **kwargs)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--lorenz-steps', help='Lorenz curve population percentage thresholds', dest='lorenz_steps', nargs='+', action='store', type=Decimal, default=[Decimal(v) for v in range(0,102,2)])
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  measures = ['num_edits', 'num_coll_edits']
  
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
  print "Computing population statistics for measures: %s" % ", ".join(measures)

  # =================
  # = Compute stats =
  # =================

  #
  # Per group: collect population measures
  # 
  
  # dict: group -> measure -> list of values
  pop = dict()
  for group in groups:
    rec = dict()
    for measure in measures:
      rec[measure] = [d[measure] for d in data[group]]
    pop[group] = rec
    
  #
  # Per group: compute summary stats
  # 

  # dict: measure -> group -> score -> value
  stats = defaultdict(dict)
  for measure in measures:
    for group in groups:
      values = [v for v in pop[group][measure] if v>0]
      rec = dict()
      rec['pop'] = len(values)
      rec['total'] = sum(values)
      rec['gini'] = gini(values)
      rec['palma'] = palma(values)
      rec['top_10%'] = ranked_percentile_share(values, Decimal(10), top=True)
      
      stats[measure][group] = rec

  #
  # Per group: collab share
  #
  
  # dict: group -> score -> value
  coll_stats = defaultdict(dict)
  for group in groups:
    rec = dict()
    rec['coll_user_share'] = stats['num_coll_edits'][group]['pop'] / Decimal(stats['num_edits'][group]['pop'])
    rec['coll_edit_share'] = stats['num_coll_edits'][group]['total'] / Decimal(stats['num_edits'][group]['total'])
    
    coll_stats[group] = rec

  # ====================
  # = Reports & charts =
  # ====================

  mkdir_p(args.outdir)

  #
  # Summary stats
  #
  
  stat_names = ['pop', 'total', 'gini', 'palma', 'top_10%']

  for measure in measures:
    groupstat_report(stats[measure], groupcol, stat_names,
      args.outdir, 'stats_%s' % measure)

    groupstat_plot(stats[measure], groups, stat_names, 
      args.outdir, 'stats_%s' % measure)

  #
  # Collab stats
  #

  coll_stat_names = ['coll_user_share', 'coll_edit_share']

  groupstat_report(coll_stats, groupcol, coll_stat_names,
    args.outdir, 'coll_stats')

  groupstat_plot(coll_stats, groups, coll_stat_names, 
    args.outdir, 'coll_stats')

  #
  # Lorenz curves
  #
  
  lorenz_matrix_plot(pop, groups, measures, args.lorenz_steps,
    args.outdir, 'lorenz_matrix')

  for measure in measures:
    combined_lorenz_plot(pop, groups, measure, args.lorenz_steps,
      args.outdir, 'lorenz_%s' % measure)
