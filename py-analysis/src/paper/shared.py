# Some functions shared by several scripts.

from decimal import Decimal
import gc
import math

import matplotlib.pyplot as plt
from matplotlib import ticker
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

# Convert any string objects to UTF-8
def encode(arr):
  return [v.encode('utf-8') if type(v) in [str, unicode] else v for v in arr]

# Export member profiles that are segmented into groups.
# data: a dict: group_id -> list of profile dictionaries
# groupcolname: used in TSV header
# propcolnames: used to iterate over the data, and in TSV header
def profiledata_report(data, groupcolname, propcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(encode([groupcolname] + propcolnames))
  for key in sorted(data.keys()):
    for row in data[key]:
      outcsv.writerow(encode([key] + [row[colname] for colname in propcolnames]))
  outfile.close()

# Export summary statistics for several groups.
# data: a nested dict: group_id -> stat_id -> value
# groupcolname: used in TSV header
# statcolnames: used to iterate over the data, and in TSV header
def groupstat_report(data, groupcolname, statcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(encode([groupcolname] + statcolnames))
  for key in sorted(data.keys()):
    outcsv.writerow(encode([key] + [data[key][colname] for colname in statcolnames]))
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

# data: row -> column -> list of values
# kwargs is passed on to plt.boxplot(...).
def boxplot_matrix(data, rows, columns, outdir, filename_base, min_values=5,
   shared_yscale=True, show_minmax=True, **kwargs):

  for (column, row, ax1) in plot_matrix(columns, rows, shared_yscale=shared_yscale):
    values = data[row][column]
    if len(values) < min_values:
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      ax1.boxplot(values, **kwargs)
      
      if show_minmax:
        w = 0.1
        plt.plot([-w, w], [min(values)]*2, 'k-')
        plt.plot([-w, w], [max(values)]*2, 'k-')

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    # ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data_cols: group -> metric -> value
# data_rows: group -> metric -> value
# groups: list of groups to plot
# row_measures: list of metrics across rows
# col_measures: list of metrics across columns
# outdir:
# filename_base:
# scale:
# colors:
# size: dot size in points^2
# sizemap: a map from group name to a [0..1] size multiplier
#
# kwargs is passed on to plt.scatter(...).
def scatter_matrix(data_rows, data_cols, groups, row_measures, col_measures, 
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
