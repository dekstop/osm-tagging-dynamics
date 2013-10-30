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

# Computes percentile band breaks so that every band is half the size of the previous one.
# bottom, top are in range [0..100]
def get_shrinking_percentile_bands(bottom, top, num_bands):
  num_slots = pow(2, num_bands) - 1
  v = bottom
  bands = [bottom]
  for i in range(num_bands-1):
    band_slot_width = pow(2, (num_bands-1) - i)
    v += 1.0 * (top-bottom) * band_slot_width / num_slots
    bands.append(v)
  bands.append(top)
  return bands

# code from http://danieljlewis.org/files/2010/06/Jenks.pdf
# described at http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/
def get_jenks_breaks(values, num_breaks):
  values.sort()
  mat1 = []
  for i in range(0,len(values)+1):
    temp = []
    for j in range(0,num_breaks+1):
      temp.append(0)
    mat1.append(temp)
  mat2 = []
  for i in range(0,len(values)+1):
    temp = []
    for j in range(0,num_breaks+1):
      temp.append(0)
    mat2.append(temp)
  for i in range(1,num_breaks+1):
    mat1[1][i] = 1
    mat2[1][i] = 0
    for j in range(2,len(values)+1):
      mat2[j][i] = float('inf')
  v = 0.0
  for l in range(2,len(values)+1):
    s1 = 0.0
    s2 = 0.0
    w = 0.0
    for m in range(1,l+1):
      i3 = l - m + 1
      val = float(values[i3-1])
      s2 += val * val
      s1 += val
      w += 1
      v = s2 - (s1 * s1) / w
      i4 = i3 - 1
      if i4 != 0:
        for j in range(2,num_breaks+1):
          if mat2[l][j] >= (v + mat2[i4][j - 1]):
            mat1[l][j] = i3
            mat2[l][j] = v + mat2[i4][j - 1]
    mat1[l][1] = 1
    mat2[l][1] = v
  k = len(values)
  breaks = []
  for i in range(0,num_breaks+1):
    breaks.append(0)
  breaks[num_breaks] = float(values[len(values) - 1])
  countNum = num_breaks
  while countNum >= 2:#print "rank = " + str(mat1[k][countNum])
    id = int((mat1[k][countNum]) - 2)
    #print "val = " + str(values[id])
    breaks[countNum - 1] = values[id]
    k = int((mat1[k][countNum] - 1))
    countNum -= 1
  return breaks

# Jiang (2011): Head/tail Breaks
# Computes breaks by iteratively segmenting the remaining top end along the mean.
def get_head_tail_breaks(values, num_breaks):
  values = sorted(values)
  breaks = [values[0]-1]
  for n in range(num_breaks-1):
    mean = numpy.mean(values)
    breaks.append(mean)
    values = [v for v in values if v>mean]
    if len(values)==1:
      break
  breaks.append(values[-1])
  return breaks
  

