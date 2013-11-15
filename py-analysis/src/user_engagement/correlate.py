#
# Pearson/Spearman correlation between pairs of user engagement metrics.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import sys

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
import scipy.stats.stats as stats

from app import *

# =========
# = tools =
# =========

def float_f(f):
  return format(f, 'f').rstrip('0')

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
# corr: metric1 -> metric2 -> measure -> value
def scatterplot(data, metrics, corr, outdir, filename_base, **kwargs):

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
      scores = corr[metrics[a]][metrics[b]]

      plt.text(0.05, 0.95, "PCC=%.3f\np=%.3f" % (scores['pcc'], scores['p_pcc']),
        transform=ax1.transAxes, color='b', ha='left', va='top', size='small')
      plt.text(0.95, 0.05, "\nSCC=%.3f\np=%.3f" % (scores['scc'], scores['p_scc']), 
        transform=ax1.transAxes, color='r', ha='right', va='bottom', size='small')
  
  plt.savefig("%s/%s.pdf" % (args.outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (args.outdir, filename_base), bbox_inches='tight')


# corr: metric1 -> metric2 -> measure -> value
def corrmatrix(metrics, corr, measure, outdir, filename_base, cmap=cm.gray, **kwargs):

  # TODO: OR: plt.matshow, plt.pcolor, ...

  ncols = len(metrics)
  nrows = len(metrics)

  fig = plt.figure(figsize=(1*ncols, 0.75*nrows))
  plt.subplots_adjust(hspace=0, wspace=0)
  fig.patch.set_facecolor('white')

  for a in range(len(metrics)):
    for b in range(a):

      scores = corr[metrics[a]][metrics[b]]
      val = scores[measure]

      # Plot
      n = a * len(metrics) + b + 1
      ax1 = plt.subplot(nrows, ncols, n)
      
      if a == len(metrics)-1: # last row
        plt.xlabel(metrics[b], rotation=90)

      if (b == 0): # first column
        plt.ylabel(metrics[a], rotation=0)
      
      ax1.bar(0, 1, 1, 0, color=cmap(val), **kwargs)

      ax1.get_xaxis().set_ticks([])
      ax1.get_yaxis().set_ticks([])
  
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

  query = """SELECT r.name AS region, ues.uid, %s
    FROM %s.user_edit_stats ues
    JOIN region r ON ues.region_id=r.id """ % (', '.join(metrics), args.schema)
  conditions = []

  if args.scheme_name!=None:
    print "Loading segmented data scheme: '%s'" % (args.scheme_name)
    query += "JOIN %s.region_user_segment seg ON \
      (seg.region_id=ues.region_id AND seg.uid=ues.uid)" % (args.schema)
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
    data[region].append(dict(row.items()))
    # for metric in metrics:
      # data[region][metric].append(row[metric])
    
    num_records += 1

  print "Loaded %d records." % (num_records)

  regions = sorted(data.keys())

  # Prep
  mkdir_p(args.outdir)
  
  #
  # Log transform
  #
  
  # for idx in range(len(data[region])):
  #   for metric in metrics:
  #     if data[region][idx][metric]==0:
  #       print "zero for metric: %s uid: %d metric: %s" % (region, data[region][idx]['uid'], metric)
  #       data[region][idx][metric] = None
  #     else:
  #       data[region][idx][metric] = numpy.log(data[region][idx][metric])
  
  
  #
  # Correlation
  #

  # region -> metric1 -> metric2 -> measure -> value
  corr = dict()
  
  for region in regions:
    corr[region] = defaultdict(dict)

    outfile = open("%s/%s_corr.txt" % (args.outdir, region), 'wb')
    outcsv = csv.writer(outfile, dialect='excel-tab')
    outcsv.writerow(['metric_a', 'metric_b', 'pcc', 'p_pcc', 'scc', 'p_scc'])

    for a in range(len(metrics)):
      for b in range(a):
      
        data_a = [record[metrics[a]] for record in data[region]]
        data_b = [record[metrics[b]] for record in data[region]]

        # Correlation coefficients
        (pcc, p_pcc) = stats.pearsonr(data_a, data_b)
        (scc, p_scc) = stats.spearmanr(data_a, data_b)

        scores = dict()
        scores['pcc'] = pcc
        scores['p_pcc'] = p_pcc
        scores['scc'] = scc
        scores['p_scc'] = p_scc
      
        corr[region][metrics[a]][metrics[b]] = scores
        corr[region][metrics[b]][metrics[a]] = scores # Symmetry
  
        outcsv.writerow([metrics[a], metrics[b], 
          float_f(scores['pcc']), 
          float_f(scores['p_pcc']), 
          float_f(scores['scc']), 
          float_f(scores['p_scc'])])

    outfile.close()

  #
  # Plots 
  #
  
  for region in regions:
    qqplot(data[region], metrics, args.outdir, "%s_qq-plot" % (region))
    scatterplot(data[region], metrics, corr[region], args.outdir, "%s_scatter" % (region))
    corrmatrix(metrics, corr[region], 'pcc', args.outdir, "%s_corr_pcc" % (region), cmap=cm.Blues)
    corrmatrix(metrics, corr[region], 'scc', args.outdir, "%s_corr_scc" % (region), cmap=cm.Blues)
