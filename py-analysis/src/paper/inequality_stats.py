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
# = Tools =
# =========

# What is the sum of the highest-ranking x% number of entries?
#
# The process:
# - count the number of items
# - order all values by size (by default: in descending order)
# - identify the index position which is at the given percentage (rounding down)
# - return the sum of these values
#
# values: array of numbers
# perc: [0..100]
def ranked_percentile_sum(values, perc, reverse=True):
  values = sorted(values, reverse=reverse)
  limit = int(len(values) * perc / Decimal(100))
  return sum(values[limit:])

# What is the share (workload, income, ...) of the lowest-ranking x% number of entries (contributors)?
#
# The process:
# - count the number of items
# - order all values by size (by default: in ascending order)
# - identify the index position which is at the given percentage (rounding down)
# - calculate the sum of these values
# - calculate its percentage of the overall total
#
# values: array of numbers
# perc: [0..100]
def ranked_percentile_share(values, perc, reverse=False):
  values = sorted(values, reverse=reverse)
  limit = int(len(values) * perc / Decimal(100))
  return Decimal(sum(values[:limit])) / sum(values) * 100

# From http://stackoverflow.com/questions/20279458/implementation-of-theil-inequality-index-in-python

def error_if_not_in_range01(value):
  if (value < 0) or (value > 1):
    raise Exception, str(value) + ' is not in [0,1]!'

def Group_negentropy(x_i):
  if x_i == 0:
    return 0.0
  else:
    return x_i * np.log(x_i)

def H(x):
  n = len(x)
  entropy = 0.0
  sum = 0.0
  for x_i in x: # work on all x[i]
    # print x_i
    error_if_not_in_range01(x_i)
    sum += x_i
    group_negentropy = Group_negentropy(x_i)
    entropy += group_negentropy
  # error_if_not_1(sum)
  return -entropy

# x is a list of percentages in the range [0,1]
# NOTE: sum(x) must be 1.0
def theil(x):
  # print x
  n = len(x)
  maximum_entropy = np.log(n)
  actual_entropy = H(x)
  redundancy = maximum_entropy - actual_entropy
  inequality = 1 - np.exp(-redundancy)
  return redundancy,inequality

# ==========
# = Graphs =
# ==========

# data: iso2 -> measure -> threshold -> value
# Plots percentage thresholds, where values in range [0..1]
# kwargs is passed on to plt.bar(...).
def threshold_plot(data, iso2s, measures, thresholds, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, scale=100, **kwargs):
  
  cells = [(ax, bx) for ax in measures for bx in thresholds]
  
  for (cell, iso2, ax1) in plot_matrix(cells, iso2s, cellwidth=4, cellheight=0.5):
    measure, threshold = cell
    
    colgen = looping_generator(colors)
    value = data[iso2][measure][threshold] * scale
    ax1.barh(0, value, 1, left=0, color=next(colgen), **kwargs)
    ax1.barh(0, scale-value, 1, left=value, color=next(colgen), **kwargs)

    ax1.margins(0, 0)
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])
    
    ax1.patch.set_visible(False)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: iso2 -> measure -> list of values
# steps: the percentages for which cumulative "income" is computed
# Converts to relative values and draws a Lorenz curve per iso2 and measure.
# kwargs is passed on to plt.fill(...).
def lorenz_plot(data, iso2s, measures, steps, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):
  
  for (measure, iso2, ax1) in plot_matrix(measures, iso2s, cellwidth=4, cellheight=4):
    colgen = looping_generator(colors)
    y = [ranked_percentile_share(data[iso2][measure], perc) for perc in steps]
    ax1.fill(steps, y, color=colgen.next(), **kwargs)

    ax1.margins(0.1, 0.1)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: iso2 -> measure -> list of values
