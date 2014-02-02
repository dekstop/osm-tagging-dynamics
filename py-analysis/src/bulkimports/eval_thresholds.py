#
# Evaluate the suitability of various engagement thresholds for automated bulk import detection.
# 

from __future__ import division # non-truncating division in Python 2.x

import argparse
from collections import defaultdict
import decimal
import locale
import random
import sys

import numpy as np

from app import *

# ===========
# = Reports =
# ===========

def encode(obj):
  if isinstance(obj, basestring):
    return obj.encode('utf-8')
  return obj

# data: a list of dictionaries
def eval_report(data, colnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(colnames)
  for row in data:
    outcsv.writerow([encode(row[colname]) for colname in colnames])
  outfile.close()

# ======
# = DB =
# ======

# Global only for now.
# stats_table: table with user edit stats
# abs_threshold: min. number of edits
# countries: list of iso2 country codes
# Returns a set of uids
def get_uids_above_abs_threshold(session, stats_table, abs_threshold, countries=None):
  country_filter = ''
  if countries:
    country_filter = "WHERE w.iso2 IN ('%s')" % ("', '".join(countries))
  result = session.execute("""SELECT uid 
    FROM %s ue 
    JOIN world_borders w ON (w.gid=ue.country_gid)
    %s
    GROUP BY uid
    HAVING sum(num_edits)>=%d""" % (stats_table, country_filter, abs_threshold))
  uids = set()
  for row in result:
    uids.add(row['uid'])
  return uids
  
# Global only for now.
# stats_table: table with user edit stats
# percentile: [0..100] inclusive
# countries: list of iso2 country codes
# Returns an absolute threshold
def get_threshold_for_percentile(session, stats_table, percentile, countries=None):
  country_filter = ''
  if countries:
    country_filter = "WHERE w.iso2 IN ('%s')" % ("', '".join(countries))
  result = session.execute("""SELECT num_edits 
    FROM %s ue
    JOIN world_borders w ON (w.gid=ue.country_gid)
    %s
    ORDER BY num_edits ASC""" % (stats_table, country_filter))
  ranking = []
  for row in result:
    ranking.append(row['num_edits'])
  return round(np.percentile(ranking, percentile))
  
# =========
# = Tools =
# =========

def f_score(precision, recall, beta=1):
  return (1 + beta*beta) * (precision*recall) / (beta*beta*precision + recall)

def eval_summary(cohort, filter_type, filter_param, abs_threshold, relevant, retrieved):
  rec = defaultdict(lambda: None)
  rec['cohort'] = cohort
  rec['filter_type'] = filter_type
  rec['filter_param'] = filter_param
  rec['abs_threshold'] = abs_threshold
  rec['num_relevant'] = len(relevant)
  rec['num_retrieved'] = len(retrieved)
  rec['num_relevant_retrieved'] = len(relevant.intersection(retrieved))
  if rec['num_relevant_retrieved']>0:
    rec['precision'] = float(rec['num_relevant_retrieved']) / rec['num_retrieved']
    rec['recall'] = float(rec['num_relevant_retrieved']) / rec['num_relevant']
    rec['F'] = f_score(rec['precision'], rec['recall'], 2)
  return rec

def abs_eval_summary(cohort, threshold, labelled_uids, session, stats_table, countries=None):
  relevant = labelled_uids['bulkimport'] # .union(labelled_uids['unknown'])
  retrieved = get_uids_above_abs_threshold(session, stats_table, threshold, countries)
  retrieved.discard(labelled_uids['unknown'])

  return eval_summary(cohort, 
    'absolute', threshold, threshold, 
    relevant, retrieved)

def rel_eval_summary(cohort, percentile, labelled_uids, session, stats_table, countries=None):
  relevant = labelled_uids['bulkimport'] # .union(labelled_uids['unknown'])
  threshold = get_threshold_for_percentile(session, stats_table, percentile, countries)
  retrieved = get_uids_above_abs_threshold(session, stats_table, threshold, countries)
  retrieved.discard(labelled_uids['unknown'])
  
  return eval_summary(cohort, 
    'relative', percentile, threshold, 
    relevant, retrieved)

# =========
# = Plots =
# =========  

# x_labels: used for x-axis labels
# metrics: metric_name -> list of measures, with same size as x_labels
# kwargs is passed on to plt.scatter(...).
def eval_plot(x_labels, measures, metric_names, outdir, filename_base, 
  colors=QUALITATIVE_DARK, max_labels=20, legend_loc='upper right', **kwargs):
  
  fig = plt.figure(figsize=(4, 3))
  fig.patch.set_facecolor('white')
  
  # x-axis labels
  if len(x_labels) < max_labels:
    x = range(len(x_labels))
    plt.xticks(x, x_labels)
  else:
    x = [int(v*len(x_labels)/max_labels) for v in range(len(x_labels))]
    # skip = int(len(x_labels) / max_labels) + 1
    # x = range(0, max_labels, skip)
    labels = [x_labels[x1] for x1 in x if x1<len(x_labels)]
    while len(labels) < len(x_labels):
      labels.append('')
    plt.xticks(x, labels)
  
  # plot
  colgen = looping_generator(colors)
  for metric_name in metric_names:
    y = measures[metric_name]
    plt.plot(range(len(x_labels)), y, label=metric_name, color=next(colgen), **kwargs)

  plt.legend(loc=legend_loc, prop={'size':'xx-small'})
    # , bbox_to_anchor=(1, 0.5), 
  
  # rotate labels
  locs, labels = plt.xticks()
  plt.setp(labels, rotation=90)

  plt.margins(0.1, 0.1)
  plt.tick_params(axis='both', which='major', labelsize='xx-small')
  # plt.tick_params(axis='both', which='minor', labelsize='xx-small')

  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# stats: ordered list of eval_summary(...) results
# xlabel_formatter: function for x-axis label format
# metric_names: list of metrics to plot from stats entries
def make_eval_plot(stats, xlabel_formatter, metric_names, outdir, filename_base, 
  colors=QUALITATIVE_DARK, legend_loc='upper right'):

  if 2 > len([True for s in stats if s['num_relevant_retrieved']>1]):
    print "Skipping plot %s: not enough data" % filename_base
    return
    
  xlabels = [xlabel_formatter(s['filter_param']) for s in stats]
  measures = defaultdict(list)
  for s in stats:
    for metric in metric_names:
      measures[metric].append(s[metric])

  eval_plot(xlabels, measures, metric_names, outdir, filename_base, 
    colors=colors, legend_loc=legend_loc)
  

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Evaluate the suitability of various engagement thresholds for automated bulk import detection.')
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('--stats-table', help='Name of DB table with user edit stats', 
    dest='stats_table', action='store', type=str, default='user_edit_stats')
  parser.add_argument('--countries', help='Optional list of ISO2 country codes', 
    dest='countries', nargs='+', action='store', type=str, default=None)
  args = parser.parse_args()
  
  #
  # Filter parameters
  #
  
  # abs_thresholds = range(10000, 210000, 10000)
  abs_thresholds = range(1000, 801000, 1000)

  # from 40% - ~99.994% in decreasing step sizes
  # rel_thresholds = [100 - 60.0/pow(2,n) for n in range(14)]
  # rel_thresholds = range(40, 80) + [100 - 20.0/pow(2,n) for n in range(14)]
  rel_thresholds = \
    [40 + v*40/200.0 for v in range(200)] + \
    [80 + v*15/200.0 for v in range(200)] + \
    [95 + v*5/400.0 for v in range(400)]

  #
  # Get data
  #
  
  #getDb().echo = True    
  session = getSession()
  
  result = session.execute("""SELECT iso2, ue.uid as uid, type
    FROM %s ue 
    JOIN bulkimport_users bu ON (ue.uid=bu.uid)
    JOIN world_borders w ON (w.gid=ue.country_gid)
    ORDER BY iso2, type""" % (args.stats_table))

  # dict of sets: type -> (uid, uid, ...)
  all_users = defaultdict(set)
  # nested dict of sets: iso2 -> type -> (uid, uid, ...)
  users_by_country = defaultdict(lambda: defaultdict(set))
  
  num_records = 0
  for row in result:
    iso2 = row['iso2']
    uid = row['uid']
    type = row['type']
    
    all_users[type].add(uid)
    users_by_country[iso2][type].add(uid)
    num_records += 1

  print "Loaded %d records." % (num_records)
  
  if num_records==0:
    print "No training data found!"
    sys.exit(0)

  # Country selection
  countries = [iso2 
    for iso2 in users_by_country.keys() 
    if (len(users_by_country[iso2]['bulkimport'])>=2
      and len(users_by_country[iso2]['non-bulkimport'])>=2)]
  
  if args.countries:
    # manual country selection
    countries = []
    for iso2 in args.countries:
      if (len(users_by_country[iso2]['bulkimport'])>=2 and 
        len(users_by_country[iso2]['non-bulkimport'])>=2):
        countries.add(iso2)
      else:
        print "Not enough labelled data for country: %s, skipping" % iso2

  #
  # Global evaluation reports
  #

  # report TSV format
  colnames = ['cohort', 'filter_type', 'filter_param', 'abs_threshold', 
    'num_relevant', 'num_retrieved', 'num_relevant_retrieved', 'precision', 
    'recall', 'F']

  abs_stats = []
  for threshold in abs_thresholds:
    abs_stats.append(abs_eval_summary('global', threshold, all_users, 
      session, args.stats_table))
  
  rel_stats = []
  for percentile in rel_thresholds:
    rel_stats.append(rel_eval_summary('global', percentile, all_users, 
      session, args.stats_table))

  mkdir_p(args.outdir)

  eval_report(abs_stats, colnames, args.outdir, 'global_eval_absolute')
  eval_report(rel_stats, colnames, args.outdir, 'global_eval_relative')
  
  #
  # Country evaluation reports
  #
  
  abs_country_stats = defaultdict(list)
  rel_country_stats = defaultdict(list)

  for iso2 in countries:
    for threshold in abs_thresholds:
      abs_country_stats[iso2].append(
        abs_eval_summary(iso2, threshold, users_by_country[iso2], 
          session, args.stats_table, countries=[iso2]))

    eval_report(abs_country_stats[iso2], colnames, args.outdir, 
      '%s_eval_absolute' % iso2)
  
  for iso2 in countries:
    for percentile in rel_thresholds:
      rel_country_stats[iso2].append(
        rel_eval_summary(iso2, percentile, users_by_country[iso2], 
          session, args.stats_table, countries=[iso2]))

    eval_report(rel_country_stats[iso2], colnames, args.outdir, 
      '%s_eval_relative' % iso2)
  
  #
  # Country report: "best" thresholds
  #
  
  # iso2 -> eval_summary record
  peak_abs_stats = []
  peak_rel_stats = []
  
  for iso2 in countries:
    abs_F_scores = [s['F'] for s in abs_country_stats[iso2] if s['F']!=None]
    if len(abs_F_scores) > 0:
      max_abs_F = max(abs_F_scores)
      max_abs_threshold = min([s['abs_threshold'] for s in abs_country_stats[iso2] if s['F']==max_abs_F])

      all_at_abs_threshold = [[s
        for s in abs_country_stats[_iso2] 
        if s['abs_threshold']==max_abs_threshold and s['F']!=None]
          for _iso2 in abs_country_stats.keys()]
      F_at_abs_threshold = [s['F'] for sublist in all_at_abs_threshold for s in sublist]

      peak_abs_stats.append({
        'iso2': iso2,
        'threshold': max_abs_threshold,
        'F': max_abs_F,
        'all_F_at_threshold': F_at_abs_threshold,
        'mean_F_at_threshold': np.mean(F_at_abs_threshold),
        'std_F_at_threshold': np.std(F_at_abs_threshold)
      })
  
    rel_F_scores = [s['F'] for s in rel_country_stats[iso2] if s['F']!=None]
    if len(rel_F_scores) > 0:
      max_rel_F = max(rel_F_scores)
      max_rel_percentile = min([s['filter_param'] for s in rel_country_stats[iso2] if s['F']==max_rel_F])
      max_rel_threshold = min([s['abs_threshold'] for s in rel_country_stats[iso2] if s['F']==max_rel_F])

      all_at_rel_threshold = [[s
        for s in rel_country_stats[_iso2] 
        if s['filter_param']==max_rel_percentile and s['F']!=None]
          for _iso2 in rel_country_stats.keys()]
      F_at_rel_threshold = [s['F'] for sublist in all_at_rel_threshold for s in sublist]

      peak_rel_stats.append({
        'iso2': iso2,
        'percentile': max_rel_percentile,
        'threshold': max_rel_threshold,
        'F': max_rel_F,
        'all_F_at_threshold': F_at_rel_threshold,
        'mean_F_at_threshold': np.mean(F_at_rel_threshold),
        'std_F_at_threshold': np.std(F_at_rel_threshold)
      })
  
  eval_report(peak_abs_stats, 
    ['iso2', 'threshold', 'F', 'mean_F_at_threshold', 'std_F_at_threshold'], 
    args.outdir, 'countries_absolute_best')

  eval_report(peak_rel_stats, 
    ['iso2', 'percentile', 'threshold', 'F', 'mean_F_at_threshold', 'std_F_at_threshold'], 
    args.outdir, 'countries_relative_best')

  #
  # Threshold stability/variance report
  # 
  
  # Summary stats for "best" thresholds
  peak_abs_thresholds = [s['threshold'] for s in peak_abs_stats]
  peak_rel_thresholds = [s['threshold'] for s in peak_rel_stats]
  peak_rel_percentiles = [s['percentile'] for s in peak_rel_stats]

  F_at_peak_rel_threshold = [s 
    for sublist in peak_rel_stats 
    for s in sublist['all_F_at_threshold']]

  # Apply the "best" thresholds to all countries and get F-scores
  F_at_peak_abs_threshold = [s 
    for sublist in peak_abs_stats 
    for s in sublist['all_F_at_threshold']]

  F_at_peak_rel_threshold = [s 
    for sublist in peak_rel_stats 
    for s in sublist['all_F_at_threshold']]
  
  # Report
  var_stats = []
  var_stats.append({'type': 'absolute', 
    'num_countries': len(peak_abs_stats),
    'pop_std_F_at_peak': np.std(F_at_peak_abs_threshold),
    'mean_peak_percentile': None,
    'std_peak_percentile': None,
    'mean_peak_threshold': np.mean(peak_abs_thresholds),
    'std_peak_threshold': np.std(peak_abs_thresholds)
  })
  var_stats.append({'type': 'relative', 
    'num_countries': len(peak_rel_stats),
    'pop_std_F_at_peak': np.std(F_at_peak_rel_threshold),
    'mean_peak_percentile': np.mean(peak_rel_percentiles),
    'std_peak_percentile': np.std(peak_rel_percentiles),
    'mean_peak_threshold': np.mean(peak_rel_thresholds),
    'std_peak_threshold': np.std(peak_rel_thresholds)
  })

  eval_report(var_stats, 
    ['type', 'num_countries', 
      'pop_std_F_at_peak', 
      'mean_peak_percentile', 'std_peak_percentile',
      'mean_peak_threshold', 'std_peak_threshold'], 
    args.outdir, 'countries_variance')

  #
  # Global evaluation plots
  #
  
  metric_names = ['precision', 'recall', 'F']
  colors = ['#6EDD89', '#75A8EB', '#000000']
  # QUALITATIVE_DARK = ['#6EDD89', '#75A8EB', '#F2798C', '#F2D779', '#74D3E8']
  locale.setlocale(locale.LC_ALL, 'en_GB.utf8')
  
  make_eval_plot(abs_stats, 
    lambda x: locale.format("%d", x, grouping=True), 
    metric_names, args.outdir, 'global_eval_absolute', 
    colors=colors, legend_loc='lower right')

  make_eval_plot(rel_stats, 
    lambda x: str(x) + ' %', 
    metric_names, args.outdir, 'global_eval_relative', 
    colors=colors)

  #
  # Country evaluation plots
  #
  
  for iso2 in countries:

    make_eval_plot(abs_country_stats[iso2], 
      lambda x: locale.format("%d", x, grouping=True), 
      metric_names, args.outdir, '%s_eval_absolute' % iso2, 
      colors=colors, legend_loc='lower right')

    make_eval_plot(rel_country_stats[iso2], 
      lambda x: str(x) + ' %', 
      metric_names, args.outdir, '%s_eval_relative' % iso2,
      colors=colors)
