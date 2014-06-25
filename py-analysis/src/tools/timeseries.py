#
# Multiple tagged time series plots.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
import decimal
import gc
import os

from matplotlib.dates import datestr2num
import matplotlib.pyplot as plt
import pandas as pd

from app import *

# =========
# = Plots =
# =========

# data: DataFrame with group -> list of records
# groups: list of groups to plot
# datecol: column name with date values
# measures: list of metrics
# outdir:
# filename_base:
#
# kwargs is passed on to plt.scatter(...).
def ts_plot(data, groups, datecol, measures, outdir, filename_base,
  **kwargs):
  
  for (measure, group, ax1) in plot_matrix(measures, groups, cellwidth=10, 
    cellheight=2, hspace=0.4, wspace=0.1, shared_xscale=True):

    x = [datestr2num(d) for d in data.ix[group][datecol]]
    y = data.ix[group][measure]

    ax1.plot(x, y, **kwargs)

    ax1.xaxis_date()
    # ax1.margins(0.2, 0.2)
    # ax1.set_xscale(scale)
    # ax1.set_yscale(scale)
    # ax1.get_xaxis().set_ticks([])
    # ax1.get_yaxis().set_ticks([])
  
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
    description='Time series plots across multiple streams.')
  parser.add_argument('tsv', help='Input TSV file. The first column is taken as group identifier, the second as date column, the remaining columns as measures.')
  parser.add_argument('outdir', help='Directory for output files')
  
  args = parser.parse_args()

  #
  # Get data
  #
  
  # data = pd.read_table(args.tsv, index_col=0)
  data = pd.DataFrame.from_csv(args.tsv, sep='\t')

  groups = sorted(set(data.index))
  datecol = data.keys()[0]
  metrics = data.keys()[1:]

  print "Number of groups: %d" % len(groups)
  
  #
  # Plots.
  #
  mkdir_p(args.outdir)
  filename_base = os.path.splitext(os.path.basename(args.tsv))[0]
  
  ts_plot(data, groups, datecol, metrics, 
    args.outdir, filename_base)
  