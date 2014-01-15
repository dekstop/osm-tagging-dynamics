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

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy
import scipy.stats.stats as stats

from app import *

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
# perc: [0..1]
def count_cumsum_percentile(values, perc, reverse=True):
  values = sorted(values, reverse=reverse)
  total = sum(values)
  limit = decimal.Decimal(total) * decimal.Decimal(perc)
  ax = decimal.Decimal(0)
  for idx in range(len(values)):
    ax += values[idx]
    if ax >= limit:
      return idx + 1
  return len(values)


# ===========
# = Reports =
# ===========

# data: a list of dictionaries
def report(data, colnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(colnames)
  for row in data:
    outcsv.writerow([row[colname] for colname in colnames])
  outfile.close()

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


# =========
# = Plots =
# =========

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Statistics relating to collaborative editing practices.')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--countries', help='list of country names', 
    dest='countries', nargs='+', action='store', type=str, default=None)
  parser.add_argument('--min-edits', dest='min_edits', type=int, default=None, 
    action='store', help='minimum number of edits per user')
  parser.add_argument('--max-edits', dest='max_edits', type=int, default=None, 
    action='store', help='maximum number of edits per user')
  
  args = parser.parse_args()

  #
  # Get data
  #
  
  user_fields = ['uid', 'num_poi', 
    'num_edits',  'num_tag_add', 'num_tag_update', 'num_tag_remove', 
    'num_coll_edits',  'num_coll_tag_add', 'num_coll_tag_update', 'num_coll_tag_remove', 
    'p_coll_edit', 'p_coll_tag_add', 'p_coll_tag_update', 'p_coll_tag_remove',
    'num_tag_keys', 'days_active', 'activity_period_days']
  
  # country_fields = ['country', 'num_editors'] + user_fields
  
  # select_expr = []
  # for field in user_fields:
  #   select_expr.append("median(%s) as %s" % (field, field))

  # filters
  select_filter = ""

  if args.countries:
    print "Limiting to countries: " + ", ".join(args.countries)
    select_filter += " AND w.name IN ('%s') " % ("', '".join(args.countries))
  
  if args.min_edits:
    select_filter += " AND ue.num_edits>=%d " % (args.min_edits)
  if args.max_edits:
    select_filter += " AND ue.num_edits<%d " % (args.max_edits)
  
  #getDb().echo = True    
  session = getSession()
  result = session.execute("""SELECT w.name as country, %s
  FROM user_edit_stats ue
  JOIN world_borders w ON (ue.country_gid=w.gid)
  WHERE TRUE %s
  ORDER BY w.name, uid""" % (", ".join(user_fields), select_filter))

  # dict: country -> list of user records
  data = defaultdict(list)
  num_records = 0
  for row in result:
    record = dict()
    for field in user_fields:
      record[field] = row[field]
    data[row['country']].append(record)
    num_records += 1
  print "Loaded %d records." % (num_records)

  #
  # Basic user report
  #
  mkdir_p(args.outdir)
  group_report(data, 'country', user_fields, args.outdir, "user_profiles")
  
  #
  # Country aggregations
  #
  
  topuser_percentile = 0.8
  tag_action_threshold = 50
  
  countrydata = dict()
  for country in data.keys():
    rec = dict()
    num_users = len(data[country])

    edits = [d['num_edits'] for d in data[country]]
    tag_adds = [d['num_tag_add'] for d in data[country]]
    tag_updates = [d['num_tag_update'] for d in data[country]]
    tag_removes = [d['num_tag_remove'] for d in data[country]]
    coll_edits = [d['num_coll_edits'] for d in data[country]]
    coll_tag_adds = [d['num_coll_tag_add'] for d in data[country]]
    coll_tag_updates = [d['num_coll_tag_update'] for d in data[country]]
    coll_tag_removes = [d['num_coll_tag_remove'] for d in data[country]]

    # "population"
    rec['num_users'] = num_users

    # percentage of users who account for 80% of edits
    num_top_users = count_cumsum_percentile(edits, 0.8)
    rec['p_top_editors'] = decimal.Decimal(num_top_users) / num_users
    
    # percentage of edits that are collaborative
    rec['p_coll_edits'] = decimal.Decimal(sum(coll_edits)) / sum(edits)
    rec['p_coll_adds'] = decimal.Decimal(sum(coll_tag_adds)) / sum(edits)
    rec['p_coll_updates'] = decimal.Decimal(sum(coll_tag_updates)) / sum(edits)
    rec['p_coll_removes'] = decimal.Decimal(sum(coll_tag_removes)) / sum(edits)

    # percentage of users who account for 80% of collab edits
    num_top_coll_users = count_cumsum_percentile(coll_edits, 0.8)
    rec['p_top_coll_editors'] = decimal.Decimal(num_top_coll_users) / num_users
    
    # percentage of users who account for 80% of all adds
    num_top_add_users = count_cumsum_percentile(tag_adds, 0.8)
    rec['p_top_add_editors'] = decimal.Decimal(num_top_add_users) / num_users

    # percentage of users who account for 80% of all updates
    num_top_update_users = count_cumsum_percentile(tag_updates, 0.8)
    rec['p_top_update_editors'] = decimal.Decimal(num_top_update_users) / num_users

    # percentage of users who account for 80% of all removes
    num_top_remove_users = count_cumsum_percentile(tag_removes, 0.8)
    rec['p_top_remove_editors'] = decimal.Decimal(num_top_remove_users) / num_users

    # done.
    countrydata[country] = rec
  
  country_fields = ['num_users', 'p_top_editors', 
    'p_coll_edits', 'p_coll_adds', 'p_coll_updates', 'p_coll_removes',
    'p_top_coll_editors', 'p_top_add_editors', 'p_top_update_editors', 'p_top_remove_editors',
    ]
  segment_report(countrydata, 'country', country_fields, args.outdir, "country_profiles")
  