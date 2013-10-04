import matplotlib
matplotlib.use('Agg')

import cStringIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import numpy as np
import pandas

from app import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  # session = getSession()
  # result = session.execute("SELECT 1 as name")
  # for f in result:
  #   print f['name']

  # Load data
  data = [
    {'region':'Belarus', 'usertype':'only_creators', 'num_users':548, 'num_poi':5583, 'num_edits':5583},
    {'region':'Denmark', 'usertype':'only_creators', 'num_users':659, 'num_poi':7773, 'num_edits':7773},
    {'region':'Guatemala', 'usertype':'only_creators', 'num_users':63, 'num_poi':637, 'num_edits':637},
    {'region':'India', 'usertype':'only_creators', 'num_users':926, 'num_poi':7316, 'num_edits':7316},
    {'region':'Philippines', 'usertype':'only_creators', 'num_users':479, 'num_poi':19728, 'num_edits':19728},
    {'region':'Belarus', 'usertype':'only_editors', 'num_users':237, 'num_poi':5509, 'num_edits':5975},
    {'region':'Denmark', 'usertype':'only_editors', 'num_users':385, 'num_poi':15649, 'num_edits':16294},
    {'region':'Guatemala', 'usertype':'only_editors', 'num_users':49, 'num_poi':218, 'num_edits':253},
    {'region':'India', 'usertype':'only_editors', 'num_users':262, 'num_poi':2548, 'num_edits':2682},
    {'region':'Philippines', 'usertype':'only_editors', 'num_users':203, 'num_poi':2594, 'num_edits':3117},
    {'region':'Belarus', 'usertype':'creators_and_editors', 'num_users':718, 'num_poi':103301, 'num_edits':132747},
    {'region':'Denmark', 'usertype':'creators_and_editors', 'num_users':1035, 'num_poi':2599237, 'num_edits':2934137},
    {'region':'Guatemala', 'usertype':'creators_and_editors', 'num_users':83, 'num_poi':7640, 'num_edits':15249},
    {'region':'India', 'usertype':'creators_and_editors', 'num_users':937, 'num_poi':390813, 'num_edits':421802},
    {'region':'Philippines', 'usertype':'creators_and_editors', 'num_users':595, 'num_poi':184362, 'num_edits':238036},
  ]
  
  df = pandas.DataFrame(data)
  # print df[df['region']=='Belarus']

  pivot = df.pivot(index='usertype', columns='region', values='num_poi')
  regions = pivot.columns
  groups = pivot.index.tolist()
  
  pivot_norm = pivot.astype(float) / pivot.sum()

  # Make plot
  fig = plt.figure()
  fig.patch.set_facecolor('white')

  N = len(regions)
  ind = np.arange(N)
  width = 0.35
  idx = 0
  bars = [None] * len(groups)
  colors = ['r', 'y', 'g']
  bottom = [0.0] * N
  for group in groups:
    region_values = pivot_norm.ix[group].values
    bars[idx] = plt.bar(ind, region_values, width, bottom=bottom, color=colors[idx])
    bottom += region_values
    idx += 1

  # Labels
  plt.title('Editing activity by user group')
  plt.xticks(ind + width/2., regions)
  plt.ylabel('Number of POI')
  plt.yticks([])
  plt.legend(bars, groups, loc=4)
  
  # Save to file.
  # plt.show()
  canvas = FigureCanvas(fig)
  output = cStringIO.StringIO()
  canvas.print_png('test.png')
