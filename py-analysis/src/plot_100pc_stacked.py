import matplotlib
matplotlib.use('Agg')

import argparse
import csv
import numpy as np
import pandas

import matplotlib.pyplot as plt

from app import *

# ==========
# = Charts =
# ==========

def plot(pivot, groups, aspects, title=None, nolegend=False, colors = ['r', 'y', 'b']):
  N = len(groups)
  ind = np.arange(N)
  width = 1
  idx = 0
  bar_plots = [None] * len(aspects)
  bottom = [0.0] * N
  for aspect in aspects:
    aspect_values = pivot.ix[aspect].values
    bar_plots[idx] = plt.bar(ind, aspect_values, width, bottom=bottom, color=colors[idx])
    bottom += aspect_values
    idx += 1

  # Labels etc
  if title:
    plt.title(title) 

  plt.xticks(ind + width/2., groups)
  plt.gca().axes.get_yaxis().set_visible(False)

  if nolegend==False:
    # drawing is from bottom to top, so label order is reversed:
    plt.legend(reversed(bar_plots), reversed(aspects), loc=4)
  
# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='A 100%% stacked bar chart for multiple groups of data.')
  parser.add_argument('datafile', help='input filename, in TSV format')
  parser.add_argument('outfile', help='output filename, also determines image format')
  parser.add_argument('--groups', dest='groups', action='store', help='data column for group names')
  parser.add_argument('--aspects', dest='aspects', action='store', help='data column for aspect names')
  parser.add_argument('--values', dest='values', action='store', help='data column for values')
  parser.add_argument('--title', dest='title', action='store', help='graph title')
  parser.add_argument('--nolegend', dest='nolegend', default=False, action='store_true', help='don''t include a legend')
  args = parser.parse_args()
  
  # outfile = sys.argv[1]
  # rows = int(sys.argv[2])
  # cols = int(sys.argv[3])
  # infiles = sys.argv[4:]

  # Load data
  df = pandas.read_csv(args.datafile, index_col=None, dialect=csv.excel_tab)
  pivot = df.pivot(index=args.aspects, columns=args.groups, values=args.values)
  groups = pivot.columns
  aspects = pivot.index.tolist()
  
  pivot_norm = pivot.astype(float) / pivot.sum()

  # Make plot
  fig = plt.figure()
  fig.patch.set_facecolor('white')
  plot(pivot_norm, groups, aspects, title=args.title, nolegend=args.nolegend)
  
  # Save to file.
  # plt.show()
  plt.savefig(args.outfile, bbox_inches='tight')
