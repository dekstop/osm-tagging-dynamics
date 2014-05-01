#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import copy
from decimal import Decimal
import gc
import sys

import pandas

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np

from app import *
from shared import *

# ==========
# = Graphs =
# ==========

# data: group -> measure -> value
# Plots floating point numbers as bar charts.
# Axes are auto-scalled across groups for each measure, so data can have arbitrary ranges.
# kwargs is passed on to plt.barh(...).
def group_plot(data, groups, measures, outdir, filename_base, 
  xgroups=None, colors=QUALITATIVE_MEDIUM, **kwargs):

  for (measure, iso2, ax1) in plot_matrix(measures, groups, cellwidth=3, 
    cellheight=0.5, shared_xscale=True, xgroups=xgroups,
    hspace=0.05, wspace=0.05):

    if data[iso2][measure] == None:
      ax1.set_axis_bgcolor('#eeeeee')
      plt.setp(ax1.spines.values(), color='none')
    else:
      value = data[iso2][measure]
      ax1.barh(0, value, 1, left=0, 
        color=colors[0], edgecolor='none',
        **kwargs)
      ax1.set_frame_on(False)

    ax1.margins(0.05, 0.05)
    # ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(to_even_percent))
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])
    
    # ax1.patch.set_visible(False)
    # ax1.axis('off')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

  # free memory
  plt.close() # closes current figure
  gc.collect()

