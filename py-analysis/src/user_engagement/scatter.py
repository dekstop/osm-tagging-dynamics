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
# = Tools =
# =========

def remove_zero_or_less(x, y):
  x1 = []
  y1 = []
  for idx in range(len(x)):
    if (x[idx]>0 and y[idx]>0):
      x1.append(x[idx])
      y1.append(y[idx])
  return (x1, y1)

# =========
# = Plots =
# =========

# kwargs is passed on to plt.scatter(...).
def plot_scatter(data, anchor_row, columns, rows, outdir, filename_base, log_scale=False, **kwargs):
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

      if log_scale:
        (x, y) = remove_zero_or_less(x, y)

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)

      plt.scatter(x,y, **kwargs)
      
      if log_scale:
        ax1.set_xscale('log')
        ax1.set_yscale('log')
      else:
        ax1.get_xaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
        ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(simplified_SI_format))
      ax1.tick_params(axis='both', which='major', labelsize='x-small')
      ax1.tick_params(axis='both', which='minor', labelsize='xx-small')

      n += 1
  
  plt.savefig("%s/%s.pdf" % (outdir, filename_base), bbox_inches='tight')
  plt.savefig("%s/%s.png" % (outdir, filename_base), bbox_inches='tight')

# ========
# = Main =
# ========

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='User engagement distribution per region.')
  parser.add_argument('outdir', help='directory for output files')
  parser.add_argument('--schema', dest='schema', type=str, default='public', 
      action='store', help='parent schema that contains data tables. Default: public')
  args = parser.parse_args()

  #
  # Get data
  #
  
  metrics = ['num_poi', 
    'num_poi_created', 'num_poi_edited', 
    'num_changesets', 'num_edits', 
    'num_tag_keys', 'num_tag_add', 'num_tag_update', 'num_tag_remove',
    'days_active', 'lifespan_days']
  
  data = dict()
  for metric in metrics:
    data[metric] = defaultdict(list)

  # getDb().echo = True    
  session = getSession()
  result = session.execute(
    """SELECT r.name AS region, %s FROM %s.user_edit_stats s 
    JOIN region r ON s.region_id=r.id""" % (', '.join(metrics)), args.schema)
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
    args.outdir, 'scatter_num_edits')

  plot_scatter(data, 'num_edits', regions, metrics, 
    args.outdir, 'scatter_num_edits_log', log_scale=True)

  plot_scatter(data, 'days_active', regions, metrics, 
    args.outdir, 'scatter_days_active')

  plot_scatter(data, 'days_active', regions, metrics, 
    args.outdir, 'scatter_days_active_log', log_scale=True)
