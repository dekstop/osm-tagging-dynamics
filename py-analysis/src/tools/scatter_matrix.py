#
# Scatter plots between pairs of metrics.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import gc
import sys

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
import pandas as pd
import scipy.stats.stats as stats

from app import *

# =========
# = Plots =
# =========

# data_cols: group -> metric -> value
# data_rows: group -> metric -> value
# groups: list of groups to plot
# col_measures: list of metrics across columns
# row_measures: list of metrics across rows
# outdir:
# filename_base:
# scale:
# colors:
# size: dot size in points^2
# sizemap: a map from group name to a [0..1] size multiplier
#
# kwargs is passed on to plt.scatter(...).
def scatter_grid(data_cols, data_rows, groups, col_measures, row_measures, 
  outdir, filename_base,  scale='linear', colors=QUALITATIVE_MEDIUM, size=20, 
  sizemap=None, **kwargs):
  
  for (col, row, ax1) in plot_matrix(col_measures, row_measures):
    x = [data_cols[group][col] for group in groups]
    y = [data_rows[group][row] for group in groups]

    s = size
    if sizemap!=None:
      s = [sizemap[group] * size for group in groups]

    ax1.scatter(x, y, s=s, edgecolors='none', color=colors[0], **kwargs)

    # # Workaround: won't autoscale for very small values
    # ax1.set_xlim(min(x), max(x))
    # ax1.set_ylim(min(y), max(y))

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
  parser = argparse.ArgumentParser(
    description='Correlation matrix of two different sets of metrics of the same named items.')
  parser.add_argument('tsv_a', help='Input TSV file. The first column is taken as group identifier, the remaining columns as measures.')
  parser.add_argument('tsv_b', help='A second (optional) input TSV file to compare against.', nargs='?', default=None)
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('--scalecol', help='For bubble plots: column name in tsv_a to use as a scale factor', dest='scalecol', action='store', type=str, default=None)
  parser.add_argument('--scale', help='Scale factor for points/bubbles', dest='scale', action='store', type=float, default=1.0)
  
  args = parser.parse_args()

  #
  # Get data
  #
  
  # data_a = pd.DataFrame.from_csv(args.tsv_a, sep='\t')
  data_a = pd.read_table(args.tsv_a, index_col=0)
  if args.tsv_b:
    data_b = pd.read_table(args.tsv_b, index_col=0)
    self_corr = False
  else:
    data_b = data_a
    self_corr = True
  
  groups_a = data_a.index
  groups_b = data_b.index
  groups = sorted([g for g in groups_a if g in groups_b])
  print "Number of samples: %d" % len(groups)
  
  metrics_a = data_a.keys()
  metrics_b = data_b.keys()
  
  #
  # Report and correlation matrix plots.
  #
  mkdir_p(args.outdir)
  
  # Scatter plots
  if args.scalecol:
    pop = {group: data_a.ix[group][args.scalecol] for group in groups}
    max_pop = max(pop.values())
    norm = {group: 1.0 * pop[group] / max_pop for group in groups}
    sizemap = {group: args.scale * norm[group] + 0.2 for group in groups}
  else:
    sizemap = defaultdict(lambda: args.scale)

  scatter_grid(data_a.ix, data_b.ix, groups, metrics_a, metrics_b, 
    args.outdir, 'scatter_matrix',
    size=100, sizemap=sizemap, alpha=0.8)
  