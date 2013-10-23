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

# This is *not* the classic percentile function (numpy.percentile) --
# it determines thresholds based on the *sum* of observations, not their count,
# and it orders observations in descending order.
#
# The process:
# - calculate the total (the sum of all values)
# - order all values by size, *descending*
# - for each requested percentile: 
#   - pick the n largest entries whose sum just exceeded the percentile (as percentage of the total)
#   - return the smallest value in this selected group
def top_percentile(values, percentiles):
  values = sorted(values, reverse=True)
  percentiles = sorted(percentiles)

  total = sum(values)
  thresholds = []
  for perc in percentiles:
    ax = decimal.Decimal(0)
    for val in values:
      ax += val
      if (100*ax/total >= perc):
        # print "threshold: %f at value: %d (%f%%)" % (perc, val, 100*ax/total)
        thresholds.append(val)
        break
  return thresholds

# a = [1,2,3,4,5,6,7,8,9,10]
# b = [1,1,1,1,1,1,1,1,1,1]
# p = [1, 10,20,50]
# print a, p
# print top_percentile(a, p)
# print numpy.percentile(a, p)
# print b, p
# print top_percentile(b, p)
# print numpy.percentile(b, p)

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
  parser.add_argument('--bands', dest='bands', type=int, nargs='+', default=[25,50,75], 
      action='store', help='percentile bands, a space-separated list of numbers [0..100]. Default: 25 50 75 (quartiles)')
  parser.add_argument('--overwrite', dest='overwrite', default=False, 
    action='store_true', help='overwrite existing data if the scheme already exists')
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
  num_users = 0
  for row in result:
    region = row['region']
    data[region].append(row[args.metric])
    num_users += 1
  
  print "Loaded %d records." % (num_users)

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

    # classic percentile
    thresholds = sorted(numpy.percentile(values, args.bands))
    
    # top-ranked percentile
    # thresholds = sorted(top_percentile(values, args.bands))
    
    # if (max(values) not in thresholds):
    thresholds.append(max(values))
    
    # remove duplicate thresholds for low-data regions
    unique_thresholds = sorted(list(set(thresholds)))
    if (unique_thresholds != thresholds):
      print "Warning: duplicate band thresholds found for region '%s', reducing number of bands." % (region)
      print "Requested: %s" % (thresholds)
      print "Without duplicates: %s" % (unique_thresholds)
    
    thresholds = unique_thresholds

    band_expr = ''
    band_idx = 1
    low = 0
    for high in thresholds:
      band_expr += "WHEN (%s > %f AND %s <= %f) THEN %d " % (args.metric, low, args.metric, high, band_idx)
      band_thresholds[region][band_idx] = [low, high]

      band_idx += 1
      low = high

    result = session.execute(
    """INSERT INTO sample_1pc.region_user_segment(region_id, scheme, uid, groupid) 
      SELECT r.id, '%s', uid, 
      CASE %s END
      FROM sample_1pc.user_edit_stats ues
      JOIN region r ON ues.region_id=r.id
      WHERE r.name='%s'
      """ % (args.scheme_name, band_expr, region))
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
  