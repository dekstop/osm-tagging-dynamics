#
# Produce Lorenz plots.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
from decimal import Decimal

import matplotlib.pyplot as plt
import pandas as pd

from app import *

# ==========
# = Graphs =
# ==========

# data: group -> measure -> list of values
# steps: the percentages for which cumulative "income" is computed
# Converts to relative values and draws a Lorenz curve per group and measure.
# kwargs is passed on to plt.fill(...).
def lorenz_plot(data, groups, measures, steps, outdir, filename_base, 
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
# with_gini: compute gini score per group and use as alpha channel
# Converts to relative values and draws a Lorenz curve per group.
# kwargs is passed on to plt.plot(...).
def combined_lorenz_plot(data, groups, measure, steps, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, alpha=0.4, with_gini=False, **kwargs):
  
  fig = plt.figure(figsize=(4, 4))
  fig.patch.set_facecolor('white')
  plt.margins(0.1, 0.1)
  
  colgen = looping_generator(colors)
  color = colgen.next()
  
  for group in groups:
    y = [ranked_percentile_share(data[group][measure], perc) for perc in steps]
    if with_gini:
      g = gini(data[group][measure])
      color = "%.3f" % (1 - g**5)
    plt.plot(steps, y, color=color, alpha=alpha, **kwargs)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Compute long-tail distribution metrics: coefficients, goodness of fit.')
  parser.add_argument('tsvfile', help='Input TSV file. The first column is taken as group identifier, the remaining columns as measures.')
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('--groupcol', help='column name used to group population subsets', dest='groupcol', default=None)
  parser.add_argument('--measures', help='column names of population measures', dest='measures', nargs='*', default=[])
  parser.add_argument('--lorenz-steps', help='Lorenz curve population percentage thresholds', dest='lorenz_steps', nargs='+', action='store', type=Decimal, default=[Decimal(v) for v in range(0,102,2)])
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()

  #
  # Get data
  #
  
  df = pd.read_csv(args.tsvfile, sep="\t")
  groupcol = args.groupcol or df.columns.tolist()[0]
  measures = sorted(args.measures) or sorted(df.columns.tolist())
  if groupcol in measures:
    measures.remove(groupcol) 

  # dict: group -> measure -> list of values
  pop = defaultdict(lambda: defaultdict(list)) 
  groups = set()
  for idx, row in df.iterrows():
    group = row[groupcol]
    groups.add(group)
    for measure in measures:
      pop[group][measure].append(row[measure])

  #
  # Filter according to options, if needed
  #

  if args.num_groups:
    print "Limiting to %d groups (from %d)" % (args.num_groups, len(groups))
    ranked = sorted(groups, key=lambda group: len(pop[group][measures[0]]), reverse=True)
    groups = sorted(ranked[:args.num_groups]) # sort by name
  else:
    groups = sorted(groups) # sort by name

  #
  # Graphs: Lorenz curves
  #
  
  mkdir_p(args.outdir)
  
  lorenz_plot(pop, groups, measures, args.lorenz_steps,
    args.outdir, 'lorenz_matrix')

  for measure in measures:
    combined_lorenz_plot(pop, groups, measure, args.lorenz_steps,
      args.outdir, 'lorenz_%s' % measure)

    combined_lorenz_plot(pop, groups, measure, args.lorenz_steps,
      args.outdir, 'lorenz_%s_gini' % measure,
      alpha=1.0, with_gini=True)
