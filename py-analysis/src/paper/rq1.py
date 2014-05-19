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
  to_cohort_name = lambda measure: measure.replace('num_', '', 1)
  cohorts = [to_cohort_name(measure) for measure in measures]

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
  
  # dict: group -> cohort -> list of values
  pop = { 
    group: { 
      to_cohort_name(measure): [
        d[measure] for d in data[group]
      ] for measure in measures 
    } for group in groups 
  }
  
  #
  # Per group: compute summary stats
  # 

  # dict: cohort -> group -> score -> value
  stats = defaultdict(dict)
  for cohort in cohorts:
    for group in groups:
      values = pop[group][cohort]
      rec = dict()
      rec['pop'] = len([v for v in values if v>0])
      rec['edits'] = sum(values)
      rec['gini'] = gini(values)
      rec['palma'] = palma(values)
      rec['top10%'] = ranked_percentile_share(values, Decimal(10), top=True)
      
      stats[cohort][group] = rec

  #
  # Per group: collab share
  #
  
  # dict: group -> score -> value
  coll_stats = defaultdict(dict)
  for group in groups:
    rec = dict()
    rec['%pop'] = stats['coll_edits'][group]['pop'] / Decimal(stats['edits'][group]['pop'])
    rec['%edits'] = stats['coll_edits'][group]['edits'] / Decimal(stats['edits'][group]['edits'])

    for stat_name in ['gini', 'palma', 'top10%']:
      rec[stat_name] = stats['coll_edits'][group][stat_name]

    coll_stats[group] = rec

  # ====================
  # = Reports & charts =
  # ====================

  mkdir_p(args.outdir)

  #
  # Summary stats: group sizes
  #
  
  # dict: group -> cohort -> value
  cohort_sizes = { group: { cohort: 
        stats[cohort][group]['pop'] 
      for cohort in cohorts } 
    for group in groups }

  groupstat_report(cohort_sizes, groupcol, cohorts, args.outdir, 'cohort_sizes')

  #
  # Summary stats per metric
  #
  
  stat_names = ['pop', 'edits', 'gini', 'palma', 'top10%']

  for cohort in cohorts:
    groupstat_report(stats[cohort], groupcol, stat_names,
      args.outdir, 'cohort_%s' % cohort)

    groupstat_plot(stats[cohort], groups, stat_names, 
      args.outdir, 'cohort_%s' % cohort)

  #
  # Collab stats
  #

  coll_stat_names = ['%pop', '%edits', 'gini', 'palma', 'top10%']

  groupstat_report(coll_stats, groupcol, coll_stat_names,
    args.outdir, 'coll_stats')

  groupstat_plot(coll_stats, groups, coll_stat_names, 
    args.outdir, 'coll_stats')

  #
  # Lorenz curves
  #
  
  lorenz_matrix_plot(pop, groups, cohorts, args.lorenz_steps,
    args.outdir, 'lorenz_matrix')
  
  for cohort in cohorts:
    combined_lorenz_plot(pop, groups, cohort, args.lorenz_steps,
      args.outdir, 'lorenz_%s' % cohort)
