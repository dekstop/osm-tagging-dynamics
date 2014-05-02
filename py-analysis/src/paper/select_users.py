#
# Statistics relating to collaborative editing practices.
#

from __future__ import division # non-truncating division in Python 2.x

import argparse
from collections import defaultdict
from decimal import Decimal
import sys

import numpy as np

from app import *
from shared import *

# =========
# = Tools =
# =========

def get_unknown_countries(session, iso2_codes):
  result = session.execute(
    """SELECT w.iso2 FROM world_borders w 
    WHERE w.iso2 IN ('%s')""" % ("', '".join(iso2_codes)))
  found = set([rec['iso2'] for rec in result])
  return [iso2 for iso2 in iso2_codes if iso2 not in found]
 
# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--iso2-codes', help='list of ISO2 country codes', dest='iso2_codes', nargs='+', action='store', type=str, default=None)
  parser.add_argument('--min-edits', help='minimum number of edits per user and region', dest='min_edits', action='store', type=int, default=None)
  parser.add_argument('--max-edits', help='maximum number of edits per user and region', dest='max_edits', action='store', type=int, default=None)
  parser.add_argument('--bulk-percentile', help='percentile threshold for bulk import users, range [0..100]', dest='bulk_percentile', type=float, action='store', default=None)
  parser.add_argument('--stats-table', help='table name with user edit stats', dest='stats_table', action='store', default='user_edit_stats')
  args = parser.parse_args()

  #
  # Get data
  #

  user_fields = ['uid', 'num_poi', 
    'num_edits',  'num_tag_add', 'num_tag_update', 'num_tag_remove', 
    'num_coll_edits',  'num_coll_tag_add', 'num_coll_tag_update', 'num_coll_tag_remove', 
    'p_coll_edit', 'p_coll_tag_add', 'p_coll_tag_update', 'p_coll_tag_remove',
    'num_tag_keys', 'days_active', 'activity_period_days']

  #getDb().echo = True    
  session = getSession()
  
  # filters
  select_filter = ""

  if args.iso2_codes and len(args.iso2_codes)>0:
    print "Limiting to countries: " + ", ".join(args.iso2_codes)
    select_filter += " AND w.iso2 IN ('%s') " % ("', '".join(args.iso2_codes))
    # validate first
    missing = get_unknown_countries(session, args.iso2_codes)
    if len(missing) > 0:
      print "Could not recognise all country codes. Unknown: %s" % (', '.join(missing))
      sys.exit(1)
  
  if args.min_edits:
    select_filter += " AND ue.num_edits>=%d " % (args.min_edits)
  if args.max_edits:
    select_filter += " AND ue.num_edits<%d " % (args.max_edits)
  
  session = getSession()
  result = session.execute("""SELECT w.iso2, %s
  FROM %s ue
  JOIN world_borders w ON (ue.country_gid=w.gid)
  WHERE TRUE %s
  ORDER BY w.name, uid""" % (", ".join(user_fields), args.stats_table, select_filter))
  
  # dict: iso2 -> list of user records
  raw_data = defaultdict(list)
  num_records = 0
  for row in result:
    record = dict()
    for field in user_fields:
      record[field] = row[field]
    raw_data[row['iso2']].append(record)
    num_records += 1
  print "Loaded %d records." % (num_records)
  
  
  #
  # No filter? Store and exit
  #
  
  mkdir_p(args.outdir)

  if args.bulk_percentile==None:
    profiledata_report(raw_data, 'country', user_fields, args.outdir, "user_profiles")
    sys.exit(0)
  
  #
  # Filter bulk imports
  #
  
  # dict: iso2 -> list of user records
  data = defaultdict(list)
  bulk_thresholds = defaultdict(None)

  print "Filtering bulk imports based on percentile threshold: %.4f" % args.bulk_percentile
  for iso2 in raw_data.keys():
    all_num_edits = [r['num_edits'] for r in raw_data[iso2]]
    bulk_thresholds[iso2] = round(np.percentile(sorted(all_num_edits), args.bulk_percentile))
    data[iso2] = [r for r in raw_data[iso2] if r['num_edits'] < bulk_thresholds[iso2]]

  for iso2 in sorted(data.keys()):
    print "%s: %d raw, %d filtered (max %d edits)" % (
      iso2, len(raw_data[iso2]), len(data[iso2]), bulk_thresholds[iso2])

  #
  # Filter stats: impact of bulk import filter
  #
  
  # iso2 -> metric -> value
  filter_stats = defaultdict(dict)

  for iso2 in data.keys():
    rec = dict()

    rec['threshold'] = bulk_thresholds[iso2]

    rec['num_users_pre'] = len(raw_data[iso2])
    rec['num_users_post'] = len(data[iso2])
    rec['p_users_removed'] = Decimal(1.0) - \
      Decimal(rec['num_users_post']) / rec['num_users_pre']

    raw_edits = [d['num_edits'] for d in raw_data[iso2]]
    edits = [d['num_edits'] for d in data[iso2]]
    rec['num_edits_pre'] = sum(raw_edits)
    rec['num_edits_post'] = sum(edits)
    rec['p_edits_removed'] = Decimal(1.0) - \
      Decimal(rec['num_edits_post']) / rec['num_edits_pre']

    raw_coll_edits = [d['num_coll_edits'] for d in raw_data[iso2]]
    coll_edits = [d['num_coll_edits'] for d in data[iso2]]
    rec['num_coll_edits_pre'] = sum(raw_coll_edits)
    rec['num_coll_edits_post'] = sum(coll_edits)
    rec['p_coll_edits_removed'] = Decimal(1.0) - \
      Decimal(rec['num_coll_edits_post']) / rec['num_coll_edits_pre']
    
    filter_stats[iso2] = rec
  
  #
  # Basic user report, impact of bulk import filter
  #
  
  profiledata_report(raw_data, 'country', user_fields, args.outdir, "user_profiles_unfiltered")
  profiledata_report(data, 'country', user_fields, args.outdir, "user_profiles")

  groupstat_report(filter_stats, 'country', 
    ['threshold', 
      'num_users_pre', 'num_users_post', 'p_users_removed',
      'num_edits_pre', 'num_edits_post', 'p_edits_removed',
      'num_coll_edits_pre', 'num_coll_edits_post', 'p_coll_edits_removed'], 
    args.outdir, 'bulkimport_filter_stats')
  
  # Countries are ranked by number of users, descending
  iso2s = sorted(data.keys(), key=lambda iso2: len(data[iso2]), reverse=True)
  
  group_share_plot(filter_stats, iso2s, 
    ['p_users_removed', 'p_edits_removed', 'p_coll_edits_removed'], 
    args.outdir, 'bulkimport_filter_stats',
    colors=['#E8AFB8', '#EEEEEE'])
