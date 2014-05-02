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
  parser.add_argument('groupcol', help='column name used to group population subsets')
  parser.add_argument('measures', help='column names of population measures', nargs='+')
  parser.add_argument('--lorenz-steps', help='Lorenz curve population percentage thresholds', dest='lorenz_steps', nargs='+', action='store', type=Decimal, default=[Decimal(v) for v in range(0,102,2)])
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()

  #
  # Get data and transform it
  #
  
  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(args.groupcol)
  
  # dict: group -> list of user dicts
  data = defaultdict(list)
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[group].append(rec)

  #
  # Filter according to options, if needed
  #

  groups = top_keys(data, args.num_groups)
  
  print "Group column: %s" % args.groupcol
  print "Found %d groups" % len(groups)
  print "Computing population statistics for measures: %s" % ", ".join(args.measures)

  #
  # Per group: collect population measures
  # 
  
  # dict: group -> measure -> list of values
  pop = dict()
  for group in groups:
    rec = dict()
    for measure in args.measures:
      rec[measure] = [d[measure] for d in data[group]]
    pop[group] = rec
    
  #
  # Per group: compute inequality scores
  # 

  # dict: measure -> group -> score -> value
  scores = defaultdict(dict)
  for measure in args.measures:
    for group in groups:
      values = [v for v in pop[group][measure] if v>0]
      rec = dict()
      rec['pop'] = len(values)
      rec['total'] = sum(values)
      rec['gini'] = gini(values)
      rec['palma'] = palma(values)
      rec['top_10%'] = ranked_percentile_share(values, Decimal(10), top=True)
      
      scores[measure][group] = rec

  #
  # Inequality measures
  #
  
  mkdir_p(args.outdir)

  score_names = ['pop', 'total', 'gini', 'palma', 'top_10%']

  for measure in args.measures:
    groupstat_report(scores[measure], args.groupcol, score_names,
      args.outdir, 'inequality_scores_%s' % measure)

    groupstat_plot(scores[measure], groups, score_names, 
      args.outdir, 'inequality_scores_%s' % measure)

  #
  # Graphs: Lorenz curves
  #
  
  lorenz_matrix_plot(pop, groups, args.measures, args.lorenz_steps,
    args.outdir, 'lorenz_plots')

  for measure in args.measures:
    combined_lorenz_plot(pop, groups, measure, args.lorenz_steps,
      args.outdir, 'lorenz_plot_combined_%s' % measure)
