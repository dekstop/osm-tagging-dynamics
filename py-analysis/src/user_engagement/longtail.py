#
# Compute long-tail distribution metrics: coefficients, goodness of fit.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict

import matplotlib.pyplot as plt
import powerlaw

from app import *

# =========
# = Plots =
# =========

# kwargs are passed on to plt.hist(...)
def plot_hist(data, columns, rows, outdir, filename_base, **kwargs):
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
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

def plot_dist(data, columns, rows, outdir, filename_base):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  reportfilename = "%s/%s.txt" % (outdir, filename_base)
  reportfile = open(reportfilename, 'wb')
  n = 1
  for row in rows:
    for column in columns:

      reportfile.write("= %s: %s =\n" % (column, row))
      
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
      reportfile.write("Lognormal:\n")
      reportfile.write("  mu = %f\n" % (fit.lognormal.mu))
      reportfile.write("  sigma = %f\n" % (fit.lognormal.sigma))
      reportfile.write("  xmin = %d\n" % (fit.lognormal.xmin))
      reportfile.write("Power-law:\n")
      reportfile.write("  alpha = %f\n" % (fit.power_law.alpha))
      reportfile.write("  sigma = %f\n" % (fit.power_law.sigma))
      reportfile.write("  xmin = %d\n" % (fit.power_law.xmin))

      R, p = fit.distribution_compare('lognormal', 'power_law')
      # 'lognormal', 'exponential', 'truncated_power_law', 'stretched_exponential', 'gamma', 'power_law'
      reportfile.write("Lognormal fit compared to power-law distribution: R=%f, p=%f\n" % (R, p))
      reportfile.write("\n")

      fit.power_law.plot_pdf(linestyle='--', color='b', ax=ax1, label='Power-law fit')
      info = "Power-law:\nalpha=%.3f\nsigma=%.3f\nxmin=%d" % (fit.power_law.alpha, fit.power_law.sigma, fit.power_law.xmin)
      plt.text(0.1, 0.1, info, transform=ax1.transAxes, color='b', ha='left', va='bottom', size='small')

      fit.lognormal.plot_pdf(linestyle='--', color='r', ax=ax1, label='Lognormal fit')
      info = "Lognormal:\nmu=%.3f\nsigma=%.3f\nxmin=%d" % (fit.lognormal.mu, fit.lognormal.sigma, fit.lognormal.xmin)
      plt.text(0.9, 0.9, info, transform=ax1.transAxes, color='r', ha='right', va='top', size='small')

      n += 1
  reportfile.close()
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Compute long-tail distribution metrics: coefficients, goodness of fit.')
  parser.add_argument('outdir', help='directory for output files')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove']
  
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
  
  # Plot1: histogram
  plot_hist(data, regions, metrics, args.outdir, 'longtail_user_hist',
    normed=True, range=[0, 20])
  
  plot_hist(data, regions, metrics, args.outdir, 'longtail_user_hist_log',
    normed=True, range=[0, 20], log=True)
  
  # Plot2: distribution estimation
  plot_dist(data, regions, metrics, args.outdir, 'longtail_user_dist_fit')
