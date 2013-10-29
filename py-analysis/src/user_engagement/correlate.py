#
# Pearson/Spearman correlation between pairs of user engagement metrics.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import sys

import matplotlib.pyplot as plt
import numpy
import scipy.stats.stats as stats

from app import *

# =========
# = Plots =
# =========

# data: list of dict(metric -> value)
# assumes that all records have all metrics
def qqplot(data, metrics, outdir, filename_base, **kwargs):

  ncols = len(metrics)
  nrows = len(metrics)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  for a in range(len(metrics)):
    for b in range(a):
      # correlation
      data_a = sorted([record[metrics[a]] for record in data])
      data_b = sorted([record[metrics[b]] for record in data])

      minval = min([data_a[0], data_b[0]])
      maxval = max([data_a[-1], data_b[-1]])

      # Plot
      n = a * len(metrics) + b + 1
      
      if a == b+1: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=metrics[b])
      else:
        ax1 = plt.subplot(nrows, ncols, n)
    
      if (b == 0): # first column
        plt.ylabel(metrics[a])
      
      ax1.scatter(data_b, data_a, **kwargs)
      ax1.plot([minval, maxval], [minval, maxval], 'r--')

      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

  plt.savefig("%s/%s.pdf" % (args.outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (args.outdir, filename_base), bbox_inches='tight')


# data: list of dict(metric -> value)
def corr_plot_report(data, metrics, outdir, filename_base, **kwargs):

  outfile = open("%s/%s.txt" % (args.outdir, filename_base), 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(['metric_a', 'metric_b', 'pcc', 'p_pcccc', 'scc', 'p_scc'])

  ncols = len(metrics)
  nrows = len(metrics)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  for a in range(len(metrics)):
    for b in range(a):
      # correlation
      data_a = [record[metrics[a]] for record in data]
      data_b = [record[metrics[b]] for record in data]

      # Plot
      n = a * len(metrics) + b + 1
      
      if a == b+1: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=metrics[b])
      else:
        ax1 = plt.subplot(nrows, ncols, n)
    
      if (b == 0): # first column
        plt.ylabel(metrics[a])
      
      ax1.scatter(data_b, data_a, **kwargs)

      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
      
      # Correlation coefficients
      (pcc, p_pcc) = stats.pearsonr(data_a, data_b)
      (scc, p_scc) = stats.spearmanr(data_a, data_b)

      plt.text(0.05, 0.95, "PCC=%.3f\np=%.3f" % (pcc, p_pcc),
        transform=ax1.transAxes, color='b', ha='left', va='top', size='small')
      plt.text(0.95, 0.05, "\nSCC=%.3f\np=%.3f" % (scc, p_scc), 
        transform=ax1.transAxes, color='r', ha='right', va='bottom', size='small')
      
      outcsv.writerow([metrics[a], metrics[b], pcc, p_pcc, scc, p_scc])

  outfile.close()

  plt.savefig("%s/%s.pdf" % (args.outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (args.outdir, filename_base), bbox_inches='tight')


# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Pearson/Spearman correlation between pairs of user engagement metrics.')
  parser.add_argument('--schema', dest='schema', type=str, default='public', 
      action='store', help='parent schema that contains data tables. Default: public')
  parser.add_argument('--regions', dest='regions', type=str, nargs='+', default=None, 
      action='store', help='list of region names')
  parser.add_argument('--scheme', dest='scheme_name', type=str, default=None, 
      action='store', help='name of the segmentation scheme')
  parser.add_argument('outdir', help='directory for output files')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove',
    'days_active', 'lifespan_days']
  
  data = defaultdict(list) # region -> list of user edit stats
  
  # getDb().echo = True    
  session = getSession()
  query = """SELECT r.name AS region, %s
    FROM %s.user_edit_stats ues
    JOIN region r ON ues.region_id=r.id """ % (', '.join(metrics), args.schema)
  conditions = []
  if args.scheme_name!=None:
    print "Loading segmented data scheme: '%s'" % (args.scheme_name)
    query += "JOIN sample_1pc.region_user_segment seg ON (seg.region_id=ues.region_id AND seg.uid=ues.uid)"
    conditions.append("seg.scheme='%s'" % (args.scheme_name))
  if args.regions!=None:
    str_regions = "', '".join(args.regions)
    print "Limiting to regions: '%s'" % (str_regions)
    conditions.append("r.name IN ('%s')" % (str_regions))
  if len(conditions)>0:
    query += " WHERE " + " AND ".join(conditions)
  result = session.execute(query)
  # print result.keys()

  num_records = 0
  for row in result:
    region = row['region']
    data[region].append(row)
    # for metric in metrics:
    #   data[region][metric].append(row[metric])
    
    num_records += 1

  print "Loaded %d records." % (num_records)

  regions = sorted(data.keys())

  # Prep
  mkdir_p(args.outdir)

  #
  # Correlation
  #
  
  for region in regions:
    qqplot(data[region], metrics, args.outdir, "qq-plot_%s" % (region))
    corr_plot_report(data[region], metrics, args.outdir, "corr_%s" % (region))
