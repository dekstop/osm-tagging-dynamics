#
# Multiple tagged time series plots.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
import datetime
import dateutil.parser
import decimal
import gc
import os

from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import pandas as pd

from app import *

# =========
# = Tools =
# =========

def datestr2num(d):
  return dateutil.parser.parse(d, default=datetime.datetime(2000, 1, 1, 0, 0, 0, 0))

# =========
# = Plots =
# =========

# data: DataFrame with group -> list of records
# groups: list of groups to plot
# datecol: column name with date values
# measures: list of metrics
# marker_date: a date value, or None
# bar_from_date: a date value, or None
# bar_to_date: a date value, or None
# outdir:
# filename_base:
#
# kwargs is passed on to plt.scatter(...).
def ts_plot(data, groups, datecol, measures, marker_date, bar_from_date, bar_to_date, 
  outdir, filename_base, **kwargs):

  first_date = data[datecol].min()
  last_date = data[datecol].max()

  draw_bar = lambda ax, X, extent: ax.imshow(X, vmin=0, vmax=1, aspect='auto', interpolation='bicubic', cmap=cm.Blues, alpha=0.4, extent=extent)

  has_data = False

  for (measure, group, ax1) in plot_matrix(measures, groups, cellwidth=10, 
    cellheight=2, hspace=0.4, wspace=0.1, shared_xscale=True):

    min_value = min(data.ix[group][measure])
    max_value = max(data.ix[group][measure])
    bar_step = (max_value - min_value) * 0.1
    min_bar_y = max_value + bar_step
    max_bar_y = max_value + 2 * bar_step

    if min_value!=None:

      has_data = True

      #ax1.axvspan(datestr2num(bar_from_date), datestr2num(bar_to_date), color='blue', alpha=0.2)
      if bar_from_date and bar_to_date:
        extent = (datestr2num(bar_from_date), datestr2num(bar_to_date), min_bar_y, max_bar_y)
        draw_bar(ax1, [[1, 1], [1, 1]], extent)
      elif bar_from_date:
        extent = (datestr2num(bar_from_date), datestr2num(last_date), min_bar_y, max_bar_y)
        draw_bar(ax1, [[1, 0], [1, 0]], extent)
      elif bar_to_date:
        extent = (datestr2num(first_date), datestr2num(bar_to_date), min_bar_y, max_bar_y)
        draw_bar(ax1, [[0, 1], [0, 1]], extent)
  
      if marker_date:
        ax1.axvline(datestr2num(marker_date), color=QUALITATIVE_DARK[2])
  
      x = [datestr2num(d) for d in data.ix[group][datecol]]
      y = data.ix[group][measure]
  
      ax1.plot(x, y, color=QUALITATIVE_DARK[1], **kwargs)

    ax1.xaxis_date()
    # ax1.margins(0.2, 0.2)
  
  if has_data:
    plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
    plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')
  else:
    print "No data to plot, skipping."

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
  parser.add_argument('--marker', help='Marker position (a date string), e.g. to highlight events', dest='marker', action='store', type=str, default=None)
  parser.add_argument('--bar-from', help='Start position for a horizontal bar, e.g. to highlight periods', dest='bar_from', action='store', type=str, default=None)
  parser.add_argument('--bar-to', help='End position for a horizontal bar, e.g. to highlight periods', dest='bar_to', action='store', type=str, default=None)
  
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
  if args.marker:
    print "Marker at: %s" % args.marker
  
  #
  # Plots.
  #
  mkdir_p(args.outdir)
  filename_base = os.path.splitext(os.path.basename(args.tsv))[0]
  
  ts_plot(data, groups, datecol, metrics, args.marker, args.bar_from, args.bar_to,
    args.outdir, filename_base)
  
