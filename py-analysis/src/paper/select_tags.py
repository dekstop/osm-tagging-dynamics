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
  parser.add_argument('--tag-column', help='the column name used for tag IDs', dest='tagcol', action='store', default='key')
  parser.add_argument('--iso2-codes', help='list of ISO2 country codes', dest='iso2_codes', nargs='+', action='store', type=str, default=None)
  parser.add_argument('--min-edits', help='minimum number of edits per user and region', dest='min_edits', action='store', type=int, default=None)
  parser.add_argument('--max-edits', help='maximum number of edits per user and region', dest='max_edits', action='store', type=int, default=None)
  parser.add_argument('--tag-stats-table', help='table name with tag edit stats', dest='tag_stats_table', action='store', default='tag_edit_stats')
  parser.add_argument('--user-stats-table', help='table name with user edit stats', dest='user_stats_table', action='store', default='user_edit_stats')
  args = parser.parse_args()

  #
  # Get data
  #

  tag_fields = [args.tagcol, 'num_users', 'num_coll_users', 'num_poi', 
    'num_edits',  'num_tag_add', 'num_tag_update', 'num_tag_remove', 
    'num_coll_edits',  'num_coll_tag_add', 'num_coll_tag_update', 'num_coll_tag_remove', 
    'num_tag_values']
  computed_tag_fields = ['%pop', '%coll_pop', '%edits', '%coll_edits']
  fields = tag_fields + computed_tag_fields

  #getDb().echo = True    
  session = getSession()
  
  # filters
  country_filter = ""

  if args.iso2_codes and len(args.iso2_codes)>0:
    print "Limiting to countries: " + ", ".join(args.iso2_codes)
    country_filter = " AND w.iso2 IN ('%s') " % ("', '".join(args.iso2_codes))
    # validate first
    missing = get_unknown_countries(session, args.iso2_codes)
    if len(missing) > 0:
      print "Could not recognise all country codes. Unknown: %s" % (', '.join(missing))
      sys.exit(1)
  
  thresholds_filter = ""
  if args.min_edits:
    thresholds_filter += " AND te.num_edits>=%d " % (args.min_edits)
  if args.max_edits:
    thresholds_filter += " AND te.num_edits<%d " % (args.max_edits)
  
  # select
  session = getSession()
  result = session.execute("""SELECT w.iso2, %s,
    num_users::numeric / pop_users as \"%%pop\",
    num_edits::numeric / pop_edits as \"%%edits\",
    num_coll_users::numeric / pop_coll_users as \"%%coll_pop\",
    num_coll_edits::numeric / pop_coll_edits as \"%%coll_edits\"
  FROM %s te
  JOIN (
    SELECT country_gid,
      count(distinct uid) as pop_users, 
      count(coll_user) as pop_coll_users, 
      sum(num_edits) as pop_edits, 
      sum(num_coll_edits) as pop_coll_edits
    FROM (
      SELECT *,
        CASE WHEN num_coll_edits>0 THEN 1 ELSE 0 END as coll_user
      FROM %s
    ) t
    GROUP BY country_gid
  ) pop ON (te.country_gid=pop.country_gid)
  JOIN world_borders w ON (te.country_gid=w.gid)
  WHERE TRUE %s %s
  ORDER BY w.iso2, %s""" % (", ".join(tag_fields), args.tag_stats_table, 
    args.user_stats_table, country_filter, thresholds_filter, args.tagcol))
  
  # dict: iso2 -> list of user records
  raw_data = defaultdict(list)
  num_records = 0
  for row in result:
    record = dict()
    for field in fields:
      record[field] = row[field]
    raw_data[row['iso2']].append(record)
    num_records += 1
  print "Loaded %d records." % (num_records)

  #
  # Store and exit
  #
  
  mkdir_p(args.outdir)

  profiledata_report(raw_data, 'country', fields, args.outdir, "profiles")