# steps: the percentages for which cumulative "income" is computed
# Converts to relative values and draws a Lorenz curve per iso2.
# kwargs is passed on to plt.plot(...).
def combined_lorenz_plot(data, iso2s, measure, steps, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, alpha=0.4, **kwargs):
  
  fig = plt.figure(figsize=(4, 4))
  fig.patch.set_facecolor('white')
  plt.margins(0.1, 0.1)
  
  colgen = looping_generator(colors)
  color = colgen.next()
  
  for iso2 in iso2s:
    y = [ranked_percentile_share(data[iso2][measure], perc) for perc in steps]
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
  parser.add_argument('--topuser-percentiles', help='work percentile threshold for highly engaged users', dest='topuser_percentiles', nargs='+', action='store', type=Decimal, default=[Decimal(10), Decimal(1), Decimal('0.1')])
  parser.add_argument('--lorenz-steps', help='Lorenz curve population percentage thresholds', dest='lorenz_steps', nargs='+', action='store', type=Decimal, default=[Decimal(v) for v in range(0,102,2)])
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()

  #
  # Get data and transform it
  #
  
  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(args.groupcol)
  
  # group -> list of user dicts
  data = defaultdict(list)
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[group].append(rec)

  # Groups are ranked by population size, descending
  groups = sorted(data.keys(), key=lambda group: len(data[group]), reverse=True)

  if args.num_groups:
    print "Limiting to %d groups (from %d)" % (args.num_groups, len(data.keys()))
    groups = groups[:args.num_groups]

  #
  # Per country: Lorenz curves
  # 
  
  # dict: iso2 -> metric -> list of values
  pop = dict()
  for group in groups:
    rec = dict()
    for measure in ['num_edits', 'num_coll_edits']:
      rec[measure] = [d[measure] for d in data[group]]
    pop[group] = rec
  
  #
  # Per country: impact of highly engaged editors
  # 
  
  # dict: iso2 -> metric -> value
  stats = defaultdict(dict)
  for group in groups:
    rec = dict()

    # "population"
    rec['num_users'] = len(data[group])

    # "work"
    edits = [d['num_edits'] for d in data[group]]
    coll_edits = [d['num_coll_edits'] for d in data[group]]
    # coll_tag_adds = [d['num_coll_tag_add'] for d in data[group]]
    # coll_tag_updates = [d['num_coll_tag_update'] for d in data[group]]
    # coll_tag_removes = [d['num_coll_tag_remove'] for d in data[group]]

    # # "population inequality"
    # norm_edits = edits / linalg.norm(edits)
    # redundancy, inequality = theil(norm_edits)
    # # rec['edits_theil_r'] = redundancy
    # rec['edits_theil'] = inequality
    # 
    # norm_coll_edits = coll_edits / linalg.norm(coll_edits)
    # redundancy, inequality = theil(norm_coll_edits)
    # rec['coll_edits_theil'] = inequality

    # percentage of edits/collab edits made by X% of users
    rec['top_users'] = dict()
    rec['top_coll_users'] = dict()
    for pc in args.topuser_percentiles:
      rec['top_users'][pc] = Decimal(ranked_percentile_sum(edits, pc)) / rec['num_users']
      rec['top_coll_users'][pc] = Decimal(ranked_percentile_sum(coll_edits, pc)) / rec['num_users']
    
    stats[group] = rec
  
  #
  # Graphs: country profiles
  #
  
  mkdir_p(args.outdir)

  lorenz_plot(pop, groups, ['num_edits', 'num_coll_edits'], args.lorenz_steps,
    args.outdir, 'lorenz_plots')
  combined_lorenz_plot(pop, groups, 'num_edits', args.lorenz_steps,
    args.outdir, 'lorenz_plot_combined_num_edits')
  combined_lorenz_plot(pop, groups, 'num_coll_edits', args.lorenz_steps,
    args.outdir, 'lorenz_plot_combined_num_coll_edits')

  threshold_plot(stats, groups, 
    ['top_users', 'top_coll_users'], args.topuser_percentiles,
    args.outdir, 'inequality_users')
