#
# Pearson/Spearman correlation between pairs of metrics.
#

from __future__ import division # non-truncating division in Python 2.x

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict
import decimal
import gc
import sys

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
import pandas as pd
import scipy.stats.stats as stats

from app import *

# ===========
# = Reports =
# ===========

# data: a nested dict: key1 -> key2 -> colname -> value
def report(data, key1name, key2name, colnames, outdir, filename_base):
  filename = "%s/%s.txt" % (outdir, filename_base)
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow([key1name, key2name] + colnames)
  for key1 in sorted(data.keys()):
    for key2 in sorted(data[key1].keys()):
      if len(data[key1][key2]) > 0:
        outcsv.writerow([key1, key2] + [data[key1][key2][col] for col in colnames])
  outfile.close()

# =========
# = Plots =
# =========

# corr: metric1 -> metric2 -> measure -> value
def corrmatrix(metrics1, metrics2, corr, measure, outdir, filename_base, 
  cmap=cm.gray, **kwargs):

  ncols = len(metrics1)
  nrows = len(metrics2)

  fig = plt.figure(figsize=(1*ncols, 0.75*nrows))
  plt.subplots_adjust(hspace=0, wspace=0)
  fig.patch.set_facecolor('white')

  for a in range(len(metrics1)):
    for b in range(len(metrics2)):

      scores = corr[metrics1[a]][metrics2[b]]
      if len(scores) > 0:
        val = scores[measure]

        # Plot
        n = a + len(metrics1) * b + 1
        ax1 = plt.subplot(nrows, ncols, n)
      
        if b == len(metrics2)-1: # last row
          plt.xlabel(metrics1[a], rotation=90)

        if (a == 0): # first column
          plt.ylabel(metrics2[b], rotation=0)
      
        ax1.bar(0, 1, 1, 0, color=cmap(val), **kwargs)

        ax1.get_xaxis().set_ticks([])
        ax1.get_yaxis().set_ticks([])
  
  plt.savefig("%s/%s.pdf" % (args.outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (args.outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Correlation matrix of two different sets of metrics of the same named items.')
  parser.add_argument('tsv_a', help='Input TSV file. The first column is taken as group identifier, the remaining columns as measures.')
  parser.add_argument('tsv_b', help='A second (optional) input TSV file to compare against.', nargs='?', default=None)
  parser.add_argument('outdir', help='Directory for output files')
  
  args = parser.parse_args()

  #
  # Get data
  #
  
  # data_a = pd.DataFrame.from_csv(args.tsv_a, sep='\t')
  data_a = pd.read_table(args.tsv_a, index_col=0)
  if args.tsv_b:
    data_b = pd.read_table(args.tsv_b, index_col=0)
    self_corr = False
  else:
    data_b = data_a
    self_corr = True
  
  groups_a = data_a.index
  groups_b = data_b.index
  groups = sorted([g for g in groups_a if g in groups_b])
  print "Number of samples: %d" % len(groups)
  
  metrics_a = data_a.keys()
  metrics_b = data_b.keys()

  #
  # Correlation scores
  #
  
  # dict: metric1 -> metric2 -> measure -> value
  corr = defaultdict(lambda: defaultdict(dict)) 
  
  for metric_a in metrics_a:
    print metric_a + " ..."
    values_a = [data_a.ix[g][metric_a] for g in groups if data_a.ix[g][metric_a]!=None]

    for metric_b in metrics_b:

      if self_corr and len(corr[metric_b][metric_a]) > 0:
        pass # Check for symmetry: we already computed this
      else:
        values_b = [data_b.ix[g][metric_b] for g in groups if data_b.ix[g][metric_b]!=None]
      
        (pcc, p_pcc) = stats.pearsonr(values_a, values_b)
        (scc, p_scc) = stats.spearmanr(values_a, values_b)

        scores = dict()
        scores['pcc'] = pcc
        scores['p_pcc'] = p_pcc
        scores['scc'] = scc
        scores['p_scc'] = p_scc
      
        corr[metric_a][metric_b] = scores
  
  #
  # Report and correlation matrix plots.
  #
  mkdir_p(args.outdir)
  
  measures = ['pcc', 'p_pcc', 'scc', 'p_scc']
  report(corr, 'metric a', 'metric b', measures, args.outdir, 'corr_matrix')
  
  for measure in measures:
    corrmatrix(metrics_a, metrics_b, corr, measure, args.outdir, 
      'corr_matrix_' + measure, cmap=cm.Blues)
  