# ========
# = Main =
# ========

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Segment the users of each region by a single anchoring metric.')
  parser.add_argument('scheme_name', help='name for this segmentation scheme')
  parser.add_argument('metric', help='metric along which users are segmented')
  parser.add_argument('outdir', help='output directory for segmentation reports')
  parser.add_argument('--schema', dest='schema', type=str, default='public', 
      action='store', help='parent schema that contains data tables. Default: public')
  parser.add_argument('--regions', dest='regions', type=str, nargs='+', default=None, 
      action='store', help='list of region names')
  parser.add_argument('--overwrite', dest='overwrite', default=False, 
    action='store_true', help='overwrite existing data if the scheme already exists')

  parser.add_argument('--filter-lower', dest='filter_lower', type=float, default=None, 
      action='store', help='filter the metric using a lower percentile threshold (inclusive)')
  parser.add_argument('--filter-upper', dest='filter_upper', type=float, default=None, 
      action='store', help='filter the metric using am upper percentile threshold (inclusive)')

  subparsers = parser.add_subparsers(dest='segmentation_type')

  subparser1 = subparsers.add_parser('percentiles')
  subparser1.add_argument('percentiles', type=float, nargs='+', default=[0,25,50,75,100], 
      action='store', help='percentile bands, a space-separated list of numbers [0..100]. Default: 0 25 50 75 100 (quartiles)')
  subparser1.add_argument('--cumsum', dest='cumsum', default=False, 
    action='store_true', help='determine percentile thresholds based on the cumulative sum of observations, not their count')

  subparser2 = subparsers.add_parser('jenks')
  subparser2.add_argument('num_breaks', type=int, action='store', help='number of breaks')
  # subparser2.add_argument('--min-percentile', dest='min_percentile', type=float, default=None, 
  #     action='store', help='minimum percentile of the data to include')
  # subparser2.add_argument('--max-percentile', dest='max_percentile', type=float, default=None, 
  #     action='store', help='maximum percentile of the data to include')

  subparser3 = subparsers.add_parser('shrinking-percentiles')
  subparser3.add_argument('num_breaks', type=int, action='store', help='number of breaks')
  subparser3.add_argument('--min-percentile', dest='min_percentile', type=float, default=0, 
      action='store', help='minimum percentile of the data to include')
  subparser3.add_argument('--max-percentile', dest='max_percentile', type=float, default=100, 
      action='store', help='maximum percentile of the data to include')

  subparser4 = subparsers.add_parser('head-tail')
  subparser4.add_argument('num_breaks', type=int, action='store', help='number of breaks')
  # subparser4.add_argument('--min-percentile', dest='min_percentile', type=float, default=0, 
  #     action='store', help='minimum percentile of the data to include')
  # subparser4.add_argument('--max-percentile', dest='max_percentile', type=float, default=100, 
  #     action='store', help='maximum percentile of the data to include')

  args = parser.parse_args()

  # getDb().echo = True
  session = getSession()

  #
  # Overwrite check
  #
  
  row = session.execute("""SELECT count(*) as total FROM %s.region_user_segment 
      WHERE scheme='%s'""" % (args.schema, args.scheme_name)).fetchone()

  if row['total'] > 0:
    if args.overwrite:
      session.execute("""DELETE FROM %s.region_user_segment 
        WHERE scheme='%s'""" % (args.schema, args.scheme_name))
    else:
      print "Error: the segmentation scheme '%s' already exists!" % (args.scheme_name)
      sys.exit(1)

  #
  # Load data
  #
  
  query = """SELECT r.name AS region, %s FROM %s.user_edit_stats s 
    JOIN region r ON s.region_id=r.id""" % (args.metric, args.schema)
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
  # Filtering
  #

  # region -> threshold
  filter_min = dict()
  filter_max = dict()
  
  if args.filter_lower:
    print "Filtering: %s >= %.3f%%" % (args.metric, args.filter_lower)
    for region in regions:
      values = data[region]
      filter_min[region] = percentile(values, [args.filter_lower])[0]
      data[region] = [val for val in data[region] if val>=filter_min[region]]
      print "  region '%s': %s >= %d" % (region, args.metric, filter_min[region])

  if args.filter_upper:
    print "Filtering: %s <= %.3f" % (args.metric, args.filter_upper)
    for region in regions:
      values = data[region]
      filter_max[region] = percentile(values, [args.filter_upper])[0]
      data[region] = [val for val in data[region] if val<=filter_max[region]]
      print "  region '%s': %s <= %d" % (region, args.metric, filter_max[region])
  
  #
  # Get bands per region
  #
  
  band_thresholds = dict()
  for region in regions:
    band_thresholds[region] = defaultdict(list)
  
  for region in regions:
    # print region
    values = data[region]

    # calculate thresholds
    if args.segmentation_type=='percentiles':
      if args.cumsum:
        # percentiles of the cumulative sum
        thresholds = sorted(cumsum_percentile(values, args.percentiles))
      else:
        # classic percentiles
        thresholds = sorted(percentile(values, args.percentiles))
    elif args.segmentation_type=='jenks':
      # jenks natural breaks
      thresholds = sorted(get_jenks_breaks(values, args.num_breaks))
    elif args.segmentation_type=='shrinking-percentiles':
      # poor man's 2:1 iterative segmentation
      bands = get_shrinking_percentile_bands(args.min_percentile, args.max_percentile, args.num_breaks)
      thresholds = sorted(percentile(values, bands))
    elif args.segmentation_type=='head-tail':
      thresholds = sorted(get_head_tail_breaks(values, args.num_breaks))

    print "%s: %s" % (region, str(thresholds))
    
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

    query = """INSERT INTO %s.region_user_segment(region_id, scheme, uid, groupid) 
      SELECT r.id, '%s', uid, 
      CASE %s END
      FROM %s.user_edit_stats ues
      JOIN region r ON ues.region_id=r.id
      WHERE r.name='%s'
      """ % (args.schema, args.scheme_name, band_expr, args.schema, region)

    if min_threshold and min_threshold>=min(values):
      print "Filtering the bottom band for region '%s': %s > %f" % (region, args.metric, min_threshold)
      query += " AND %s > %f" % (args.metric, min_threshold)

    if max_threshold<max(values):
      print "Filtering the top band for region '%s': %s <= %f" % (region, args.metric, max_threshold)
      query += " AND %s <= %f" % (args.metric, max_threshold)
    
    if region in filter_min and filter_min[region]:
      query += " AND %s >= %f" % (args.metric, filter_min[region])
    if region in filter_max and filter_max[region]:
      query += " AND %s <= %f" % (args.metric, filter_max[region])

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
      FROM %s.region_user_segment seg
      JOIN %s.user_edit_stats ues ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)
      JOIN region r ON seg.region_id=r.id
      WHERE seg.scheme='%s'
      GROUP BY r.name, scheme, groupid
      ORDER BY r.name, scheme, groupid""" % (args.metric, args.schema, args.schema, args.scheme_name))

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
  