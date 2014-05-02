#
# Compare two populations (pre- and post-filter), compute a report on the differences.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import gc
import sys

import csv
import pandas

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np

from app import *
from shared import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Compare two populations (pre- and post-filter).')
  parser.add_argument('pre_data', help='TSV of user data before filtering')
  parser.add_argument('post_data', help='TSV of user data after filtering')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('groupcol', help='column name used to group population subsets')
  parser.add_argument('metrics', nargs='+', help='column names for aggregate statistics per segment')
  args = parser.parse_args()

  #
  # Read and process data
  #
  
  pre_data = pandas.read_csv(args.pre_data, sep="\t")
  pre_data = pre_data[[args.groupcol] + args.metrics]
  pre_groups = pre_data.groupby(args.groupcol)
  pre_len = pre_groups[args.groupcol].count()
  pre_stats = pre_groups.sum()

  post_data = pandas.read_csv(args.post_data, sep="\t")
  post_data = post_data[[args.groupcol] + args.metrics]
  post_groups = post_data.groupby(args.groupcol)
  post_len = post_groups[args.groupcol].count()
  post_stats = post_groups.sum()

  # group -> metric -> value
  stats = defaultdict(dict)

  for group in pre_data[args.groupcol].unique():
    rec = dict()
  
    rec['pop_pre'] = pre_len[group]
    rec['pop_post'] = post_len[group]
    rec['p_pop_removed'] = 1 - 1.0 * post_len[group] / pre_len[group]
  
    for metric in args.metrics:
      rec['%s_pre' % metric] = pre_stats.ix[group][metric]
      rec['%s_post' % metric] = post_stats.ix[group][metric]
      rec['p_%s_removed' % metric] = 1 - 1.0 * post_stats.ix[group][metric] / pre_stats.ix[group][metric]
  
    stats[group] = rec
  
  #
  # Report
  #
  
  mkdir_p(args.outdir)
  
  report_measures = ['pop_pre', 'pop_post', 'p_pop_removed']
  graph_measures = ['p_pop_removed']
  for metric in args.metrics:
    report_measures.append('%s_pre' % metric)
    report_measures.append('%s_post' % metric)
    report_measures.append('p_%s_removed' % metric)
    graph_measures.append('p_%s_removed' % metric)

  groupstat_report(stats, args.groupcol, report_measures,
    args.outdir, 'bulkimport_filter_stats')
  
  # Groups are ranked by population size, descending
  groups = sorted(pre_len.keys(), key=lambda group: pre_len[group], reverse=True)

  group_share_plot(stats, groups, graph_measures, 
    args.outdir, 'bulkimport_filter_stats',
    colors=['#E8AFB8', '#EEEEEE'])
