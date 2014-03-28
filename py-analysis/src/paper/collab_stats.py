#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import gc
import sys

import pandas

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np

from app import *
from shared import *

# =========
# = Tools =
# =========

# How many of the provided values are required to reach or exceed the given
# percentile threshold?
#
# The process:
# - calculate the total (the sum of all values)
# - order all values by size (by default: in descending order)
# - pick the n largest entries whose sum is at or above the percentile (as percentage of the total)
# - return the number of items in this selected group
#
# values: array of numbers
# perc: [0..100]
def count_cumsum_percentile(values, perc, reverse=True):
  values = sorted(values, reverse=reverse)
  total = sum(values)
  limit = decimal.Decimal(total) * decimal.Decimal(perc / 100.0)
  ax = decimal.Decimal(0)
  for idx in range(len(values)):
    ax += values[idx]
    if ax >= limit:
      return idx + 1
  return len(values)

# From http://planspace.org/2013/06/21/how-to-calculate-gini-coefficient-from-raw-data-in-python/
def gini(list_of_values):
  sorted_list = sorted(list_of_values)
  height, area = 0, 0
  for value in sorted_list:
    height += value
    area += height - value / decimal.Decimal(2)
  fair_area = height * len(list_of_values) / decimal.Decimal(2)
  return (fair_area - area) / fair_area

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
  
# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('groupcol', help='column name used to group population subsets')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--topuser-percentile', help='work percentile threshold for highly engaged users', dest='topuser_percentile', action='store', type=decimal.Decimal, default=80.0)
  args = parser.parse_args()

  #
  # Get data and transform it
  #
  
  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(args.groupcol)
  
  # iso2 -> list of user dicts
  data = defaultdict(list)
  
  for idx, row in df.iterrows():
    iso2 = row[args.groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[iso2].append(rec)

  #
  # Per country: share of collab editors
  # 
  
  # dict: iso2 -> metric -> value
  stats = defaultdict(dict)
  for iso2 in data.keys():
    rec = dict()
    num_users = len(data[iso2])

    edits = [d['num_edits'] for d in data[iso2]]
    tag_adds = [d['num_tag_add'] for d in data[iso2]]
    tag_updates = [d['num_tag_update'] for d in data[iso2]]
    tag_removes = [d['num_tag_remove'] for d in data[iso2]]
    coll_edits = [d['num_coll_edits'] for d in data[iso2]]
    coll_tag_adds = [d['num_coll_tag_add'] for d in data[iso2]]
    coll_tag_updates = [d['num_coll_tag_update'] for d in data[iso2]]
    coll_tag_removes = [d['num_coll_tag_remove'] for d in data[iso2]]
    
    # "population"
    rec['num_users'] = num_users

    rec['num_coll_users'] = len([1 for n in coll_edits if n>0])
    rec['p_coll_users'] = decimal.Decimal(rec['num_coll_users']) / rec['num_users']

    rec['coll_users_gini'] = gini(coll_edits)
    
    sum_coll_edits = sum(coll_edits)
    p_coll_edits = [1.0 * n / sum_coll_edits for n in coll_edits]
    redundancy, inequality = theil(p_coll_edits)
    # rec['coll_users_theil_r'] = redundancy
    rec['coll_users_theil'] = inequality

    # percentage of users who are responsible for X% of edits, collab edits
    rec['num_top_users'] = count_cumsum_percentile(edits, args.topuser_percentile)
    rec['p_top_users'] = decimal.Decimal(rec['num_top_users']) / rec['num_users']
    
    rec['num_top_coll_users'] = count_cumsum_percentile(coll_edits, args.topuser_percentile)
    rec['p_top_coll_users'] = decimal.Decimal(rec['num_top_coll_users']) / rec['num_users']
    
    # volume of collaborative maintenance work
    rec['num_edits'] = sum(edits)
    rec['num_coll_edits'] = sum(coll_edits)
    rec['p_coll_edits'] = decimal.Decimal(sum(coll_edits)) / sum(edits)

    rec['num_coll_tag_add'] = sum(coll_tag_adds)
    rec['p_coll_tag_add'] = decimal.Decimal(sum(coll_tag_adds)) / sum(edits)
    rec['num_coll_tag_update'] = sum(coll_tag_updates)
    rec['p_coll_tag_update'] = decimal.Decimal(sum(coll_tag_updates)) / sum(edits)
    rec['num_coll_tag_remove'] = sum(coll_tag_removes)
    rec['p_coll_tag_remove'] = decimal.Decimal(sum(coll_tag_removes)) / sum(edits)
    
    stats[iso2] = rec
  
  #
  # Report: country profiles
  #
  
  mkdir_p(args.outdir)
  
  country_fields = ['num_users', 
    'num_top_users', 'p_top_users', 

    'num_coll_users', 'p_coll_users',
    'coll_users_gini',
    'coll_users_theil',
    'num_top_coll_users', 'p_top_coll_users', 

    'num_edits',
    'num_coll_edits', 'p_coll_edits',
    'num_coll_tag_add', 'p_coll_tag_add',
    'num_coll_tag_update', 'p_coll_tag_update',
    'num_coll_tag_remove', 'p_coll_tag_remove',
    ]
  segment_report(stats, 'country', country_fields, args.outdir, 'country_profiles')
  
  #
  # Graphs: country profiles
  #
  
  # Countries are ranked by number of users, descending
  iso2s = sorted(stats.keys(), key=lambda iso2: stats[iso2]['num_users'], reverse=True)
  
  group_share_plot(stats, iso2s, 
    ['p_top_users', 
    'p_coll_users', 'p_top_coll_users', 
    'coll_users_gini',
    'coll_users_theil'], 
    args.outdir, 'country_profiles_users')

  group_share_plot(stats, iso2s, 
    ['p_coll_edits', 
    'p_coll_tag_add', 'p_coll_tag_update', 'p_coll_tag_remove'], 
    args.outdir, 'country_profiles_edits')
