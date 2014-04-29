import csv
import os, errno

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

