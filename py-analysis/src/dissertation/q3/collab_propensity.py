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

# =========
# = Plots =
# =========

# kwargs is passed on to plt.scatter(...).
def scatterplot(x, y, outdir, filename_base, scale='linear', **kwargs):
  
  fig = plt.figure(figsize=(4, 3))
  fig.patch.set_facecolor('white')
  plt.scatter(x, y, edgecolors='none', **kwargs)
  plt.margins(0.1, 0.1)
  plt.tick_params(axis='both', which='major', labelsize='x-small')
  plt.tick_params(axis='both', which='minor', labelsize='xx-small')
  plt.xscale(scale)
  plt.yscale(scale)

  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')
  
  # free memory
  plt.close() # closes current figure
  gc.collect()

# kwargs is passed on to plt.scatter(...).
def hist2dplot(x, y, outdir, filename_base, scale='linear', **kwargs):
  
  fig = plt.figure(figsize=(4, 3))
  fig.patch.set_facecolor('white')
  plt.hist2d(x, y, **kwargs)
  plt.margins(0.1, 0.1)
  plt.tick_params(axis='both', which='major', labelsize='x-small')
  plt.tick_params(axis='both', which='minor', labelsize='xx-small')
  plt.xscale(scale)
  plt.yscale(scale)

  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')
  
  # free memory
  plt.close() # closes current figure
  gc.collect()

# data: { segment -> list of values }
# kwargs is passed on to plt.boxplot(...).
def boxplot(data, segments, outdir, filename_base, show_minmax=False, **kwargs):
  
  fig = plt.figure(figsize=(2.5, 3))
  fig.patch.set_facecolor('white')
  celldata = []
  minv = []
  maxv = []
  for segment in segments:
    celldata.append(data[segment])
    if len(data[segment]) > 0:
      minv.append(min(data[segment]))
      maxv.append(max(data[segment]))

  plt.boxplot(celldata, positions=range(len(segments)), **kwargs)

  if show_minmax and len(minv)>0 and len(maxv)>0:
    for idx in range(len(minv)):
      w = 0.1
      plt.plot([idx-w, idx+w], [minv[idx]]*2, 'k-')
      plt.plot([idx-w, idx+w], [maxv[idx]]*2, 'k-')
    
  plt.margins(0.1, 0.1)
  ax = plt.gca()
  ax.get_xaxis().set_visible(False)
  ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
  plt.tick_params(axis='y', which='major', labelsize='x-small')
  plt.tick_params(axis='y', which='minor', labelsize='xx-small')
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')
  
  # free memory
  plt.close() # closes current figure
  gc.collect()

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Statistics relating to collaborative editing practices.')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--schema', dest='schema', type=str, default='public', 
      action='store', help='parent schema that contains data tables. Default: public')
  parser.add_argument('--actions', help='list of tag edit actions', 
    dest='actions', nargs='+', action='store', type=str, default=None)
  args = parser.parse_args()

  #
  # Get data
  #
  
  fields = ['uid', 'num_edits', 'num_collab_edits', 'share_collab_edits']
  
  action_filter = ""
  if args.actions:
    print "Limiting to actions: " + ", ".join(args.actions)
    action_filter = " WHERE pt.action IN ('%s') " % ("', '".join(args.actions))
  
  #getDb().echo = True    
  session = getSession()
  
  # result = session.execute("""SELECT 1 uid, 1 as num_edits, 
  #   1 as num_collab_edits, 1.0 as share_collab_edits""")
  result = session.execute("""SELECT t1.uid as uid, num_edits, 
    COALESCE(num_collab_edits, 0) as num_collab_edits, 
    COALESCE(num_collab_edits, 0)::numeric / num_edits as share_collab_edits
  FROM (
    SELECT uid, count(*) as num_edits
    FROM %s.poi p 
    JOIN %s.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
    GROUP BY uid
  ) t1
  LEFT OUTER JOIN (
    SELECT uid, count(*) as num_collab_edits
    FROM %s.poi p
    JOIN shared_poi sp ON (p.id=sp.poi_id AND p.version>=sp.first_shared_version)
    JOIN %s.poi_tag_edit_action pt ON (p.id=pt.poi_id AND p.version=pt.version)
    %s
    GROUP BY uid
  ) t2 ON (t1.uid=t2.uid)
  ORDER BY num_edits ASC""" % (args.schema, args.schema, args.schema, args.schema, action_filter))

  data = []
  num_records = 0
  for row in result:
    record = dict()
    for field in fields:
      record[field] = row[field]
    data.append(record)
    num_records += 1
  print "Loaded %d records." % (num_records)

  #
  # Reports
  #
  mkdir_p(args.outdir)
  report(data, fields, args.outdir, "editor_collab_stats")
  
  #
  # Remove outliers
  #
  
  # outlier thresholds
  min_edits = 20
  # max_edits = 50000

  filtered_data = [record for record in data if record['num_edits']>=min_edits]
  
  # filtered_data = [record for record in data if
  #   record['num_edits']>=min_edits and
  #   record['num_edits']<=max_edits]

  # filtered_data = data

  #
  # Regression
  #
  x = []
  y = []
  for row in filtered_data:
    x.append(row['num_edits'])
    y.append(row['share_collab_edits'])
  
  (pcc, p_pcc) = stats.pearsonr(x, y)
  (scc, p_scc) = stats.spearmanr(x, y)
  
  results = []
  columns = ['type', 'cc', 'p']
  results.append(dict(zip(columns, ['pcc', pcc, p_pcc])))
  results.append(dict(zip(columns, ['scc', scc, p_scc])))
  report(results, columns, args.outdir, "editor_collab_correlation")
  
  #
  # Box plots of normal/power user propensity
  #
  power_threshold = 50
  normal_propensity = [record['share_collab_edits'] for record in filtered_data 
    if record['num_edits']<=power_threshold]
  power_propensity = [record['share_collab_edits'] for record in filtered_data 
    if record['num_edits']>power_threshold]
  
  columns = ['normal', 'power']
  prop_classes = dict(zip(columns, [normal_propensity, power_propensity]))

  boxplot(prop_classes, columns, args.outdir, "editor_collab_propensity_boxplot_fliers")

  boxplot(prop_classes, columns, args.outdir, "editor_collab_propensity_boxplot",
    sym='') # don't show fliers

  #
  # Scatter plots
  #
  
  # value ranges
  min_edits = 20
  max_edits = 5000
  
  chart_data = [record for record in filtered_data if
    record['num_edits']>=min_edits and
    record['num_edits']<=max_edits]
  
  # propensity
  x = []
  y = []
  for row in chart_data:
    x.append(row['num_edits'])
    y.append(row['share_collab_edits'])
  
  scatterplot(x, y, args.outdir, "editor_collab_propensity_scatter", alpha=0.8)
  hist2dplot(x, y, args.outdir, "editor_collab_propensity_hist2d")
