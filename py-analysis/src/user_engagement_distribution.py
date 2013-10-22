#
# Compute power-law distribution metrics: coefficients, goodness of fit.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy
import powerlaw

from app import *

# =========
# = Plots =
# =========

# kwargs are passed on to plt.hist(...)
def plot_hist(data, columns, rows, filename, **kwargs):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
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
  
      plt.hist(data[row][column], bins=20, histtype='bar', **kwargs)
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
  
      n += 1
  
  plt.savefig(filename, bbox_inches='tight')

def plot_dist(data, columns, rows, filename):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      print "= %s: %s =" % (column, row)
      
      values = list(value for value in data[row][column] if value>0)
      # print data[row][column]
      # print values

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      powerlaw.plot_pdf(values, ax=ax1, color='k')
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      fit = powerlaw.Fit(values, discrete=True, xmin=2) #, xmin=min(values))
      print "Lognormal:"
      print "  mu = %f" % (fit.lognormal.mu)
      print "  sigma = %f" % (fit.lognormal.sigma)
      print "  xmin = %d" % (fit.lognormal.xmin)
      print "Power-law:"
      print "  alpha = %f" % (fit.power_law.alpha)
      print "  sigma = %f" % (fit.power_law.sigma)
      print "  xmin = %d" % (fit.power_law.xmin)

      R, p = fit.distribution_compare('lognormal', 'power_law')
      # 'lognormal', 'exponential', 'truncated_power_law', 'stretched_exponential', 'gamma', 'power_law'
      print "Lognormal fit compared to power-law distribution: R=%f, p=%f" % (R, p)
      print

      fit.power_law.plot_pdf(linestyle='--', color='b', ax=ax1, label='Power-law fit')
      info = "Power-law:\nalpha=%.3f\nsigma=%.3f\nxmin=%d" % (fit.power_law.alpha, fit.power_law.sigma, fit.power_law.xmin)
      plt.text(0.1, 0.1, info, transform=ax1.transAxes, color='b', ha='left', va='bottom', size='small')

      fit.lognormal.plot_pdf(linestyle='--', color='r', ax=ax1, label='Lognormal fit')
      info = "Lognormal:\nmu=%.3f\nsigma=%.3f\nxmin=%d" % (fit.lognormal.mu, fit.lognormal.sigma, fit.lognormal.xmin)
      plt.text(0.9, 0.9, info, transform=ax1.transAxes, color='r', ha='right', va='top', size='small')

      n += 1
  
  plt.savefig(filename, bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='User engagement statistics per region.')
  parser.add_argument('outdir', help='directory for output files')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove']
  
  segmentation_metric = 'num_edits'
  segmentation_bands = [20, 50, 80]

  data = dict()
  for metric in metrics:
    data[metric] = defaultdict(list)

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, %s FROM sample_1pc.user_edit_stats s 
    JOIN region r ON s.region_id=r.id""" % (', '.join(metrics)))
  # print result.keys()

  num_users = 0
  for row in result:
    for metric in metrics:
      region = row['region']
      data[metric][region].append(row[metric])
    num_users += 1
  
  print "Loaded data for %d users." % (num_users)
  
  regions = sorted(data[metrics[0]].keys())
  ncols = len(regions)
  nrows = len(metrics)
  
  # Prep
  mkdir_p(args.outdir)
  
  #
  # Plots
  # 
  
  # Plot1: histogram
  plot_hist(data, regions, metrics, "%s/user_hist.pdf" % (args.outdir), 
    normed=True, range=[0, 20])
  
  plot_hist(data, regions, metrics, "%s/user_hist_log.pdf" % (args.outdir), 
    normed=True, log=True, range=[0, 20])
  
  # Plot2: distribution estimation
  plot_dist(data, regions, metrics, "%s/user_dist_fit.pdf" % (args.outdir))

  #
  # User engagement bands per region
  #
  
  scores = ['edits_per_user', 'poi_edit_score', 'tag_edit_score', 'tag_removal_score']

  filename = "%s/segments.txt" % (args.outdir)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  header = ['region', 'band', 'low', 'high', 
    'num_users', 'total_users', 
    'num_edits', 'total_edits']
  header.extend(metrics)
  header.extend(scores)
  outcsv.writerow(header)

  for region in regions:
    print "= %s =" % (region)

    values = data[segmentation_metric][region]
    total_edits = sum(values)
    total_users = len(values)

    # inverted percentile: we're interested in the n% _top_ entries
    top_bands = segmentation_bands #list(100 - numpy.array(segmentation_bands))
    thresholds = numpy.percentile(values, top_bands) 
    thresholds.append(max(values))

    # remove duplicate thresholds for low-data regions
    thresholds = sorted(list(set(thresholds)))
    print thresholds
    
    low = 0
    band_idx = 1
    for high in thresholds:
      print "Band: %f < %s <= %f" % (low, segmentation_metric, high)
      
      result = session.execute(
        """SELECT avg(%s), 
        1.0*sum(num_edits)/count(distinct uid) as edits_per_user, 
        avg(num_poi_edited/(num_poi_created + 1)) as poi_edit_score, 
        avg(num_tag_update/(num_tag_add + 1)) as tag_edit_score, 
        avg(num_tag_remove/(num_tag_add + 1)) as tag_removal_score, 
        sum(num_edits) as num_edits,
        count(distinct uid) as num_users 
        FROM sample_1pc.user_edit_stats s 
        JOIN region r ON s.region_id=r.id
        WHERE r.name='%s' 
        AND s.num_edits>%f
        AND s.num_edits<=%f""" % ('), avg('.join(metrics), region, low, high))
      
      for row in result:
        outdata = [region, 'band_%d' % (band_idx), low, high, 
          row['num_users'], total_users, 
          row['num_edits'], total_edits]
        
        print "Number of users: %d (total: %d)" % (row['num_users'], total_users)
        print "Number of edits: %d (total: %d)" % (row['num_edits'], total_edits)

        for idx in range(len(metrics)):
          print "  avg %s: %f" % (metrics[idx], row[idx])
          outdata.append(row[idx])

        for col in scores:
          print "  %s: %f" % (col, row[col])
          outdata.append(row[col])
        
        outcsv.writerow(outdata)
      
      low = high
      band_idx += 1
    
  outfile.close()
  
  # for metric in metrics:
  #   print "= %s =" % (metric)
  #   for region in regions:
  #     print "%s" % (region)
  #     for band in bands:
  #       v = numpy.percentile(data[metric][region], band)
  #       print "  %.0f%%: %.2f" % (band, v)
