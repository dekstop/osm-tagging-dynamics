#
# Evaluate the suitability of various engagement thresholds for automated bulk import detection.
# 

from __future__ import division # non-truncating division in Python 2.x

import argparse
from collections import defaultdict
import decimal
import random
import sys

import numpy

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
# abs_threshold: min. number of edits
# Returns a set of uids
def get_uids_above_abs_threshold(session, abs_threshold):
  result = session.execute("""SELECT uid 
    FROM user_edit_stats ue 
    GROUP BY uid 
    HAVING sum(num_edits)>=%d""" % (abs_threshold))
  uids = set()
  for row in result:
    uids.add(row['uid'])
  return uids
  
# Global only for now.
# percentile: [0..100] inclusive
# Returns an absolute threshold
def get_threshold_for_percentile(session, percentile):
  ranking = []
  result = session.execute("""SELECT num_edits 
    FROM user_edit_stats 
    ORDER BY num_edits ASC""")
  for row in result:
    ranking.append(row['num_edits'])
  return round(numpy.percentile(ranking, percentile))
  
# =========
# = Tools =
# =========

def f_score(precision, recall, beta=1):
  return (1 + beta*beta) * (precision*recall) / (beta*beta*precision + recall)

def eval_summary(cohort, filter_type, filter_param, abs_threshold, relevant, retrieved):
  rec = defaultdict(lambda: '-')
  rec['cohort'] = cohort
  rec['filter_type'] = filter_type
  rec['filter_param'] = filter_param
  rec['abs_threshold'] = abs_threshold
  rec['num_relevant'] = len(relevant)
  rec['num_retrieved'] = len(retrieved)
  rec['num_relevant_retrieved'] = len(relevant.intersection(retrieved))
  if rec['num_retrieved']>0:
    rec['precision'] = float(rec['num_relevant_retrieved']) / rec['num_retrieved']
    rec['recall'] = float(rec['num_relevant_retrieved']) / rec['num_relevant']
    rec['F_1'] = f_score(rec['precision'], rec['recall'], 1)
    rec['F_0_5'] = f_score(rec['precision'], rec['recall'], 0.5)
  return rec

# =========
# = Plots =
# =========  

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Evaluate the suitability of various engagement thresholds for automated bulk import detection.')
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('--country', help='Optional list of ISO2 country codes', 
    dest='countries', nargs='+', action='store', type=str, default=None)
  args = parser.parse_args()

  #
  # Get data
  #
  
  #getDb().echo = True    
  session = getSession()
  
  country_filter = ''
  if args.countries:
    country_filter = "WHERE w.iso2 IN '%s'" % ("', '".join(args.countries))
  
  result = session.execute("""SELECT iso2, ue.uid as uid, type
    FROM user_edit_stats ue 
    JOIN bulkimport_users bu ON (ue.uid=bu.uid)
    JOIN world_borders w ON (w.gid=ue.country_gid)
    %s
    ORDER BY iso2, type""" % (country_filter))

  # dict of sets: type -> (uid, uid, ...)
  all_users = defaultdict(set)
  # nested dict of sets: iso2 -> type -> (uid, uid, ...)
  by_country = defaultdict(lambda: defaultdict(set))
  
  num_records = 0
  for row in result:
    iso2 = row['iso2']
    uid = row['uid']
    type = row['type']
    
    all_users[type].add(uid)
    by_country[iso2][type].add(uid)
    num_records += 1
  print "Loaded %d records." % (num_records)
  
  if num_records==0:
    print "No training data found!"
    sys.exit(0)

  #
  # Evaluate
  #

  # report TSV format
  colnames = ['cohort', 'filter_type', 'filter_param', 'abs_threshold', 
    'num_relevant', 'num_retrieved', 'num_relevant_retrieved', 'precision', 
    'recall', 'F_1', 'F_0_5']

  # a list of evaluation metrics per filter and threshold
  eval_stats = []
  
  for threshold in range(1000, 50000, 1000):
    # global
    relevant = all_users['bulkimport'] # .union(all_users['unknown'])
    retrieved = get_uids_above_abs_threshold(session, threshold)
    eval_stats.append(eval_summary('global', 
      'absolute', threshold, threshold, 
      relevant, retrieved))
  
  # from 40% - ~99.994% in decreasing step sizes
  for percentile in [100 - 60.0/pow(2,n) for n in range(14)]:
    # global
    relevant = all_users['bulkimport'] # .union(all_users['unknown'])
    abs_threshold = get_threshold_for_percentile(session, percentile)
    retrieved = get_uids_above_abs_threshold(session, abs_threshold)
    eval_stats.append(eval_summary('global', 
      'relative', percentile, abs_threshold, 
      relevant, retrieved))

    # by country
    # for iso2 in sorted(by_country.keys()):
      # pass


  # 
  # Report
  # 

  mkdir_p(args.outdir)
  eval_report(eval_stats, colnames, args.outdir, 'global_thresholds')
  