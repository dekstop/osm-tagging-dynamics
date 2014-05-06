# Some functions shared by several scripts.

from decimal import Decimal
import gc
import math

import numpy as np

from app import *

# =============
# = Filtering =
# =============

# Returns a list of dict keys, ranked in descending order based on a computed 
# summary statistic.
#
# data: an arbitrary dict, e.g. a mapping of { key: [val1, val2, val3] }
# num_keys: the number of keys to return, or None for all
# summarise(data, key): an expression that returns a score for a given key. By 
# default: the number of items stored under this key.
def top_keys(data, num_keys=None, summarise=lambda data,key: len(data[key])):
  keys = sorted(data.keys(), key=lambda _key: summarise(data, _key), reverse=True)
  if num_keys:
    return keys[:num_keys]
  return keys

# ===========
# = Reports =
# ===========

# Export member profiles that are segmented into groups.
# data: a dict: group_id -> list of profile dictionaries
# groupcolname: used in TSV header
# propcolnames: used to iterate over the data, and in TSV header
def profiledata_report(data, groupcolname, propcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([groupcolname] + propcolnames)
  for key in sorted(data.keys()):
    for row in data[key]:
      outcsv.writerow([key] + [row[colname] for colname in propcolnames])
  outfile.close()

# Export summary statistics for several groups.
# data: a nested dict: group_id -> stat_id -> value
# groupcolname: used in TSV header
# statcolnames: used to iterate over the data, and in TSV header
def groupstat_report(data, groupcolname, statcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([groupcolname] + statcolnames)
  for key in sorted(data.keys()):
    outcsv.writerow([key] + [data[key][colname] for colname in statcolnames])
  outfile.close()

# ==========
# = Graphs =
# ==========

# Plots a matrix of floating point variables as horizontal bar charts.
# Axes are auto-scalled within columns, so data can have arbitrary ranges.
# 
# data: group -> measure -> value
# groups: the list of groups to plot, in order (top to bottom)
# measures: the metrics to plot, in order (left to right)
# xgroups: a nested list of measures that share the same horizontal scale.
# kwargs is passed on to plt.barh(...).
def groupstat_plot(data, groups, measures, outdir, filename_base, 
  xgroups=None, colors=QUALITATIVE_MEDIUM, **kwargs):

  for (measure, group, ax1) in plot_matrix(measures, groups, cellwidth=4, 
    cellheight=0.5, shared_xscale=True, xgroups=xgroups,
    hspace=0.05, wspace=0.05):

    if data[group][measure]==None or math.isnan(data[group][measure]):
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      value = data[group][measure]
      ax1.barh(0, value, 1, left=0, 
        color=colors[0], edgecolor='none',
        **kwargs)
      ax1.set_frame_on(False)

    ax1.margins(0.05, 0.05)
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

  # free memory
  plt.close() # closes current figure
  gc.collect()


# TODO: deprecate this, in favour of groupstat_plot
# data: iso2 -> measure -> value
# Plots percentage thresholds, where values in range [0..1]
# kwargs is passed on to plt.bar(...).
def group_share_plot(data, iso2s, measures, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, scale=100, **kwargs):

  for (measure, iso2, ax1) in plot_matrix(measures, iso2s, cellwidth=4, cellheight=0.5):
    if data[iso2][measure] != None:
      colgen = looping_generator(colors)
      value = data[iso2][measure] * scale
      ax1.barh(0, value, 1, left=0, color=next(colgen), **kwargs)
      ax1.barh(0, scale-value, 1, left=value, color=next(colgen), **kwargs)

    ax1.margins(0, 0)
    # ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(to_even_percent))
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])
    
    ax1.patch.set_visible(False)
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

