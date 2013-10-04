from app import *

# ========
# = Main =
# ========

if __name__ == "__main__":
  print "Connecting to DB..."
  getDb().echo = True    
  initDb()
  
  print "Running a test query..."  
  session = getSession()
  result = session.execute("SELECT 1 as name")
  print result.keys()
  for f in result:
    print f
    print f[0]
    print len(f)

  print "All fine!"
