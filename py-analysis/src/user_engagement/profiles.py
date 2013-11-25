#
# Profiles of regional editing behaviour.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import sys

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy

from app import *

# ===========
# = Reports =
# ===========

# data: region -> score -> value
# vardata: region -> score -> variance
# scores: list of score names
def report_region_scores(data, vardata, regions, scores, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(['region'] + scores + ['var_'+score for score in scores])
  for region in regions:
    outcsv.writerow([region] +
      [data[region][score] for score in scores] +
      [vardata[region][score] for score in scores])
  outfile.close()

# region_segment_weight: region -> segment -> score -> value
def report_region_segment_weights(data, regions, scores,
    outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(['region', 'groupid'] + scores)
  for region in regions:
    for segment in data[region].keys():
      outcsv.writerow([region, segment] +
        [data[region][segment][score] for score in scores])
  outfile.close()

# =========
# = Plots =
# =========

# data: column -> segment -> row -> value
# kwargs is passed on to plt.bar(...).
def group_scores_plot(data, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):

  for (column, row, ax1) in plot_matrix(columns, rows):
    celldata = []
    for segment in sorted(data[column].keys()):
      celldata.append(data[column][segment][row] + 0.0001) # got some 0 values...

    ax1.bar(range(1, len(celldata)+1), celldata, color=colors, **kwargs)

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
    
    minv = min(celldata)
    maxv = max(celldata)
    vrange = max(abs(minv), abs(maxv))
    ax1.set_ylim([-vrange, vrange])
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Profiles of regional editing behaviour.')
  parser.add_argument('scheme_name', help='name of the segmentation scheme')
  parser.add_argument('anchor_metric', help='name of the engagement metric used as independent variable in regression analyses')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--schema', dest='schema', type=str, default='public', 
      action='store', help='parent schema that contains data tables. Default: public')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = [
    'num_poi', 'num_poi_edits', 'num_poi_add', 'num_poi_update', 
    'num_tag_edits', 'num_tag_add', 'num_tag_update', 'num_tag_remove', 
    # 'num_tag_keys', 'num_changesets', 
    'days_active', 'lifespan_days']
  scores = [
    'poi_add_score', 'poi_update_score', 
    'tag_add_score', 'tag_update_score', 'tag_remove_score', 
    'iteration_score', # 1 - num_poi / num_poi_edits
    'activity_score' # days_active / lifespan_days
    ]
  
  # region -> group -> list of user records (each a dict of metrics/scores)
  data = defaultdict(lambda: defaultdict(list)) 

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, seg.groupid as groupid, seg.uid as uid, %s
    FROM %s.region_user_segment seg
    JOIN %s.user_edit_stats ues ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)
    JOIN region r ON seg.region_id=r.id
    WHERE seg.scheme='%s'""" % (', '.join(metrics), args.schema, args.schema, args.scheme_name))
  # print result.keys()

  num_records = 0
  for row in result:
    record = dict()
    record['uid'] = row['uid']
    for metric in metrics:
      record[metric] = row[metric]
    
    record['poi_add_score'] = row['num_poi_add'] / row['num_poi_edits']
    record['poi_update_score'] = row['num_poi_update'] / row['num_poi_edits']
    record['tag_add_score'] = row['num_tag_add'] / row['num_tag_edits']
    record['tag_update_score'] = row['num_tag_update'] / row['num_tag_edits']
    record['tag_remove_score'] = row['num_tag_remove'] / row['num_tag_edits']
    record['iteration_score'] = 1 - (row['num_poi'] / row['num_poi_edits'])
    record['activity_score'] = row['days_active'] / row['lifespan_days']
    
    region = row['region']
    groupid = row['groupid']
    data[region][groupid].append(record)

    num_records += 1

  print "Loaded %d records." % (num_records)

  # matrix columns
  regions = sorted(data.keys())

  #
  # Prep
  #
  
  mkdir_p(args.outdir)
  
  #
  # Region summary scores
  # 
  
  # region -> score -> value
  region_scores = defaultdict(dict)
  region_var = defaultdict(dict)
  for score in scores:
    for region in regions:
      region_data = [rec for segment in data[region].values() for rec in segment] # merge segments
      values = [region_data[idx][score] for idx in range(len(region_data))] 
      region_scores[region][score] = numpy.median(values)
      region_var[region][score] = numpy.var(values)
  
  report_region_scores(region_scores, region_var, regions, scores, 
    args.outdir, 'region_scores_%s' % (args.scheme_name))
  
  #
  # Region segment tendencies compared to region population tendency
  # 
  
  # region -> band -> score -> value
  region_segment_weight = defaultdict(lambda: defaultdict(dict))
  for score in scores:
    for region in regions:
      region_data = [rec for segment in data[region].values() for rec in segment] # merge segments
      region_values = [region_data[idx][score] for idx in range(len(region_data))] 
      region_median = numpy.median(region_values)
      
      for groupid in data[region].keys():
        nrecs = len(data[region][groupid])
        group_values = [data[region][groupid][idx][score] for idx in range(nrecs)]
        group_median = numpy.median(group_values)
        weight = group_median - region_median
        region_segment_weight[region][groupid][score] = weight

  report_region_segment_weights(region_segment_weight, regions, scores, 
    args.outdir, 'region_segment_weights_%s' % (args.scheme_name))
  
  group_scores_plot(region_segment_weight, regions, scores, 
    args.outdir, 'region_segment_weights_%s' % (args.scheme_name))
