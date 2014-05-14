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
# = Plots =
# =========

# data: column -> row -> list of values
# kwargs is passed on to plt.boxplot(...).
def boxplot_matrix(data, columns, rows, outdir, filename_base, min_values=5,
   shared_yscale=True, show_minmax=True, **kwargs):

  for (column, row, ax1) in plot_matrix(columns, rows, shared_yscale=shared_yscale):
    values = data[column][row]
    if len(values) < min_values:
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      mean = np.mean(values)
      norm_values = [v / mean for v in values]
      ax1.boxplot(norm_values, **kwargs)
      
      if show_minmax:
        w = 0.1
        plt.plot([-w, w], [min(values)]*2, 'k-')
        plt.plot([-w, w], [max(values)]*2, 'k-')

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  parser.add_argument('--num-segments', help='The number of segments per group', dest='num_segments', action='store', type=int, default=4)
  parser.add_argument('--threshold-base', help='The "power of x" base when calculating segment thresholds', dest='threshold_base', action='store', type=int, default=10)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  
  # segmentation: powers of ten
  segments = [args.threshold_base**p for p in range(args.num_segments-1)]
  # segments = [2**p for p in range(5)]
  # segments = [5**p for p in range(4)]
  # segments = [10**p for p in range(4)]
  thresholds = zip([None] + segments, segments + [None])
  threshold_label = lambda n1, n2: \
    '%d<n<=%d' % (n1, n2) if (n1 and n2) else \
    'n>%s' % n1 if (not n2) else \
    'n=%d' % n2
  threshold_labels = [threshold_label(min1, max1) for (min1, max1) in thresholds]

  measures = ['num_coll_edits', 'num_coll_tag_add', 'num_coll_tag_update', 
    'num_coll_tag_remove']
  # to_cohort_name = lambda measure: measure.replace('num_', '', 1)
  # cohorts = [to_cohort_name(measure) for measure in measures]

  actions = ['add', 'update', 'remove']
  
  # ============================
  # = Load data & transform it =
  # ============================

  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(groupcol)
  
  # dict: group -> list of user dicts
  data = defaultdict(list)
  for idx, row in df.iterrows():
    group = row[groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[group].append(rec)

  #
  # Filter according to options, if needed
  #

  groups = top_keys(data, args.num_groups)
  print "Found %d groups" % len(groups)

  # =================
  # = Compute stats =
  # =================

  #
  # Per group: collect population measures
  # 

  # dict: group -> metric -> value
  group_stats = defaultdict(dict)
  for group in groups:
    edits = [d['num_edits'] for d in data[group] if d['num_edits']>0]
    group_stats[group]['pop'] = len(edits)
    group_stats[group]['edits'] = sum(edits)
  
  #
  # Segment users
  # 

  # dict: group -> segment -> measure -> list of values
  pop = { 
    group: { 
      threshold_label(min1, max1): {
        measure: [
          d[measure] for d in data[group]
            if (min1==None or d['num_edits']>min1)
            and (max1==None or d['num_edits']<=max1)
        ] for measure in measures
      } for (min1, max1) in thresholds
    } for group in groups
  }
  
  # dict: measure -> group -> segment -> value
  measure_segment_sizes = {
    measure: {
      group: {
        label: 
          len([v for v in pop[group][label][measure] if v>0])
        for label in threshold_labels
      } for group in groups
    } for measure in measures
  }
  
  #
  # Per segment: compute summary stats
  # 

  # dict: stat -> group -> segment -> value
  stats = defaultdict(lambda: defaultdict(dict))
  for group in groups:
    for label in threshold_labels:
      total_users = Decimal(group_stats[group]['pop'])
      total_edits = Decimal(group_stats[group]['edits'])

      values = pop[group][label]['num_coll_edits']
      stats['%pop'][group][label] = len([v for v in values if v>0]) / total_users
      stats['%edits'][group][label] = sum(values) / total_edits
      
      for action in actions:
        values = pop[group][label]['num_coll_tag_%s' % action]
        stats['%%pop-%s' % action][group][label] = len([v for v in values if v>0]) / total_users
        stats['%%edits-%s' % action][group][label] = sum(values) / total_edits
        

  #
  # Segment variances across groups
  #
  
  stat_names = list()
  for stat_name in ['%pop', '%edits']:
    stat_names.append(stat_name)
    for action in actions:
      stat_names.append('%s-%s' % (stat_name, action))
  
  # dict: segment -> stat -> list of values
  seg_stats = { 
    label: { 
      stat_name: 
        [float(stats[stat_name][group][label]) for group in groups] 
      for stat_name in stat_names 
    } for label in threshold_labels 
  }
  
  # dict: stat -> segment -> value
  cov_seg_stats = { 
    stat_name: { 
      label: 
        np.std(seg_stats[label][stat_name]) / np.mean(seg_stats[label][stat_name]) 
      for label in threshold_labels 
    } for stat_name in stat_names 
  }
  
  # ====================
  # = Reports & charts =
  # ====================
  
  mkdir_p(args.outdir)
  
  #
  # Summary stats
  #
  
  for measure in measures:
    groupstat_report(measure_segment_sizes[measure], groupcol, threshold_labels, 
      args.outdir, 'segment_sizes_%s' % measure)

  for stat_name in stat_names:
    groupstat_report(stats[stat_name], groupcol, threshold_labels,
      args.outdir, 'stats_%s' % stat_name)
      
    groupstat_plot(stats[stat_name], groups, threshold_labels, 
      args.outdir, 'stats_%s' % stat_name,
      xgroups=[threshold_labels])
  
  boxplot_matrix(seg_stats, threshold_labels, stat_names, 
    args.outdir, 'boxplots')

  groupstat_report(cov_seg_stats, 'CoV(x)', threshold_labels,
    args.outdir, 'cov')
  # groupstat_report(cov_seg_stats, 'segment', stat_names,
  #   args.outdir, 'cov')
  
  groupstat_plot(cov_seg_stats, stat_names, threshold_labels, 
    args.outdir, 'cov', 
    xgroups=[threshold_labels])
  # groupstat_plot(cov_seg_stats, threshold_labels, stat_names, 
  #   args.outdir, 'cov')

