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

import matplotlib.dates
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import pandas as pd

from app import *

# =========
# = Tools =
# =========

# Copied from matplotlib.dates
HOURS_PER_DAY = 24.
MINUTES_PER_DAY = 60. * HOURS_PER_DAY
SECONDS_PER_DAY = 60. * MINUTES_PER_DAY
MUSECONDS_PER_DAY = 1e6 * SECONDS_PER_DAY

# Copied from matplotlib.dates._to_ordinalf
def _to_ordinalf(dt):
  """
  Convert :mod:`datetime` to the Gregorian date as UTC float days,
  preserving hours, minutes, seconds and microseconds.  Return value
  is a :func:`float`.
  """

  if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
    delta = dt.tzinfo.utcoffset(dt)
    if delta is not None:
      dt -= delta

  base = float(dt.toordinal())
  if hasattr(dt, 'hour'):
    base += (dt.hour / HOURS_PER_DAY + dt.minute / MINUTES_PER_DAY +
         dt.second / SECONDS_PER_DAY +
         dt.microsecond / MUSECONDS_PER_DAY
         )
  return base

# This replaces matplotlib.dates.datestr2num which until late 2013 didn't have customisable defaults
def datestr2num(d):
  if d==None:
    return None
  return _to_ordinalf(dateutil.parser.parse(d, default=datetime.datetime(2000, 1, 1, 0, 0, 0, 0)))

# http://stackoverflow.com/questions/13515471/matplotlib-how-to-prevent-x-axis-labels-from-overlapping-each-other
def datestr2date(d):
  if d==None:
    return None
  return matplotlib.dates.num2date(datestr2num(d))

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
# default_value: for NULL entries
#
# kwargs is passed on to plt.scatter(...).
def ts_plot(data, groups, datecol, measures, marker_date, bar_from_date, bar_to_date, 
  outdir, filename_base, default_value=None, **kwargs):

  draw_bar = lambda ax, X, extent: ax.imshow(X, vmin=0, vmax=1, aspect='auto', interpolation='bicubic', cmap=cm.Blues, alpha=0.4, extent=extent)
  clamp = lambda n, minn, maxn: n if n==None else max(min(maxn, n), minn)

  first_date = data[datecol].min()
  first_date_f = datestr2num(first_date)
  last_date = data[datecol].max()
  last_date_f = datestr2num(last_date)

  bar_from_date_f = clamp(datestr2num(bar_from_date), first_date_f, last_date_f)
  bar_to_date_f = clamp(datestr2num(bar_to_date), first_date_f, last_date_f)
  marker_date_f = clamp(datestr2num(marker_date), first_date_f, last_date_f)

  has_data = False

  for (measure, group, ax1) in plot_matrix(measures, groups, cellwidth=10, 
    cellheight=2, hspace=0.4, wspace=0.1, shared_xscale=True, xgroups=[measures], 
    autofmt_xdate=False):

    min_value = min(data.ix[group][measure])
    max_value = max(data.ix[group][measure])
    bar_step = (max_value - min_value) * 0.1
    min_bar_y = max_value + bar_step
    max_bar_y = max_value + 2 * bar_step

    if min_value!=None:

      has_data = True

      #ax1.axvspan(datestr2num(bar_from_date), datestr2num(bar_to_date), color='blue', alpha=0.2)
      if bar_from_date_f and bar_to_date_f:
        extent = (bar_from_date_f, bar_to_date_f, min_bar_y, max_bar_y)
        draw_bar(ax1, [[1, 1], [1, 1]], extent)
      elif bar_from_date_f and (bar_from_date_f < last_date_f):
        extent = (bar_from_date_f, last_date_f, min_bar_y, max_bar_y)
        print filename_base, extent[1] - extent[0]
        draw_bar(ax1, [[1, 0], [1, 0]], extent)
      elif bar_to_date_f and (bar_to_date_f > first_date_f):
        extent = (first_date_f, bar_to_date_f, min_bar_y, max_bar_y)
        draw_bar(ax1, [[0, 1], [0, 1]], extent)
  
      if marker_date:
        ax1.axvline(marker_date_f, color=QUALITATIVE_DARK[2])
  
      x = [datestr2num(d) for d in data.ix[group][datecol]]
      #if default_value:
      #  x = [v if v else default_value for v in x]
      y = data.ix[group][measure]
  
      ax1.plot_date(x, y, color=QUALITATIVE_DARK[1], **kwargs)

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
  parser.add_argument('--default-value', help='Default value for NULL entries', dest='default_value', action='store', type=float, default=None)
  
  args = parser.parse_args()

  #
  # Get data
  #
  
  # data = pd.read_table(args.tsv, index_col=0)
  data = pd.DataFrame.from_csv(args.tsv, sep='\t')

  if args.default_value:
    data = data.fillna(args.default_value)

  groups = sorted(set(data.index))
  datecol = data.keys()[0]
  metrics = data.keys()[1:]

  print "Number of groups: %d" % len(groups)
  if args.marker:
    print "Marker at: %s" % args.marker
  if args.bar_from:
    print "Bar starting at: %s" % args.bar_from
  if args.bar_to:
    print "Bar ending at: %s" % args.bar_to

  #
  # Plots.
  #
  mkdir_p(args.outdir)
  filename_base = os.path.splitext(os.path.basename(args.tsv))[0]
  
  ts_plot(data, groups, datecol, metrics, args.marker, args.bar_from, args.bar_to,
    args.outdir, filename_base)
  
  print
  
