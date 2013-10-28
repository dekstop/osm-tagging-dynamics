#
# Segment the users of each region by a single anchoring metric.
#

import argparse
from collections import defaultdict
import decimal
import sys

import numpy

from app import *

# =========
# = Tools =
# =========

# This is close to the classic percentile function (numpy.percentile) --
# it determines thresholds based on the count of observations.
#
# The process:
# - count the number of values
# - order all values by size
# - for each requested percentile: 
#   - pick the n smallest entries whose number is still below the percentile (as percentage of the count)
#   - return the largest value in this selected group, or min(values)-1 if all values exceed the threshold
def percentile(values, percentiles):
  values = sorted(values)
  percentiles = sorted(percentiles)
  count = len(values)
  thresholds = []
  for perc in percentiles:
    prev = min(values)-1
    for idx in range(count):
      if (100.0*(idx+1)/count > perc):  # exceeded the threshold?
        thresholds.append(prev)         # pick previous value
        break
      prev = values[idx]
    if prev not in thresholds:      # threshold was never exceeded? 
      thresholds.append(values[-1]) # pick max value
                                    # (happens when a percentile is '100' or more)
  return thresholds

# This is *not* the classic percentile function (numpy.percentile) --
# it determines thresholds based on the *cumulative sum* of observations, not their count.
#
# The process:
# - calculate the total (the sum of all values)
# - order all values by size
# - for each requested percentile: 
#   - pick the n smallest entries whose sum is still below the percentile (as percentage of the total)
#   - return the largest value in this selected group, or None if all values exceed the threshold
def cumsum_percentile(values, percentiles):
  values = sorted(values)
  percentiles = sorted(percentiles)
  total = sum(values)
  thresholds = []
  for perc in percentiles:
    ax = decimal.Decimal(0)
    prev = min(values)-1
    for val in values:
      ax += val
      if (100*ax/total > perc):  # exceeded the threshold?
        thresholds.append(prev)   # pick previous value
        break
      prev = val
    if prev not in thresholds:      # threshold was never exceeded? 
      thresholds.append(values[-1]) # pick max value
                                    # (happens when a percentile is '100' or more)
  return thresholds

