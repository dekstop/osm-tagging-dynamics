#
# Scatter plot of misc metrics.
#

import matplotlib
matplotlib.use('Agg')

import argparse
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import ticker

from app import *

# =========
# = Plots =
# =========

def custom_number_format(x, p):
  sign = ''
  suffix = ''
  is_fractional = False

  if x < 0:
    x *= -1
    sign = '-'

  if x >= 1000:
    x /= 1000
    suffix = 'k'
    is_fractional = True

  if x >= 1000:
    x /= 1000
    suffix = 'M'
    is_fractional = True

  if is_fractional:
    return "%s%.1f%s" % (sign, x, suffix)
  else:
    return "%s%d%s" % (sign, int(x), suffix)

# kwargs is passed on to plt.scatter(...).
def plot_scatter(data, anchor_row, columns, rows, outdir, filename_base, **kwargs):
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(4*ncols, 3*nrows))
  plt.subplots_adjust(hspace=.2, wspace=0.2)
  fig.patch.set_facecolor('white')

  n = 1
  for row in rows:
    for column in columns:

      x = data[anchor_row][column]
      y = data[row][column]

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      plt.scatter(x,y, **kwargs)
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')
      # ax1.ticklabel_format(style='sci', axis='both', scilimits=(0,0))

      ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(custom_number_format))
      ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(custom_number_format))

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='User engagement distribution per region.')
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
  
  #
  # Plots
  # 
  
  plot_scatter(data, 'num_edits', regions, metrics, 
    args.outdir, "scatter_%s" % ('num_edits'))

  plot_scatter(data, 'num_changesets', regions, metrics, 
    args.outdir, "scatter_%s" % ('num_changesets'))
