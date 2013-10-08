import argparse
import csv
import string

from app import *

# ========
# = Main =
# ========

# def get_poi_edit_filter_join(poi_edit_filter_table):
#   if poi_edit_filter_table==None:
#     return ""
#   join = string.Template("""JOIN $poi_edit_filter_table pf ON (a.poi_id=pf.poi_id and a.version=pf.version) """)
#   return join.substitute(poi_edit_filter_table=poi_edit_filter_table)

def get_changeset_filter_join(max_changeset_size):
  if max_changeset_size==None:
    return ""
  join = string.Template("JOIN (SELECT pf.id as poi_id, pf.version FROM poi pf JOIN changeset c ON (pf.changeset=c.id) WHERE num_nodes<=$max_changeset_size GROUP BY pf.id, pf.version) tf ON (a.poi_id=tf.poi_id and a.version=tf.version) ")
  return join.substitute(max_changeset_size=max_changeset_size)

def query_get_editing_group_activity(min_edits_per_user, max_changeset_size=None):
  query = string.Template("""SELECT r.name as region, 'only_creators' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM users_20131005.poi_edits_only_creators a 
    $changeset_filter_join
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'only_editors' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM users_20131005.poi_edits_only_editors a 
    $changeset_filter_join
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'creators_and_editors' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM users_20131005.poi_edits_creators_and_editors a 
    $changeset_filter_join
    JOIN users_20131005.region_user_edits ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN temp_region_poi_latest_20130910 rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) GROUP BY r.name;""")
  return query.substitute(
    min_edits_per_user=min_edits_per_user,
    changeset_filter_join=get_changeset_filter_join(max_changeset_size))

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Query editing group activity levels for a given set of thresholds.')
  parser.add_argument('filename', help='output filename')
  parser.add_argument('--max_changeset_size', dest='max_changeset_size', type=int, default=None, 
      action='store', help='maximum number of edits per changeset')
  parser.add_argument('--min_edits', dest='min_edits', type=int, default=0, 
      action='store', help='minimum number of edits per user')
  args = parser.parse_args()
  
  print "Query with parameters:"
  print "  min_edits_per_user = %d" % (args.min_edits)
  print "  max_changeset_size = %d" % (args.max_changeset_size or 0)
  query = query_get_editing_group_activity(args.min_edits, args.max_changeset_size)
  getDb().echo = True
  session = getSession()
  result = session.execute(query)

  print "Writing result to %s" % (args.filename)
  save_result(result, args.filename)
  save_text(query, args.filename + '.query')