# ========
# = Main =
# ========

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Segment the users of each region by a single anchoring metric.')
  parser.add_argument('scheme_name', help='name for this segmentation scheme')
  parser.add_argument('metric', help='metric along which users are segmented')
  parser.add_argument('outdir', help='output directory for segmentation reports')
  parser.add_argument('--regions', dest='regions', type=str, nargs='+', default=None, 
      action='store', help='list of region names')
  parser.add_argument('--overwrite', dest='overwrite', default=False, 
    action='store_true', help='overwrite existing data if the scheme already exists')

  parser.add_argument('--percentiles', dest='percentiles', type=float, nargs='+', default=[0,25,50,75,100], 
      action='store', help='percentile bands, a space-separated list of numbers [0..100]. Default: 0 25 50 75 100 (quartiles)')
  parser.add_argument('--cumsum', dest='cumsum', default=False, 
    action='store_true', help='determine percentile thresholds based on the cumulative sum of observations, not their count')
  args = parser.parse_args()

  # getDb().echo = True
  session = getSession()

  #
  # Overwrite check
  #
  
  row = session.execute("""SELECT count(*) as total FROM sample_1pc.region_user_segment 
      WHERE scheme='%s'""" % (args.scheme_name)).fetchone()

  if row['total'] > 0:
    if args.overwrite:
      session.execute("""DELETE FROM sample_1pc.region_user_segment 
        WHERE scheme='%s'""" % (args.scheme_name))
    else:
      print "Error: the segmentation scheme '%s' already exists!" % (args.scheme_name)
      sys.exit(1)

  #
  # Load data
  #
  
  query = """SELECT r.name AS region, %s FROM sample_1pc.user_edit_stats s 
    JOIN region r ON s.region_id=r.id""" % (args.metric)
  if args.regions!=None:
    str_regions = "', '".join(args.regions)
    print "Limiting to regions: '%s'" % (str_regions)
    query += " WHERE r.name IN ('%s')" % (str_regions)
  result = session.execute(query)
  # print result.keys()

  data = defaultdict(list)
  num_records = 0
  for row in result:
    region = row['region']
    data[region].append(row[args.metric])
    num_records += 1
  
  print "Loaded %d records." % (num_records)

  regions = sorted(data.keys())
  
  #
  # Get bands per region
  #
  
  band_thresholds = dict()
  for region in regions:
    band_thresholds[region] = defaultdict(list)
  
  for region in regions:
    # print region
    values = data[region]

    # percentiles
    if args.cumsum:
      thresholds = sorted(cumsum_percentile(values, args.percentiles))
    else:
      # classic percentile
      thresholds = sorted(percentile(values, args.percentiles))
    
    # remove duplicate thresholds for low-data regions
    unique_thresholds = sorted(list(set(thresholds)))
    if (unique_thresholds != thresholds):
      print "Warning: duplicate band thresholds found for region '%s', reducing number of bands." % (region)
      print "Requested: %s" % (thresholds)
      print "Without duplicates: %s" % (unique_thresholds)
    
    thresholds = unique_thresholds
    min_threshold = thresholds[0]   # may be None: "don't apply a min threshold"
    max_threshold = thresholds[-1]  # will never be None, but may be max(data)

    band_expr = ''
    groupid = 1
    low = thresholds[0]
    for high in thresholds[1:]:
      parts = []
      if low!=None: # only the first threshold can ever be 'None'
        parts.append("%s > %f" % (args.metric, low))
      parts.append("%s <= %f" % (args.metric, high)) 
      band_expr += "WHEN (" + " AND ".join(parts) + ") THEN %d" % (groupid)
      band_thresholds[region][groupid] = [low, high]
      low = high
      groupid += 1

    query = """INSERT INTO sample_1pc.region_user_segment(region_id, scheme, uid, groupid) 
      SELECT r.id, '%s', uid, 
      CASE %s END
      FROM sample_1pc.user_edit_stats ues
      JOIN region r ON ues.region_id=r.id
      WHERE r.name='%s'
      """ % (args.scheme_name, band_expr, region)

    if min_threshold and min_threshold>=min(values):
      print "Filtering the bottom band for region '%s': %s > %f" % (region, args.metric, min_threshold)
      query += " AND %s > %f" % (args.metric, min_threshold)

    if max_threshold<max(values):
      print "Filtering the top band for region '%s': %s <= %f" % (region, args.metric, max_threshold)
      query += " AND %s <= %f" % (args.metric, max_threshold)

    result = session.execute(query)
  session.commit()
  
  #
  # Report
  #
  
  mkdir_p(args.outdir)
  
  # Region totals
  filename = "%s/segments_%s_totals.txt" % (args.outdir, args.scheme_name)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  header = ['region', 'scheme', 'num_users', args.metric]
  outcsv.writerow(header)
  
  for region in regions:
    values = data[region]
    num_users = len(values)
    total = sum(values)
    outcsv.writerow([region, args.scheme_name, num_users, total])
  
  outfile.close()
  
  # Region bands
  filename = "%s/segments_%s_bands.txt" % (args.outdir, args.scheme_name)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  header = ['region', 'scheme', 'groupid', 'low', 'high', 'num_users', args.metric]
  outcsv.writerow(header)
  
  result = session.execute(
    """SELECT r.name as region, scheme, groupid, count(distinct seg.uid) as num_users, sum(%s) as total
      FROM sample_1pc.region_user_segment seg
      JOIN sample_1pc.user_edit_stats ues ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)
      JOIN region r ON seg.region_id=r.id
      WHERE seg.scheme='%s'
      GROUP BY r.name, scheme, groupid
      ORDER BY r.name, scheme, groupid""" % (args.metric, args.scheme_name))

  for row in result:
    region = row['region']
    band_idx = row['groupid']
    outcsv.writerow([
      region, row['scheme'], band_idx,
      band_thresholds[region][band_idx][0],
      band_thresholds[region][band_idx][1],
      row['num_users'], row['total']
    ])
    # print row
  
  outfile.close()
  