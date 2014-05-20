#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
from decimal import Decimal

import pandas

from app import *
from shared import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('datafile', help='TSV of user data')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--num-groups', help='The number of groups to analyse (ranked by size)', dest='num_groups', action='store', type=int, default=None)
  args = parser.parse_args()
  
  #
  # Defaults
  #
  
  groupcol = 'country'
  
  measures = ['num_coll_edits', 'num_coll_tag_add', 'num_coll_tag_update', 
    'num_coll_tag_remove']

  to_cohort_name = lambda measure: measure.replace('num_', '', 1)
  cohorts = [to_cohort_name(measure) for measure in measures]

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

  # dict: group -> measure -> list of values
  pop = { 
    group: { 
      measure: [ d[measure] for d in data[group] ] for measure in measures
    } for group in groups
  }
  
  # dict: cohort -> group -> value
  cohort_sizes = {
    group: {
      to_cohort_name(measure): 
        len([v for v in pop[group][measure] if v>0]) for measure in measures
    } for group in groups
  }
  
  #
  # Per segment: compute summary stats
  # 

  # dict: group -> stat -> value
  stats = defaultdict(lambda: defaultdict(dict))
  for group in groups:
    total_users = Decimal(group_stats[group]['pop'])
    total_edits = Decimal(group_stats[group]['edits'])

    values = pop[group]['num_coll_edits']
    stats[group]['%pop'] = len([v for v in values if v>0]) / total_users
    stats[group]['%edits'] = sum(values) / total_edits
    stats[group]['gini'] = gini(values)
    stats[group]['top10%'] = ranked_percentile_share(values, Decimal(10), top=True)
    
    for action in actions:
      values = pop[group]['num_coll_tag_%s' % action]
      stats[group]['%%pop-%s' % action] = len([v for v in values if v>0]) / total_users
      stats[group]['%%edits-%s' % action] = sum(values) / total_edits
      stats[group]['gini-%s' % action] = gini(values)
      stats[group]['top10%%-%s' % action] = ranked_percentile_share(values, Decimal(10), top=True)
  
  # ====================
  # = Reports & charts =
  # ====================
  
  mkdir_p(args.outdir)
  
  pop_names = ['%pop'] + ['%%pop-%s' % action for action in actions]
  edit_names = ['%edits'] + ['%%edits-%s' % action for action in actions]
  stat_names = pop_names + edit_names

  gini_names = ['gini'] + ['gini-%s' % action for action in actions]
  top10pc_names = ['top10%'] + ['top10%%-%s' % action for action in actions]
  ineq_stat_names = gini_names + top10pc_names
  
  #
  # Summary stats
  #

  groupstat_report(cohort_sizes, groupcol, cohorts, 
    args.outdir, 'group_sizes')


  groupstat_report(stats, groupcol, stat_names,
    args.outdir, 'stats')
    
  groupstat_plot(stats, groups, pop_names, 
    args.outdir, 'stats_%pop',
    xgroups=[pop_names])

  groupstat_plot(stats, groups, edit_names, 
    args.outdir, 'stats_%edits',
    xgroups=[edit_names])


  groupstat_report(stats, groupcol, ineq_stat_names,
    args.outdir, 'ineq_stats')

  groupstat_plot(stats, groups, ineq_stat_names, 
    args.outdir, 'ineq_stats',
    xgroups=[ineq_stat_names])

