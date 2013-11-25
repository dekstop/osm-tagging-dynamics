#
# Summary stats for the groups of a user segmentation scheme.
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

# =========
# = Tools =
# =========

def mean(numbers):
  # return decimal.Decimal(sum(numbers)) / decimal.Decimal(len(numbers))
  return numpy.mean([float(n) for n in numbers])

def median(numbers):
  return numpy.median([float(n) for n in numbers])

group_summary = median

# ===========
# = Reports =
# ===========

# region -> group -> dict of aggregate scores
# volume_data: region -> groupid -> dict of {num_users, num_poi_edits}
# scores: list of score names
def report_scores(data, volume_data, scores, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([
    'region', 'groupid', 
    'num_users', 'perc_users', 
    'num_poi_edits', 'perc_poi_edits'] + scores)
  
  for region in sorted(data.keys()):
    region_num_users = sum([volume_data[region][groupid]['num_users'] for groupid in volume_data[region].keys()])
    region_num_poi_edits = sum([volume_data[region][groupid]['num_poi_edits'] for groupid in volume_data[region].keys()])

    for groupid in sorted(data[region].keys()):
      num_users = volume_data[region][groupid]['num_users']
      num_poi_edits = volume_data[region][groupid]['num_poi_edits']
  
      outcsv.writerow([
        region, groupid,
        num_users, 100 * decimal.Decimal(num_users) / region_num_users,
        num_poi_edits, 100 * decimal.Decimal(num_poi_edits) / region_num_poi_edits] +
        [data[region][groupid][score] for score in scores])
  
  outfile.close()

# region -> group -> list of records, each a dict of scores
# volume_data: region -> groupid -> dict of {num_users, num_poi_edits}
# scores: list of score names
def report_variances(data, volume_data, scores, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([
    'region', 'groupid', 
    'num_users', 'perc_users', 
    'num_poi_edits', 'perc_poi_edits'] + ['var_'+score for score in scores])
  
  for region in sorted(data.keys()):
    region_num_users = sum([volume_data[region][groupid]['num_users'] for groupid in volume_data[region].keys()])
    region_num_poi_edits = sum([volume_data[region][groupid]['num_poi_edits'] for groupid in volume_data[region].keys()])

    for groupid in sorted(data[region].keys()):
      num_users = volume_data[region][groupid]['num_users']
      num_poi_edits = volume_data[region][groupid]['num_poi_edits']
  
      outcsv.writerow([
        region, groupid,
        num_users, 100 * decimal.Decimal(num_users) / region_num_users,
        num_poi_edits, 100 * decimal.Decimal(num_poi_edits) / region_num_poi_edits] +
        [numpy.var(
          [data[region][groupid][idx][score] 
            for idx in range(len(data[region][groupid]))]) 
          for score in scores])
  
  outfile.close()

# =========
# = Plots =
# =========

# data: column -> segment -> row -> value
# kwargs is passed on to plt.barh(...).
def group_volume_plot(data, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):
  
  for (column, row, ax1) in plot_matrix(columns, rows, cellwidth=4, cellheight=1.7):
    left = 0
    total = sum([data[column][seg][row] for seg in data[column].keys()])
    colgen = looping_generator(colors)
    for segment in sorted(data[column].keys()):
      val = data[column][segment][row] / decimal.Decimal(total)
      ax1.barh(0, val, 1, left=left, color=next(colgen), **kwargs)
      left += val

    ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(to_even_percent))
    ax1.get_yaxis().set_ticks([])
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: column -> segment -> row -> value
# kwargs is passed on to plt.bar(...).
def group_scores_plot(data, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):

  for (column, row, ax1) in plot_matrix(columns, rows):
    celldata = []
    for segment in sorted(data[column].keys()):
      celldata.append(data[column][segment][row] + 0.0001) # got some 0 values...

    ax1.bar(range(1, len(celldata)+1), celldata, color=colors, **kwargs)

    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: column -> segment -> list of records (each a dict or row values)
# kwargs is passed on to plt.boxplot(...).
def item_scores_boxplot(data, columns, rows, outdir, filename_base, **kwargs):
  for (column, row, ax1) in plot_matrix(columns, rows):
    celldata = []
    for segment in sorted(data[column].keys()):
      nrecs = len(data[column][segment])
      celldata.append([data[column][segment][idx][row] for idx in range(nrecs)])
    ax1.boxplot(celldata, **kwargs)

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: column -> segment -> list of records (each a dict or row values)
# kwargs is passed on to plt.step(...).
def item_rank_plot(data, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_DARK, x_gap=0.2, **kwargs):
  
  for (column, row, ax1) in plot_matrix(columns, rows):
    # horizontal spacing
    num_items = sum([len(data[column][segment]) for segment in data[column].keys()])
    num_groups = len(data[column].keys())
    x_spacing = int(num_items * x_gap / (num_groups-1)) # Python2 round(...) returns a float

    xoffset = 0
    colgen = looping_generator(colors)
    for segment in sorted(data[column].keys()):
      nrecs = len(data[column][segment])
      values = sorted([data[column][segment][idx][row] for idx in range(nrecs)])

      ax1.step(range(xoffset, xoffset+len(values)), values, 
        color=next(colgen), linewidth=2, **kwargs)
      xoffset += len(values) + x_spacing

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: column -> segment -> list of records (each a dict or row values)
# kwargs is passed on to plt.scatter(...).
def items_scatterplot(data, anchor_row, columns, rows, outdir, 
  filename_base, colors=QUALITATIVE_DARK, scale='log', **kwargs):
  
  for (column, row, ax1) in plot_matrix(columns, rows):
    seg_x = defaultdict(list)
    seg_y = defaultdict(list)

    for segment in sorted(data[column].keys()):
      for rec in data[column][segment]:
        x = rec[anchor_row]
        y = rec[row]
        if (x>0 and y>0): # we're using log scale...
          seg_x[segment].append(x)
          seg_y[segment].append(y)

    colgen = looping_generator(colors)
    for segment in sorted(seg_x.keys()):
      ax1.scatter(seg_x[segment], seg_y[segment], color=next(colgen), **kwargs)

    ax1.set_xscale(scale)
    ax1.set_yscale(scale)
    ax1.tick_params(axis='both', which='major', labelsize='x-small')
    ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Summary stats for the groups of a user segmentation scheme.')
  parser.add_argument('scheme_name', help='name of the segmentation scheme')
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
  # Aggregated group scores
  #
  
  # region -> group -> dict of aggregate scores
  group_scores = defaultdict(lambda: defaultdict(dict))
  for region in regions:
    for groupid in data[region].keys():
      for score in scores:
        values = [rec[score] for rec in data[region][groupid]]
        group_scores[region][groupid][score] = group_summary(values)

  # 
  # Projections for plotting
  #
  
  # region -> groupid -> dict of {num_users, num_poi_edits}
  volume_data = defaultdict(lambda: defaultdict(dict))
  for region in regions:
    for groupid in data[region].keys():
      users = [rec['uid'] for rec in data[region][groupid]]
      volume_data[region][groupid]['num_users'] = len(set(users))

      num_poi_edits = [rec['num_poi_edits'] for rec in data[region][groupid]]
      volume_data[region][groupid]['num_poi_edits'] = sum(num_poi_edits)

  #
  # Prep
  #
  
  mkdir_p(args.outdir)
  
  #
  # Report: group scores
  #
  
  report_scores(group_scores, volume_data, scores, 
    args.outdir, "report_%s" % (args.scheme_name))

  report_variances(data, volume_data, scores, 
    args.outdir, "report_%s_variances" % (args.scheme_name))

  #
  # Plots: aggregated group data
  # 
  
  group_volume_plot(volume_data, regions, ['num_users', 'num_poi_edits'], 
    args.outdir, 'volume_%s' % (args.scheme_name))

  group_scores_plot(group_scores, regions, scores, 
    args.outdir, 'scores_%s' % (args.scheme_name))

  #
  # Plots: individual user data
  # 
  
  item_scores_boxplot(data, regions, scores, 
    args.outdir, 'scores_boxplot_%s' % (args.scheme_name),
    sym='') # don't show fliers

  item_rank_plot(data, regions, scores,
    args.outdir, 'scores_rank_%s' % (args.scheme_name))

  item_rank_plot(data, regions, metrics, 
    args.outdir, 'metrics_rank_%s' % (args.scheme_name))

  items_scatterplot(data, 'num_poi_edits', regions, scores, 
    args.outdir, 'scores_scatter-lin_num_edits_%s' % (args.scheme_name), 
    scale='linear')
  
  items_scatterplot(data, 'num_poi_edits', regions, scores, 
    args.outdir, 'scores_scatter_num_edits_%s' % (args.scheme_name))
  
  items_scatterplot(data, 'days_active', regions, scores, 
    args.outdir, 'scores_scatter_days_active_%s' % (args.scheme_name))

  items_scatterplot(data, 'num_poi_edits', regions, metrics, 
    args.outdir, 'metrics_scatter_num_edits_%s' % (args.scheme_name))
  
  items_scatterplot(data, 'days_active', regions, metrics, 
    args.outdir, 'metrics_scatter_days_active_%s' % (args.scheme_name))
