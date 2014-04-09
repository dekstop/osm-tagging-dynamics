#
# Compute long-tail distribution metrics: coefficients, goodness of fit.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import ticker
import pandas as pd
import powerlaw

from app import *

# =========
# = Plots =
# =========

# data: a dict of { measure -> list of values }
# kwargs are passed on to plt.hist(...)
def plot_hist(data, measures, outdir, filename_base, bins=10, **kwargs):
  for (measure, temp, ax1) in plot_matrix(measures, [1]):
    plt.hist(data[measure], bins=bins, histtype='bar', **kwargs)

    ax1.tick_params(axis='both', which='major', labelsize='x-small')
    ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
  
    ax1.margins(0.1, 0.1)
    # ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    # ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
    ax1.get_xaxis().set_ticks([])
    ax1.get_yaxis().set_ticks([])

  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# data: a dict of { measure -> list of values }
# Will ignore values of value 0
def report_dist(data, measures, outdir, filename_base, discrete=False):
  reportfilename = "%s/%s.txt" % (outdir, filename_base)
  reportfile = open(reportfilename, 'wb')

  for (measure, temp, ax1) in plot_matrix(measures, [1]):
      reportfile.write("= %s =\n" % measure)
      values = list(value for value in data[measure] if value>0)

      powerlaw.plot_pdf(values, ax=ax1, color='k')
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      fit = powerlaw.Fit(values, discrete=discrete, xmin=2) #, xmin=min(values))
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

  reportfile.close()
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Compute long-tail distribution metrics: coefficients, goodness of fit.')
  parser.add_argument('tsv', help='Input TSV file. The first column is taken as group identifier, the remaining columns as measures.')
  parser.add_argument('outdir', help='Directory for output files')
  parser.add_argument('--discrete', help='Treat values as discrete numbers', dest='discrete', action='store', type=bool, default=False)
  args = parser.parse_args()

  #
  # Get data
  #
  
  # df = pd.DataFrame.from_csv(args.tsv, sep='\t')
  df = pd.read_table(args.tsv, index_col=0)
  groups = df.index
  metrics = df.keys()

  # dict: metric -> list of values
  data = defaultdict(list) 
  for metric in metrics:
    print "%s ..." % metric
    data[metric] = [(df.ix[g][metric]) for g in groups]
  
  # Prep
  mkdir_p(args.outdir)
  
  # Plot1: histogram
  plot_hist(data, metrics, args.outdir, 'longtail_user_hist',
    normed=True)
  
  plot_hist(data, metrics, args.outdir, 'longtail_user_hist_log',
    normed=True, log=True)
  
  # Plot2: distribution estimation
  report_dist(data, metrics, args.outdir, 'longtail_user_dist_fit', 
    discrete=args.discrete)
