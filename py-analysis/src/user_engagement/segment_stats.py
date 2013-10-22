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

def avg(numbers):
  return decimal.Decimal(sum(numbers)) / decimal.Decimal(len(numbers))

# =========
# = Plots =
# =========

# data is a mapping of column -> row -> list of items (values)
# item_groupids is a mapping of column -> list of groupids, one per item
# kwargs is passed on to plt.scatter(...).
def plot_group_scatter(data, anchor_row, item_groupids, columns, rows, outdir, filename_base, **kwargs):
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

      colors = ['b', 'c', 'm', 'y', 'r', 'k']
      for groupid in group_x.keys(): #sorted(group_x.keys(), reverse=True):
        col = colors.pop(0)
        ax1.scatter(group_x[groupid], group_y[groupid], color=col, **kwargs)

      ax1.set_xscale('log')
      ax1.set_yscale('log')
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data is a mapping of column -> row -> group -> value
# kwargs is passed on to plt.scatter(...).
def plot_group_scores(data, columns, rows, outdir, filename_base, **kwargs):
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

      colors = ['b', 'c', 'm', 'y', 'r', 'k']
      celldata = []
      for groupid in sorted(data[column][row].keys()):
        celldata.append(data[column][row][groupid])

      ax1.bar(range(1, len(celldata)+1), celldata, color=colors, **kwargs)

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
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove']
  user_scores = ['poi_edit_score', 'tag_edit_score', 'tag_removal_score']
  
  data = defaultdict(lambda: defaultdict(list)) # region -> metric -> list of user values
  region_users = defaultdict(set)    # region -> set of uids
  region_num_edits = defaultdict(int)      # region -> num_edits
  user_groups = defaultdict(list) # region -> list of user groups
  
  # User scores. region -> group -> list of values
  poi_edit_score = defaultdict(lambda: defaultdict(list)) 
  tag_edit_score = defaultdict(lambda: defaultdict(list))
  tag_removal_score = defaultdict(lambda: defaultdict(list))

  # Group scores. region -> group -> value
  group_num_users = defaultdict(lambda: defaultdict(int)) 
  group_num_edits = defaultdict(lambda: defaultdict(int))

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, seg.groupid as groupid, seg.uid as uid, %s,
    1.0 * (num_poi_edited + 1)/(num_poi_created + 1) as poi_edit_score, 
    1.0 * (num_tag_update + 1)/(num_tag_add + 1) as tag_edit_score, 
    1.0 * (num_tag_remove + 1)/(num_tag_add + 1) as tag_removal_score
    FROM sample_1pc.region_user_segment seg
    JOIN sample_1pc.user_edit_stats ues ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)
    JOIN region r ON seg.region_id=r.id
    WHERE seg.scheme='%s'""" % (', '.join(metrics), args.scheme_name))
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

  edits_per_user = defaultdict(dict)        # region -> group -> aggregate score
  avg_poi_edit_score = defaultdict(dict)    # region -> group -> aggregate score
  avg_tag_edit_score = defaultdict(dict)    # region -> group -> aggregate score
  avg_tag_removal_score = defaultdict(dict) # region -> group -> aggregate score
  
  for region in regions:
    for groupid in groups[region]:
      num_users = group_num_users[region][groupid]
      num_edits = group_num_edits[region][groupid]
      edits_per_user[region][groupid] = decimal.Decimal(num_edits) / decimal.Decimal(num_users)
      avg_poi_edit_score[region][groupid] = avg(poi_edit_score[region][groupid])
      avg_tag_edit_score[region][groupid] = avg(tag_edit_score[region][groupid])
      avg_tag_removal_score[region][groupid] = avg(tag_removal_score[region][groupid])

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
    'avg_poi_edit_score', 'avg_tag_edit_score', 'avg_tag_removal_score'])
  
  for region in regions:
    for groupid in groups[region]:
      num_users = group_num_users[region][groupid]
      num_edits = group_num_edits[region][groupid]

      outcsv.writerow([
        region, args.scheme_name, groupid,
        num_users, 100 * decimal.Decimal(num_users) / len(region_users[region]),
        num_edits, 100 * decimal.Decimal(num_edits) / region_num_edits[region],
        edits_per_user[region][groupid],
        avg_poi_edit_score[region][groupid],
        avg_tag_edit_score[region][groupid],
        avg_tag_removal_score[region][groupid]])

  #
  # Scatter plot
  #
  
  # plot_group_scatter(data, 'num_edits', user_groups, regions, metrics, 
    # args.outdir, 'scatter_num_edits_%s' % (args.scheme_name))
  
  #
  # Scores plot
  # 

  scores_data = dict()
  for region in regions:
    scores_data[region] = dict()
    scores_data[region]['edits_per_user'] = edits_per_user[region]
    scores_data[region]['avg_poi_edit_score'] = avg_poi_edit_score[region]
    scores_data[region]['avg_tag_edit_score'] = avg_tag_edit_score[region]
    scores_data[region]['avg_tag_removal_score'] = avg_tag_removal_score[region]
  
  plot_group_scores(scores_data, regions, 
    ['edits_per_user', 'avg_poi_edit_score', 'avg_tag_edit_score', 'avg_tag_removal_score'], 
    args.outdir, 'scores_%s' % (args.scheme_name))
