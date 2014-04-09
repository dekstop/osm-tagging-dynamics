# Some functions shared by several scripts.

from decimal import Decimal
import numpy as np

from app import *

# ===========
# = Reports =
# ===========

# data: a dict: key -> list of dictionaries
def group_report(data, keycolname, valcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([keycolname] + valcolnames)
  for key in sorted(data.keys()):
    for row in data[key]:
      outcsv.writerow([key] + [row[colname] for colname in valcolnames])
  outfile.close()

# data: a nested dict: key -> dict
def segment_report(data, keycolname, segcolnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([keycolname] + segcolnames)
  for key in sorted(data.keys()):
    outcsv.writerow([key] + [data[key][colname] for colname in segcolnames])
  outfile.close()

# ==========
# = Graphs =
# ==========

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

# ========================
# = Percentile selection =
# ========================

# Maps a percentile value to an overall length.
# Returns None if perc is None.
def get_percentile_index(length, perc):
  if perc==None:
    return None
  return int(length * perc / Decimal(100))

# What is the sum of a percentile segment of entries?
#
# The process:
# - order all values by size (by default: in ascending order)
# - identify the index positions for the given percentages (rounding down)
# - return the sum of values between these positions
#
# values: array of numbers
# from_pc: [0..100], or None
# to_pc: [0..100], or None
# descending: rank in descending order? This can be used to select top percentiles.
# 
# Constraints: 
# - from_pc < to_pc
# - at least one of [from_pc, to_pc] needs to be non-null
def percentile_range_sum(values, from_pc, to_pc, descending=False):
  if from_pc==None and to_pc==None:
    raise Exception("No range was provided: both [from_pc, to_pc] are None")
  if from_pc!=None and to_pc!=None and from_pc>=to_pc:
    raise Exception("Illegal range: from_pc >= to_pc (%s >= %s)" % (from_pc, to_pc))
  values = sorted(values, reverse=descending)
  length = len(values)
  from_idx = get_percentile_index(length, from_pc)
  to_idx = get_percentile_index(length, to_pc)
  return sum(values[from_idx:to_idx])

# What is the share (workload, income, ...) of a percentile segment of entries?
#
# values: array of numbers
# from_pc: [0..100], or None
# to_pc: [0..100], or None
# descending: rank in descending order? 
def percentile_range_share(values, from_pc, to_pc, descending=False):
  return Decimal(percentile_range_sum(values, from_pc, to_pc, descending=descending)) / sum(values)

# What is the sum of the lowest-ranking x% number of entries?
#
# values: array of numbers
# perc: [0..100]
# top: sum of top percentile? (vs bottom percentile)
def ranked_percentile_sum(values, perc, top=False):
  return percentile_range_sum(values, None, perc, descending=top)

# What is the share (workload, income, ...) of the lowest-ranking x% number of entries (contributors)?
#
# values: array of numbers
# perc: [0..100]
# top: share of top percentile? (vs bottom percentile)
def ranked_percentile_share(values, perc, top=False):
  return Decimal(ranked_percentile_sum(values, perc, top=top)) / sum(values)

# ====================
# = Gini coefficient =
# ====================

# From http://planspace.org/2013/06/21/how-to-calculate-gini-coefficient-from-raw-data-in-python/

# values: a list of positive integers
def gini(values):
  sorted_list = sorted(values)
  height, area = 0, 0
  for value in sorted_list:
    height += value
    area += height - value / Decimal(2)
  fair_area = height * len(values) / Decimal(2)
  return (fair_area - area) / fair_area

# ===============
# = Theil index =
# ===============

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
