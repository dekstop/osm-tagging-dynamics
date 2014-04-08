from collections import defaultdict
import ConfigParser
import csv
import os, errno

import psycopg2.extensions

from sqlalchemy import *
from sqlalchemy.orm import *

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

import matplotlib.pyplot as plt

# ============
# = Psycopg2 =
# ============

# Load all decimal numbers as float from the DB.
# This avoids lots of tedious type conversions necessiated for numpy.
# Any potential loss in precision isn't a big concern for our kind of work.
DEC2FLOAT = psycopg2.extensions.new_type(
  psycopg2.extensions.DECIMAL.values,
  'DEC2FLOAT',
  lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)

# ==============
# = DB Session =
# ==============

config = None
db = None
Session = None
session = None

def getConfig():
    global config
    if (config==None):
        SETTINGS_FILE=os.environ['SETTINGS_FILE']
        config = ConfigParser.ConfigParser()
        config.readfp(open(SETTINGS_FILE))
    return config

def getDb():
    global db
    if (db==None):
        db = create_engine(getConfig().get('db', 'uri'))
        # db.echo = True
    return db

def initDb():
    Base.metadata.create_all(getDb())

def getSession():
    global Session, session
    if (Session==None):
        Session = sessionmaker(bind=getDb())
    if (session==None):
        session = Session()
    return session

# ============
# = File I/O =
# ============

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

# Write a SQLAlchemy Result object to a TSV file.
def save_result(result, filename):
  outfile = open(filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(result.keys())
  for row in result:
    outcsv.writerow(row)
  outfile.close()

# Write a string-like object to a text file.
def save_text(text, filename):
  outfile = open(filename, 'wb')
  outfile.write(text)
  outfile.close()

# ==================
# = Plotting tools =
# ==================

CLASSIC_COLORS = ['b', 'c', 'm', 'y', 'r', 'k']

LIGHT_COLOR = '#EEEEEE'

# Broadly color-blind suitable.
# Cf. http://www.colourlovers.com/lover/martind/palettes
QUALITATIVE_LIGHT = ['#A8DDB5', '#A6BDDB', '#E8AFB8', '#FFEEB3', '#BBE0E8']
QUALITATIVE_MEDIUM = ['#9BDDAB', '#98BCEB', '#F29DAB', '#F2DD91', '#8BD8E8']
QUALITATIVE_DARK = ['#6EDD89', '#75A8EB', '#F2798C', '#F2D779', '#74D3E8']

# Temp hack to show filtered top/bottom bands
# QUALITATIVE_LIGHT = ['#EEEEEE', '#A8DDB5', '#A6BDDB', '#E8AFB8', '#FFEEB3', '#BBE0E8', '#EEEEEE']
# QUALITATIVE_MEDIUM = ['#EEEEEE', '#9BDDAB', '#98BCEB', '#F29DAB', '#F2DD91', '#8BD8E8', '#EEEEEE']
# QUALITATIVE_DARK = ['#EEEEEE', '#6EDD89', '#75A8EB', '#F2798C', '#F2D779', '#74D3E8', '#EEEEEE']

# 123456 -> "123.5k".
# The resulting string should never be longer than 6 characters. (Unless it's a massively large number...)
# TODO: support small fractions < 0.1
def simplified_SI_format(x, p):
  suffixes = ['k', 'M', 'G', 'T', 'P']
  suffix = ''
  is_fractional = (x<1 and x!=0)
  sign = ''
  if x < 0:
    x *= -1
    sign = '-'

  scale_idx = 0
  while (x >= 1000 and scale_idx<len(suffixes)):
    x /= 1000.0
    suffix = suffixes[scale_idx]
    is_fractional = True
    scale_idx += 1

  if is_fractional:
    return "%s%.2f%s" % (sign, x, suffix)
  else:
    return "%s%d%s" % (sign, int(x), suffix)

def to_percent(x, position):
  p = str(100 * x)
  return p + '%'  

def to_even_percent(x, position):
  p = str(int(100 * x))
  return p + '%'

# Returns an infinite sequence of the provided list (wrapped around)
# This is used to produce color palettes of infinite length.
def looping_generator(list):
  idx = 0
  while True:
    yield(list[idx])
    idx = (idx+1) % len(list)

def autoscale_axes_xlim(axes):
  limits = [ax1.get_xlim() for ax1 in axes]
  left = min([v[0] for v in limits])
  right = max([v[1] for v in limits])
  for ax1 in axes:
    ax1.set_xlim(left, right)

def autoscale_axes_ylim(axes):
  limits = [ax1.get_ylim() for ax1 in axes]
  bottom = min([v[0] for v in limits])
  top = max([v[1] for v in limits])
  for ax1 in axes:
    ax1.set_ylim(bottom, top)

# A generator that prepares a matrix layout of subplots and yields a tuple for each cell.
# This iterates over rows first -- i.e., the fist tuples returned are for the top row of cells.
# 
# Expected parameters:
# - columns: list of column names for this matrix
# - rows: list of row names
# 
# Optional parameters:
# - cellwidth:
# - cellheight:
# - shared_xscale: maintain x-axis range along cells in the same column?
# - xgroups: a nested list of column names, this can be used to link related columns that should have the same x-axis range: ['a', 'b', ['c', 'd']]
# - shared_xscale: maintain y-axis range along cells in the same row?
# 
# The tuple yielded per cell contains the values:
# - col: the column name for this cell
# - row: the row name
# - ax1: a matplotlib subplot handle
def plot_matrix(columns, rows, cellwidth=3, cellheight=3, shared_xscale=False, 
  xgroups=None, shared_yscale=False, hspace=0.2, wspace=0.2):
  
  ncols = len(columns)
  nrows = len(rows)

  fig = plt.figure(figsize=(cellwidth*ncols, cellheight*nrows))
  plt.subplots_adjust(hspace=hspace, wspace=wspace)
  fig.patch.set_facecolor('white')

  # dict: row -> column -> ax1
  axes = defaultdict(dict)
  n = 1
  for row in rows:
    for column in columns:

      if n <= ncols: # first row
        ax1 = plt.subplot(nrows, ncols, n, title=column)
      else:
        ax1 = plt.subplot(nrows, ncols, n)
      axes[row][column] = ax1
      
      if (n % ncols == 1): # first column
        plt.ylabel(row)
      
      yield (column, row, ax1)
      n += 1

    if shared_yscale: # for every row: shared scale across columns?
      autoscale_axes_ylim(axes[row].values())

  if shared_xscale: # for every column: shared scale across rows?
    if xgroups==None:
      xgroups = columns
    for xgroup in xgroups:
      if isinstance(xgroup, list):
        group_axes = [axes[row][col] for row in axes.keys() for col in xgroup]
        autoscale_axes_xlim(group_axes)
      else:
        group_axes = [axes[row][xgroup] for row in axes.keys()]
        autoscale_axes_xlim(group_axes)
