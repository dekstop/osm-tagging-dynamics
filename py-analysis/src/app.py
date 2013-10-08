import ConfigParser
import csv
import os

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
