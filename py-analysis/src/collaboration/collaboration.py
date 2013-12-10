#
# Statistics relating to collaborative editing practices.
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

# data: country -> is_poweruser -> metric -> list of values
def report(data, col1name, col2name, metrics, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([col1name, col2name] + metrics)
  
  for region in sorted(data.keys()):
    for groupid in sorted(data[region].keys()):
      for idx in range(len(data[region][groupid][metrics[0]])):
        outcsv.writerow([region, groupid] +
          [data[region][groupid][metric][idx] for metric in metrics])
  
  outfile.close()

# =========
# = Plots =
# =========

# data: country -> is_poweruser -> metric -> list of values
# kwargs is passed on to plt.boxplot(...).
def items_boxplot(data, columns, rows, outdir, filename_base, **kwargs):
  for (column, row, ax1) in plot_matrix(columns, rows):
    celldata = []
    for segment in sorted(data[column].keys()):
      celldata.append(data[column][segment][row])
    ax1.boxplot(celldata, **kwargs)

    ax1.margins(0.1, 0.1)
    ax1.get_xaxis().set_visible(False)
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.tick_params(axis='y', which='major', labelsize='x-small')
    ax1.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: country -> is_poweruser -> metric -> list of values
# kwargs is passed on to plt.boxplot(...).
def items_scatterplot(data, anchor_row, columns, rows, outdir, filename_base, 
  colors=QUALITATIVE_DARK, scale='log',**kwargs):
  
  for (column, row, ax1) in plot_matrix(columns, rows):
    seg_x = defaultdict(list)
    seg_y = defaultdict(list)

    for segment in sorted(data[column].keys()):
      seg_x[segment] = data[column][segment][anchor_row]
      seg_y[segment] = data[column][segment][row]
      #  if (x>0 and y>0): # we're using log scale...
      #    seg_x[segment].append(x)
      #    seg_y[segment].append(y)

    colgen = looping_generator(colors)
    for segment in sorted(seg_x.keys()):
      ax1.scatter(seg_x[segment], seg_y[segment], color=next(colgen), **kwargs)

    ax1.margins(0.1, 0.1)
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
  parser = argparse.ArgumentParser(description='Statistics relating to collaborative editing practices.')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--min-edits', help='minimum number of edits per user and region', dest='min_edits', action='store', type=int, default=None)
  parser.add_argument('--max-edits', help='maximum number of edits per user and region', dest='max_edits', action='store', type=int, default=None)
  parser.add_argument('--min-poweruser-edits', help='number of edits per user and region to be regarded a power user', dest='min_poweruser_edits', action='store', type=int, default=100)
  parser.add_argument('--countries', help='list of country names', dest='countries', nargs='+', action='store', type=str, default=None)
  args = parser.parse_args()

  #
  # Get data
  #

  edits_metrics = ['num_poi_edits', 'num_tag_add', 'num_tag_update', 'num_tag_remove']
  editors_metrics = ['num_poi_edits', 'num_sol_edits', 'num_col_edits', 'num_tag_add', 'num_tag_update', 'num_tag_remove']
  editor_scores = ['col_rate', 'col_add_rate', 'col_update_rate', 'col_remove_rate']

  country_join = ""
  if args.countries and len(args.countries)>0:
    country_join = """JOIN world_borders w1 ON wp.country_gid=w1.gid
      WHERE w1.name IN ('%s')""" % ("', '".join(args.countries))

  user_filter_join = ""
  if args.min_edits or args.max_edits:
    user_filter_join = """JOIN (
      SELECT country_gid, uid 
      FROM user_edit_stats
      GROUP BY country_gid, uid
      HAVING sum(num_poi_edits) >= %d""" % (args.min_edits or 0)
    if args.max_edits:
      user_filter_join += """
      AND sum(num_poi_edits) < %d""" % (args.max_edits)
    user_filter_join += """) uf ON (u.country_gid=uf.country_gid AND u.uid=uf.uid)"""

  #getDb().echo = True    
  session = getSession()
  
  # Edits
  edits_query = """SELECT w.name as country, u.uid as uid,
      CASE
        WHEN ue.num_poi_edits>=%d THEN TRUE
        ELSE FALSE
      END as is_poweruser,
      %s
    FROM (SELECT wp.country_gid, uid 
      FROM poi p
      JOIN poi_multiple_editors m ON (p.id=m.poi_id AND p.version>=m.first_shared_version)
      JOIN world_borders_poi_latest wp ON (p.id=wp.poi_id)
      %s
      GROUP BY country_gid, uid) u
      %s
    JOIN user_edit_stats ue ON (u.country_gid=ue.country_gid AND u.uid=ue.uid AND ue.is_collab_work=true)
    JOIN world_borders w ON (u.country_gid=w.gid)
    """ % (args.min_poweruser_edits, ", ".join(edits_metrics), country_join, user_filter_join)
  
  # country -> is_poweruser -> metric -> list of values
  edits_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) 
  result = session.execute(edits_query)
  num_records = 0
  for row in result:
    for metric in edits_metrics:
      edits_data[row['country']][row['is_poweruser']][metric].append(row[metric])
    num_records += 1
  print "Loaded %d records." % (num_records)

  # Editors
  editors_query = """SELECT w.name as country, u1.uid as uid,
      CASE WHEN (num_sol_edits+num_col_edits)>=%d THEN TRUE ELSE FALSE END as is_poweruser,
      num_col_edits + num_sol_edits as num_poi_edits,
      num_col_edits,
      num_sol_edits,
      num_tag_add, num_tag_update, num_tag_remove,
      CASE 
        WHEN num_col_edits=0 AND num_sol_edits>0 THEN 0::numeric
        WHEN num_col_edits>0 AND num_sol_edits=0 THEN 1::numeric
        ELSE round(num_col_edits::numeric / (num_col_edits+num_sol_edits), 4)
      END as col_rate,
      num_tag_add::numeric / (num_col_edits+num_sol_edits) as col_add_rate,
      num_tag_update::numeric / (num_col_edits+num_sol_edits) as col_update_rate,
      num_tag_remove::numeric / (num_col_edits+num_sol_edits) as col_remove_rate
    FROM (
      SELECT
        coalesce(sol.country_gid, col.country_gid) AS country_gid,
        coalesce(sol.uid, col.uid) AS uid,
        coalesce(sol.num_poi_edits, 0) as num_sol_edits,
        coalesce(col.num_poi_edits, 0) as num_col_edits,
        u.num_tag_add, u.num_tag_update, u.num_tag_remove
      FROM (
        SELECT country_gid, uid, 
          sum(num_tag_add) as num_tag_add,
          sum(num_tag_update) as num_tag_update,
          sum(num_tag_remove) as num_tag_remove
        FROM user_edit_stats wp
        %s
        GROUP BY country_gid, uid) u
      %s
      LEFT OUTER JOIN user_edit_stats sol ON (u.uid=sol.uid AND u.country_gid=sol.country_gid AND sol.is_collab_work=false)
      LEFT OUTER JOIN user_edit_stats col ON (u.uid=col.uid AND u.country_gid=col.country_gid AND col.is_collab_work=true)
    ) u1
    JOIN world_borders w ON (u1.country_gid=w.gid)
    """ % (args.min_poweruser_edits, country_join, user_filter_join)
    
  # country -> is_poweruser -> metric -> list of values
  editors_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) 
  result = session.execute(editors_query)
  num_records = 0
  for row in result:
    for metric in editors_metrics:
      editors_data[row['country']][row['is_poweruser']][metric].append(row[metric])
    for metric in editor_scores:
      editors_data[row['country']][row['is_poweruser']][metric].append(row[metric])
    num_records += 1
  print "Loaded %d records." % (num_records)

  #
  # Prep
  #
  
  regions = sorted(set(edits_data.keys() + editors_data.keys()))
  mkdir_p(args.outdir)

  #
  # Reports
  #

  report(edits_data, 'country', 'is_poweruser', edits_metrics, args.outdir, "collab_edits")
  report(editors_data, 'country', 'is_poweruser', editors_metrics, args.outdir, "editors")
  report(editors_data, 'country', 'is_poweruser', editor_scores, args.outdir, "editor_scores")

  edits_summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
  editors_summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
  editor_scores_summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
  for region in regions:
    for is_poweruser in [False, True]:
      cell = edits_data[region][is_poweruser]
      edits_summary[region][is_poweruser]['num_users'] = [ len(cell['num_poi_edits']) ]
      for metric in edits_metrics:
        edits_summary[region][is_poweruser][metric] = [ sum(cell[metric]) ]
  
      cell = editors_data[region][is_poweruser]
      editors_summary[region][is_poweruser]['num_users'] = [ len(cell['num_poi_edits']) ]
      for metric in editors_metrics: # sum over users
        editors_summary[region][is_poweruser][metric] = [ sum(cell[metric]) ]
      editor_scores_summary[region][is_poweruser]['num_users'] = [ len(cell['num_poi_edits']) ]
      for metric in editor_scores: # average over users
        editor_scores_summary[region][is_poweruser][metric] = [ sum(cell[metric]) / len(cell[metric]) ]
  
  report(edits_summary, 'country', 'is_poweruser', ['num_users'] + edits_metrics, args.outdir, "collab_edits_summary")
  report(editors_summary, 'country', 'is_poweruser', ['num_users'] + editors_metrics, args.outdir, "editors_summary")
  report(editor_scores_summary, 'country', 'is_poweruser', ['num_users'] + editor_scores, args.outdir, "editor_scores_summary")

  #
  # Box plots
  #
  
  items_boxplot(edits_data, regions, edits_metrics, 
    args.outdir, 'collab_edits_boxplot_fliers')

  items_boxplot(edits_data, regions, edits_metrics, 
    args.outdir, 'collab_edits_boxplot',
    sym='') # don't show fliers

  items_boxplot(editors_data, regions, editors_metrics, 
    args.outdir, 'editors_boxplot_fliers')
  
  items_boxplot(editors_data, regions, editors_metrics, 
    args.outdir, 'editors_boxplot',
    sym='') # don't show fliers
  
  items_scatterplot(editors_data, 'num_poi_edits', regions, editors_metrics, 
    args.outdir, 'editors_scatter_num_poi_edits', alpha=0.3)

  items_boxplot(editors_data, regions, editor_scores, 
    args.outdir, 'editor_scores_boxplot_fliers')
  
  items_boxplot(editors_data, regions, editor_scores, 
    args.outdir, 'editor_scores_boxplot',
    sym='') # don't show fliers
  
  items_scatterplot(editors_data, 'num_poi_edits', regions, editor_scores, 
    args.outdir, 'editor_scores_scatter_num_poi_edits', alpha=0.3)

