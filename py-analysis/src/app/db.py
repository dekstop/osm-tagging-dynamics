import ConfigParser
import os

import psycopg2.extensions

from sqlalchemy import *
from sqlalchemy.orm import *

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

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