# data:
# groups:
# col_measures:
# row_measures:
# outdir:
# filename_base:
# scale:
# colors:
# size: dot size in points^2
# sizemap: a map from group name to a [0..1] size multiplier
#
# kwargs is passed on to plt.scatter(...).
def scatter_grid(data, groups, col_measures, row_measures, outdir, filename_base, 
  scale='linear', colors=QUALITATIVE_MEDIUM, size=20, sizemap=None, **kwargs):
  
  for (col, row, ax1) in plot_matrix(col_measures, row_measures):
    x = [data[group][col] for group in groups]
    y = [data[group][row] for group in groups]

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
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('groupcol', help='column name used to group population subsets')
  parser.add_argument('measures', help='column names of population measures', nargs='+')
  parser.add_argument('--only-nonzero', help='only include users with non-zero values for population measures', dest='only_nonzero', type=bool, default=True)
  parser.add_argument('--topuser-percentiles', help='percentile thresholds for highly engaged users', dest='topuser_percentiles', nargs='+', action='store', type=Decimal, default=[Decimal(10), Decimal(1), Decimal('0.1')])
  parser.add_argument('--rop-percentiles', help='percentile thresholds for "ratio of percentiles" scores', dest='rop_percentiles', nargs='+', action='store', type=Decimal, default=[Decimal(10), Decimal(20), Decimal(50), Decimal(80), Decimal(90), Decimal(95)])
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()
  
  # #
  # # Debugging
  # #
  # 
  # # dict: group -> statistic -> score
  # test = {'group%d' % n: {
  #     'score%d' % m: Decimal(n) / 10 * 200 * (m + 1) / Decimal(2) - 50 for m in range(4)
  # } for n in range(10)}
  # 
  # test['group4']['score2'] = None
  # 
  # group_plot(test, sorted(test.keys()), sorted(test['group0'].keys()), 
  #   args.outdir, 'test',
  #   xgroups=['score0', 'score1', ['score2', 'score3']]) 
  # 
  # sys.exit(0)

  #
  # Get data and transform it
  #
  
  df = pandas.read_csv(args.datafile, sep="\t")
  metrics = df.columns.tolist()
  metrics.remove(args.groupcol)
  
  # dict: group -> list of user dicts
  data = defaultdict(list)
  for idx, row in df.iterrows():
    group = row[args.groupcol]
    rec = dict()
    for metric in metrics:
      rec[metric] = row[metric]
    data[group].append(rec)

  #
  # Filter according to options, if needed
  #

  # Groups are ranked by population size, descending
  print "Group column: %s" % args.groupcol
  
  groups = sorted(data.keys(), key=lambda group: len(data[group]), reverse=True)

  if args.num_groups:
    print "Limiting to %d groups (from %d)" % (args.num_groups, len(data.keys()))
    groups = groups[:args.num_groups]
  else:
    print "Found %d groups" % len(data.keys())
  
  print "Computing population statistics for measures: %s" % ", ".join(args.measures)

  #
  # Per group: collect population measures
  # 
  
  # dict: group -> measure -> list of values
  pop = dict()

  for group in groups:
    rec = dict()
    for measure in args.measures:
      rec[measure] = [d[measure] for d in data[group] \
        if (args.only_nonzero==False or \
        d[measure] != 0)]
    pop[group] = rec
  
  #
  # Per group: compute inequality scores
  # 

  # dict: measure -> group -> statistic -> score
  stats = defaultdict(dict)

  for measure in args.measures:
    for group in groups:
      scores = dict()

      # Basics
      values = pop[group][measure]
      scores['pop'] = len(values)
      scores['total'] = sum(values)
      median_ = np.median(values)

      # Gini index
      scores['gini'] = gini(values)
      
      # 20/20 ratio: top 20% vs bottom 20% income
      top_20 = ranked_percentile_sum(values, Decimal(20), top=True)
      bottom_20 = ranked_percentile_sum(values, Decimal(20), top=False)
      if bottom_20==0:
        scores['20_20'] = None
      else:
        scores['20_20'] = Decimal(top_20) / bottom_20

      # Palma ratio: top 10% vs bottom 40% income
      top_10 = ranked_percentile_sum(values, Decimal(10), top=True)
      bottom_40 = ranked_percentile_sum(values, Decimal(40), top=False)
      if bottom_40==0:
        scores['palma'] = None
      else:
        scores['palma'] = Decimal(top_10) / bottom_40
      
      # Top percentiles
      for pc in args.topuser_percentiles:
        scores['top_%s%%' % pc] = \
          ranked_percentile_share(values, pc, top=True)

      # Ratio of percentiles to median
      for pc in args.rop_percentiles:
        if median_==0:
          scores['rop_%s' % pc] = None
        else:
          scores['rop_%s' % pc] = \
            Decimal(ranked_percentile_sum(values, pc, top=False)) / \
            Decimal(median_)

      # Ratio of percentile bands to median
      for (q_from, q_to) in zip(range(4), range(1, 5)):
        if median_==0:
          scores['qom_%d' % q_to] = None
        else:
          from_pc = Decimal(q_from) / 4 * 100
          to_pc = Decimal(q_to) / 4 * 100
          scores['qom_%d' % q_to] = \
            Decimal(percentile_range_sum(values, from_pc, to_pc)) / Decimal(median_)

      # Done
      stats[measure][group] = scores

  # Collect keys for all score types
  basic_scores = ['gini', '20_20', 'palma']
  top_scores = ['top_%s%%' % pc for pc in args.topuser_percentiles]
  rop_scores = ['rop_%s' % pc for pc in args.rop_percentiles]
  qom_scores = ['qom_%d' % q for q in range(1,5)]

  stats_types = ['pop', 'total'] + basic_scores + top_scores + rop_scores + qom_scores
  
  #
  # Graphs and reports: country profiles
  #
  
  mkdir_p(args.outdir)

  for measure in args.measures:

    segment_report(stats[measure], args.groupcol, stats_types, 
      args.outdir, 'stats_%s' % measure) 
    
    # Bar plots
    # group_plot(stats[measure], groups, basic_scores, 
    #   args.outdir, '%s_inequality_1_normalised' % measure)
    # 
    # group_plot(stats[measure], groups, basic_scores, 
    #   args.outdir, '%s_inequality_1' % measure,
    #   xgroups=basic_scores) 
    # 
    # group_plot(stats[measure], groups, top_scores, 
    #   args.outdir, '%s_inequality_2_normalised' % measure)
    # 
    # group_plot(stats[measure], groups, top_scores, 
    #   args.outdir, '%s_inequality_2' % measure,
    #   xgroups=[top_scores]) 
    # 
    # group_plot(stats[measure], groups, rop_scores, 
    #   args.outdir, '%s_inequality_3_normalised' % measure)
    # 
    # group_plot(stats[measure], groups, rop_scores, 
    #   args.outdir, '%s_inequality_3' % measure,
    #   xgroups=[rop_scores]) 
    # 
    # group_plot(stats[measure], groups, qom_scores, 
    #   args.outdir, '%s_inequality_4_normalised' % measure)
    # 
    # group_plot(stats[measure], groups, qom_scores, 
    #   args.outdir, '%s_inequality_4' % measure,
    #   xgroups=[qom_scores]) 

    # Scatter plots
    pop = {group: stats[measure][group]['pop'] for group in groups}
    max_pop = max(pop.values())
    norm = {group: 1.0 * pop[group] / max_pop for group in groups}
    sizemap = {group: norm[group] + 0.2 for group in groups}

    # scatter_grid(stats[measure], groups, 
    #   ['20_20', 'palma', 'top_10%', 'rop_95', 'qom_3'], 
    #   ['pop', 'total', 'gini', 'top_10%', 'rop_95', 'qom_3'], 
    #   args.outdir, '%s_scatter_complements' % measure,
    #   size=100, sizemap=sizemap, alpha=0.8)

    scatter_grid(stats[measure], groups, 
      ['gini', 'palma', 'top_10%'], 
      ['pop', 'total'], 
      args.outdir, '%s_scatter_scale' % measure,
      size=100, sizemap=sizemap, alpha=0.8)

    # scatter_grid(stats[measure], groups, 
    #   top_scores, 
    #   top_scores, 
    #   args.outdir, '%s_scatter_topx' % measure,
    #   size=100, sizemap=sizemap, alpha=0.8)
    # 
    # scatter_grid(stats[measure], groups, 
    #   rop_scores, 
    #   rop_scores, 
    #   args.outdir, '%s_scatter_rop' % measure,
    #   size=100, sizemap=sizemap, alpha=0.8)
    # 
    # scatter_grid(stats[measure], groups, 
    #   qom_scores, 
    #   qom_scores, 
    #   args.outdir, '%s_scatter_qom' % measure,
    #   size=100, sizemap=sizemap, alpha=0.8)
    # 
    # scatter_grid(stats[measure], groups, 
    #   top_scores, 
    #   rop_scores, 
    #   args.outdir, '%s_scatter_top_rop' % measure,
    #   size=100, sizemap=sizemap, alpha=0.8)
    #   