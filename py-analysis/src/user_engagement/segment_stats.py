#
# Summary stats for the groups of a user segmentation scheme.
#

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

# summarisation of bands

def mean(numbers):
  # return decimal.Decimal(sum(numbers)) / decimal.Decimal(len(numbers))
  return numpy.mean([float(n) for n in numbers])

def median(numbers):
  return numpy.median([float(n) for n in numbers])

group_summary = median

# values: ordered list of values
# groupids: a list of same order+size, associates a group ID with every value
# group: the ID of the group we're interested in
# -> unpacks all this and returns all values for the specified metric and group
def get_metric_for_group(values, groupids, group):
  return [value for idx, value in enumerate(values) if groupids[idx]==group]

# =========
# = Plots =
# =========

# data is a mapping of column -> row -> groupid -> value
def group_volume_plot(data, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_MEDIUM, **kwargs):
  
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 1.7*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      colidx = 0
      left = 0
      total = decimal.Decimal(sum(data[column][row].values()))
      for groupid in sorted(data[column][row].keys()):
        col = colors[colidx]
        colidx = (colidx+1) % len(colors)
        val = data[column][row][groupid] / total
        ax1.barh(0, val, 1, left=left, color=col, **kwargs)
        left += val

      # ax1.get_xaxis().set_visible(False)
      ax1.get_yaxis().set_ticks([])

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data is a mapping of column -> row -> list of items (values)
# item_groupids is a mapping of column -> list of groupids, one per item
# kwargs is passed on to plt.scatter(...).
def group_scatterplot(data, anchor_row, item_groupids, columns, rows, outdir, 
  filename_base, colors=QUALITATIVE_DARK, **kwargs):
  
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      group_x = defaultdict(list)
      group_y = defaultdict(list)

      for idx in range(len(item_groupids[column])):
        groupid = item_groupids[column][idx]
        x = data[column][anchor_row][idx]
        y = data[column][row][idx]
        if (x>0 and y>0): # when using log scale...
          group_x[groupid].append(x)
          group_y[groupid].append(y)

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      colidx = 0
      for groupid in sorted(group_x.keys()):
        col = colors[colidx]
        colidx = (colidx+1) % len(colors)
        ax1.scatter(group_x[groupid], group_y[groupid], color=col, **kwargs)

      ax1.set_xscale('log')
      ax1.set_yscale('log')
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data is a mapping of column -> row -> group -> list of values
# kwargs is passed on to plt.boxplot(...).
def group_boxplot(data, columns, rows, outdir, filename_base, plot_means=False **kwargs):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(3*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      celldata = []
      for groupid in sorted(data[column][row].keys()):
        # boxplot / mlab bug: can't deal with Decimal types
        celldata.append([float(v) for v in data[column][row][groupid]]) 
        # print data[column][row][groupid]

      ax1.boxplot(celldata, **kwargs)

      if plot_means:
        means = [numpy.mean(x) for x in celldata]
        ax1.scatter(range(1, len(celldata)+1), means, marker='x', color='r')

      ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
      ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
      ax1.tick_params(axis='y', which='major', labelsize='x-small')
      ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
      ax1.get_xaxis().set_visible(False)

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')


# data is a mapping of column -> row -> group -> value
# kwargs is passed on to plt.bar(...).
def group_scores_plot(data, columns, rows, outdir, filename_base, colors=QUALITATIVE_MEDIUM, **kwargs):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(3*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      celldata = []
      for groupid in sorted(data[column][row].keys()):
        celldata.append(data[column][row][groupid])

      ax1.bar(range(1, len(celldata)+1), celldata, color=colors, **kwargs)

      ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
      ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
      ax1.tick_params(axis='y', which='major', labelsize='x-small')
      ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
      ax1.get_xaxis().set_visible(False)

      n += 1
  
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
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove',
    'days_active', 'lifespan_days']
  user_scores = ['poi_edit_score', 'tag_edit_score', 'tag_removal_score', 'edit_pace']
  
  data = defaultdict(lambda: defaultdict(list)) # region -> metric -> list of user values
  region_users = defaultdict(set)     # region -> set of uids
  region_num_edits = defaultdict(int) # region -> num_edits
  user_groups = defaultdict(list)     # region -> list of user groups
  
  # User scores. region -> group -> list of values
  poi_edit_score = defaultdict(lambda: defaultdict(list)) 
  tag_edit_score = defaultdict(lambda: defaultdict(list))
  tag_removal_score = defaultdict(lambda: defaultdict(list))
  edit_pace = defaultdict(lambda: defaultdict(list))

  # Group scores. region -> group -> value
  group_num_users = defaultdict(lambda: defaultdict(int)) 
  group_num_edits = defaultdict(lambda: defaultdict(int))

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, seg.groupid as groupid, seg.uid as uid, %s,
    1.0 * (num_poi_edited + 1)/(num_poi_created + 1) as poi_edit_score, 
    1.0 * (num_tag_update + 1)/(num_tag_add + 1) as tag_edit_score, 
    1.0 * (num_tag_remove + 1)/(num_tag_add + 1) as tag_removal_score,
    1.0 * num_edits / days_active as edit_pace
    FROM %s.region_user_segment seg
    JOIN %s.user_edit_stats ues ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)
    JOIN region r ON seg.region_id=r.id
    WHERE seg.scheme='%s'""" % (', '.join(metrics), args.schema, args.schema, args.scheme_name))
  # print result.keys()

  num_records = 0
  for row in result:
    region = row['region']
    groupid = row['groupid']

    for metric in metrics:
      data[region][metric].append(row[metric])

    region_users[region].add(row['uid'])
    region_num_edits[region] += row['num_edits']
    user_groups[region].append(groupid)

    poi_edit_score[region][groupid].append(row['poi_edit_score'])
    tag_edit_score[region][groupid].append(row['tag_edit_score'])
    tag_removal_score[region][groupid].append(row['tag_removal_score'])
    edit_pace[region][groupid].append(row['edit_pace'])
    
    group_num_users[region][groupid] += 1
    group_num_edits[region][groupid] += row['num_edits']

    num_records += 1

  print "Loaded %d records." % (num_records)

  regions = sorted(data.keys())

  groups = dict() # region -> group IDs
  for region in regions:
    groups[region] = set(user_groups[region])
  
  #
  # Compute derived scores
  #

  # region -> group -> aggregate score
  edits_per_user = defaultdict(dict)
  group_poi_edit_score = defaultdict(dict)
  group_tag_edit_score = defaultdict(dict)
  group_tag_removal_score = defaultdict(dict)
  group_edit_pace = defaultdict(dict)
  
  for region in regions:
    for groupid in groups[region]:
      num_users = group_num_users[region][groupid]
      num_edits = group_num_edits[region][groupid]
      # edits_per_user[region][groupid] = decimal.Decimal(num_edits) / decimal.Decimal(num_users)
      edits_per_user[region][groupid] = group_summary(get_metric_for_group(
        data[region][metric], user_groups[region], groupid))
      group_poi_edit_score[region][groupid] = group_summary(poi_edit_score[region][groupid])
      group_tag_edit_score[region][groupid] = group_summary(tag_edit_score[region][groupid])
      group_tag_removal_score[region][groupid] = group_summary(tag_removal_score[region][groupid])
      group_edit_pace[region][groupid] = group_summary(edit_pace[region][groupid])

  #
  # Report
  #
  
  mkdir_p(args.outdir)
  
  filename = "%s/segments_%s_stats.txt" % (args.outdir, args.scheme_name)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(['region', 'scheme', 'groupid', 
    'num_users', 'perc_users', 
    'num_edits', 'perc_edits',
    'edits_per_user', 
    'group_poi_edit_score', 'group_tag_edit_score', 'group_tag_removal_score', 
    'group_edit_pace'])
  
  for region in regions:
    for groupid in groups[region]:
      num_users = group_num_users[region][groupid]
      num_edits = group_num_edits[region][groupid]
  
      outcsv.writerow([
        region, args.scheme_name, groupid,
        num_users, 100 * decimal.Decimal(num_users) / len(region_users[region]),
        num_edits, 100 * decimal.Decimal(num_edits) / region_num_edits[region],
        edits_per_user[region][groupid],
        group_poi_edit_score[region][groupid],
        group_tag_edit_score[region][groupid],
        group_tag_removal_score[region][groupid],
        group_edit_pace[region][groupid]])

  #
  # Volume plot
  # 
  
  volume_data = dict()
  for region in regions:
    volume_data[region] = dict()
    volume_data[region]['num_users'] = group_num_users[region]
    volume_data[region]['num_edits'] = group_num_edits[region]
  
  group_volume_plot(volume_data, regions, ['num_users', 'num_edits'], 
    args.outdir, 'volume_%s' % (args.scheme_name))

  #
  # Scatter plot
  #
  
  group_scatterplot(data, 'num_edits', user_groups, regions, metrics, 
    args.outdir, 'scatter_num_edits_%s' % (args.scheme_name))
  
  group_scatterplot(data, 'days_active', user_groups, regions, metrics, 
    args.outdir, 'scatter_days_active_%s' % (args.scheme_name))
  
  #
  # Scores boxlot
  #
  
  group_data = dict()
  for region in regions:
    group_data[region] = dict()
    group_data[region]['edits_per_user'] = edits_per_user[region]
    group_data[region]['poi_edit_score'] = poi_edit_score[region]
    group_data[region]['tag_edit_score'] = tag_edit_score[region]
    group_data[region]['tag_removal_score'] = tag_removal_score[region]
    group_data[region]['edit_pace'] = edit_pace[region]
  
  group_boxplot(group_data, regions, ['poi_edit_score', 'tag_edit_score', 
    'tag_removal_score', 'edit_pace'], 
    args.outdir, 'boxplot_%s' % (args.scheme_name))

  group_boxplot(group_data, regions, ['poi_edit_score', 'tag_edit_score', 
    'tag_removal_score', 'edit_pace'], 
    args.outdir, 'boxplot_no-fliers_%s' % (args.scheme_name), sym='')
    
  
  #
  # Scores plot
  # 

  scores_data = dict()
  for region in regions:
    scores_data[region] = dict()
    scores_data[region]['edits_per_user'] = edits_per_user[region]
    scores_data[region]['group_poi_edit_score'] = group_poi_edit_score[region]
    scores_data[region]['group_tag_edit_score'] = group_tag_edit_score[region]
    scores_data[region]['group_tag_removal_score'] = group_tag_removal_score[region]
    scores_data[region]['group_edit_pace'] = group_edit_pace[region]
  
  group_scores_plot(scores_data, regions, 
    ['edits_per_user', 'group_poi_edit_score', 'group_tag_edit_score', 
    'group_tag_removal_score', 'group_edit_pace'], 
    args.outdir, 'scores_%s' % (args.scheme_name))
