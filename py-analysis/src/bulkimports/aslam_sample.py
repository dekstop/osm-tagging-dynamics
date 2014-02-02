#
# Sample user accounts for an evaluation of automated bulk import detection.
# 
# Sampling method: Aslam et al (2007), "A Practical Sampling Strategy 
# for Efficient Retrieval Evaluation".
#

from __future__ import division # non-truncating division in Python 2.x

import argparse
from collections import defaultdict
import random
import sys

from app import *

# ===========
# = Reports =
# ===========

def encode(obj):
  if isinstance(obj, basestring):
    return obj.encode('utf-8')
  return obj

# data: a list of dictionaries
def save_csv(cohort, data, colnames, filename):
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile)
  outcsv.writerow(['cohort'] + colnames)
  for row in data:
    outcsv.writerow([cohort] + [encode(row[colname]) for colname in colnames])
  outfile.close()

# =========
# = Tools =
# =========

# ranked_items: in descending order of sampling weight.
# count: number of items to sample.
# note: sample order will follow input order roughly, but not exactly.
def aslamSample(ranked_items, count):
  # list of segments: [[x,x,x], [x,x,x], ...]
  buckets = [ranked_items[x:x+count] for x in range(0,len(ranked_items),count)]
  # list of buckets to sample from: [0, 1, 0, ...]
  sampled_buckets = [random.randrange(len(buckets)) for n in range(count)]
  # number of samples per bucket: {bucketIdx -> count}
  bucket_sample_count = dict((n, sampled_buckets.count(n)) for n in set(sampled_buckets))
  # final list of samples, by bucket
  samples = [
    random.sample(
      buckets[b], 
      min([bucket_sample_count[b], len(buckets[b])])
    ) for b in sorted(bucket_sample_count.keys())]
  # flatten this nested list and return
  return [item for sublist in samples for item in sublist]
  

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Sample user accounts for an evaluation of automated bulk import detection.')
  parser.add_argument('cohort', help='A unique string identifier for this sample set')
  parser.add_argument('num_samples', help='The number of users to select', type=int)
  parser.add_argument('csvfile', help='A filename to store the samples')
  parser.add_argument('--stats-table', help='Name of DB table with user edit stats', 
    dest='stats_table', action='store', type=str, default='user_edit_stats')
  parser.add_argument('--min-edits', help='Minimum number of edits', dest='min_edits', 
    action='store', type=int, default=0)
  parser.add_argument('--countries', help='Optional country name, as ISO2 country code', 
    dest='countries', action='store', nargs='+', type=str, default=None)
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 'num_edits', 'num_coll_edits', 
    'num_tag_add', 'num_tag_update', 'num_tag_remove']
  fields = ['uid', 'username'] + metrics
  
  #getDb().echo = True    
  session = getSession()
  
  metrics_select = []
  for metric in metrics:
    metrics_select.append("sum(%s)::int as %s" % (metric, metric))
  
  country_join = ''
  country_filter = ''
  if args.countries:
    country_join = 'JOIN world_borders w ON (w.gid=ue.country_gid)'
    country_filter = "WHERE w.iso2 IN ('%s')" % ("', '".join(args.countries))
  
  edits_filter = ''
  if args.min_edits:
    edits_filter = 'HAVING sum(num_edits)>=%d' % (args.min_edits)
  
  result = session.execute("""SELECT uid, MAX(username) as username, %s
    FROM %s ue %s %s
    GROUP BY uid
    %s
    ORDER BY num_edits DESC""" % (
      ', '.join(metrics_select), 
      args.stats_table, country_join, country_filter, 
      edits_filter))

  # uid -> {map: uid, username, num_edits, ...}
  items = dict()
  # ranked list of uids
  ranked_ids = []
  
  num_records = 0
  for row in result:
    uid = row['uid']
    record = defaultdict(str)
    for field in fields:
      record[field] = row[field]
    if uid in items.keys():
      print "already an entry for %d" % uid
    items[uid] = record
    ranked_ids.append(uid)
    num_records += 1
  print "Loaded %d records." % (num_records)
  
  if num_records==0:
    print "No records to sample from!"
    sys.exit(0)

  #
  # Sample
  #
  
  sampled_ids = aslamSample(ranked_ids, args.num_samples)
  samples = [items[s] for s in sampled_ids]

  mkdir_p(os.path.dirname(args.csvfile))
  save_csv(args.cohort, samples, fields, args.csvfile)

  for item in samples[:10]:
    print "%d: %s (%d edits)" % (item['uid'], item['username'], item['num_edits'])
