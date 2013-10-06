import argparse
import csv
import string

from app import *

# ========
# = Main =
# ========

def query_get_editing_group_activity(min_edits_per_user):
  query = string.Template(
    """SELECT r.name as region, 'only_creators' as usertype, 
    count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi,
    count(*) as num_edits 
    FROM users_20131005.poi_edits_only_creators a 
    JOIN users_20130923.temp_poi_changeset_max_5000 pc ON (a.poi_id=pc.poi_id and a.version=pc.version) 
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'only_editors' as usertype, 
    count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi,
    count(*) as num_edits 
    FROM users_20131005.poi_edits_only_editors a 
    JOIN users_20130923.temp_poi_changeset_max_5000 pc ON (a.poi_id=pc.poi_id and a.version=pc.version) 
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'creators_and_editors' as usertype, 
    count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, 
    count(*) as num_edits 
    FROM users_20131005.poi_edits_creators_and_editors a 
    JOIN users_20130923.temp_poi_changeset_max_5000 pc ON (a.poi_id=pc.poi_id and a.version=pc.version) 
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) GROUP BY r.name;""")
  return query.substitute(min_edits_per_user=min_edits_per_user)

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Query editing group activity levels for a given set of thresholds.')
  parser.add_argument('filename', help='output filename')
  parser.add_argument('--min_edits', dest='min_edits', default=0, 
      action='store', help='minimum number of edits per user')
  args = parser.parse_args()
  
  query = query_get_editing_group_activity(10)
  session = getSession()
  result = session.execute(query)

  outfile = open(args.filename, 'wb')
  outcsv = csv.writer(outfile, dialect='excel-tab')
  outcsv.writerow(result.keys())
  for row in result:
    outcsv.writerow(row)
  outfile.close()

  outfile = open(args.filename + '.query', 'wb')
  outfile.write(query)
  outfile.close()
