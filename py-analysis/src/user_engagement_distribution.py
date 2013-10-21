#
# Compute power-law distribution metrics: coefficients, goodness of fit.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict

import matplotlib.pyplot as plt
import powerlaw

from app import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='User engagement statistics per region.')
  parser.add_argument('outfile1', help='histogram image output filename, also determines image format')
  parser.add_argument('outfile2', help='distribution image output filename, also determines image format')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 'num_tag_keys']

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, %s FROM sample_1pc.user_edit_stats s 
    JOIN region r ON s.region_id=r.id""" % (', '.join(metrics)))
  # print result.keys()

  data = dict()
  for metric in metrics:
    data[metric] = defaultdict(list)

  for row in result:
    for metric in metrics:
      region = row['region']
      data[metric][region].append(row[metric])
  
  regions = sorted(data[metrics[0]].keys())
  ncols = len(regions)
  nrows = len(metrics)
  
  #
  # Plot1: distribution estimation
  #

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')
  n = 1
  for metric in metrics:
    for region in regions:
  
      if n <=len(regions):
        ax1 = plt.subplot(nrows, ncols, n, title=region)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % len(regions) == 1):
        plt.ylabel(metric)
  
      plt.hist(data[metric][region], bins=20, histtype='bar', normed=True, #log=True,
        range=[0, 20])
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
  
      n += 1
  
  plt.savefig(args.outfile1, bbox_inches='tight')

  #
  # Plot2: distribution estimation
  #
  
  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for metric in metrics:
    for region in regions:

      print "==== %s: %s ====" % (region, metric)
      
      values = list(value for value in data[metric][region] if value>0)
      # print data[metric][region]
      # print values

      if n <=len(regions):
        ax1 = plt.subplot(nrows, ncols, n, title=region)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % len(regions) == 1):
        plt.ylabel(metric)

      powerlaw.plot_pdf(values, ax=ax1, color='k')
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      fit = powerlaw.Fit(values, discrete=True, xmin=2) #, xmin=min(values))
      print "Power-law:"
      print "  alpha = %f" % (fit.power_law.alpha)
      print "  sigma = %f" % (fit.power_law.sigma)
      print "  xmin = %d" % (fit.power_law.xmin)
      print "Lognormal:"
      print "  mu = %f" % (fit.lognormal.mu)
      print "  sigma = %f" % (fit.lognormal.sigma)
      print "  xmin = %d" % (fit.lognormal.xmin)

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
  
  plt.savefig(args.outfile2, bbox_inches='tight')
