import ConfigParser
import csv
import os, errno

from sqlalchemy import *
from sqlalchemy.orm import *

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

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
    return "%s%.1f%s" % (sign, x, suffix)
  else:
    return "%s%d%s" % (sign, int(x), suffix)
