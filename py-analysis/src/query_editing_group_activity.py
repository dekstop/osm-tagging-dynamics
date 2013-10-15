import argparse
import csv
import string
import sys

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

def query_get_editing_group_activity(region_join_table, region_user_edit_stats_table, min_edits_per_user, max_changeset_size=None):
  query = string.Template("""SELECT r.name as region, 'only_creators' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM user_edits.poi_edits_only_creators a 
    $changeset_filter_join
    JOIN $region_user_edit_stats_table ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN $region_join_table rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'only_editors' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM user_edits.poi_edits_only_editors a 
    $changeset_filter_join
    JOIN $region_user_edit_stats_table ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN $region_join_table rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name
    UNION ALL
    SELECT r.name as region, 'creators_and_editors' as usertype, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(*) as num_edits 
    FROM user_edits.poi_edits_creators_and_editors a 
    $changeset_filter_join
    JOIN $region_user_edit_stats_table ue ON (a.uid=ue.uid AND ue.num_edits>=$min_edits_per_user) 
    JOIN $region_join_table rp ON (a.poi_id=rp.poi_id) 
    JOIN region r ON (rp.region_id=r.id) GROUP BY r.name;""")
  return query.substitute(
    region_join_table=region_join_table, 
    region_user_edit_stats_table=region_user_edit_stats_table, 
    min_edits_per_user=min_edits_per_user,
    changeset_filter_join=get_changeset_filter_join(max_changeset_size))

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Query editing group activity levels for a given set of thresholds.')
  parser.add_argument('filename', help='output filename')
  parser.add_argument('--max_changeset_size', dest='max_changeset_size', type=int, default=None, 
      action='store', help='maximum number of edits per changeset')
  parser.add_argument('--min_edits', dest='min_edits', type=int, default=0, 
      action='store', help='minimum number of edits per user')
  parser.add_argument('--region_join', dest='region_join_table', default='view_region_poi_latest', 
      action='store', help='region join table for this query (needs columns: region_id, poi_id), default: view_region_poi_latest')
  parser.add_argument('--edit_stats', dest='region_user_edit_stats_table', default='temp_region_user_edit_stats_20131011', 
      action='store', help='edit stats per region and user (needs columns: region_id, uid, num_edits), default: temp_region_user_edit_stats_20131011')
  args = parser.parse_args()
  
  print "Query with parameters:"
  print "  min_edits_per_user = %d" % (args.min_edits)
  print "  max_changeset_size = %d" % (args.max_changeset_size or 0)
  print "  region_join_table = %s" % (args.region_join_table)
  print "  region_user_edit_stats_table = %s" % (args.region_user_edit_stats_table)
  sys.stdout.flush()
  
  query = query_get_editing_group_activity(args.region_join_table, args.region_user_edit_stats_table, args.min_edits, args.max_changeset_size)
  getDb().echo = True
  session = getSession()
  result = session.execute(query)

  print "Writing result to %s" % (args.filename)
  save_result(result, args.filename)
  save_text(query, args.filename + '.query')
