import argparse
import csv
import string
import sys

from app import *

# ========
# = Main =
# ========

def get_changeset_filter_join(max_changeset_size):
  if max_changeset_size==None:
    return ""
  join = string.Template("JOIN (SELECT pf.id as poi_id, pf.version FROM poi pf JOIN changeset c ON (pf.changeset=c.id) WHERE num_nodes<=$max_changeset_size GROUP BY pf.id, pf.version) tf ON (a.poi_id=tf.poi_id and a.version=tf.version) ")
  return join.substitute(max_changeset_size=max_changeset_size)

def get_min_edits_filter_join(region_user_edit_stats_table, min_edits_per_user):
  if min_edits_per_user==None:
    return ""
  join = string.Template("JOIN $region_user_edit_stats_table ue ON (a.uid=ue.uid AND ue.region_id=rp.region_id AND ue.num_edits>=$min_edits_per_user) ")
  return join.substitute(
    region_user_edit_stats_table=region_user_edit_stats_table,
    min_edits_per_user=min_edits_per_user)

def query_get_community_growth(date_format, region_join_table, region_user_edit_stats_table, min_edits_per_user=None, max_changeset_size=None):
  query = string.Template("""SELECT r.name as region, to_char(p.timestamp, '$date_format') as period, count(distinct a.uid) as num_users, count(distinct a.poi_id) as num_poi, count(distinct p.changeset) as num_changesets, count(*) as num_edits 
    FROM user_edits.poi_all_edits a 
    $changeset_filter_join
    JOIN poi p ON (a.poi_id=p.id AND a.version=p.version) 
    JOIN $region_join_table rp ON (a.poi_id=rp.poi_id) 
    $min_edits_filter_join
    JOIN region r ON (rp.region_id=r.id) 
    GROUP BY r.name, period;""")
  return query.substitute(
    date_format=date_format,
    region_join_table=region_join_table,
    min_edits_filter_join=get_min_edits_filter_join(region_user_edit_stats_table, min_edits_per_user),
    changeset_filter_join=get_changeset_filter_join(max_changeset_size))

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Query editing group activity levels for a given set of thresholds.')
  parser.add_argument('filename', help='output filename')
  parser.add_argument('--date_format', dest='date_format', default='YYYY-MM', 
      action='store', help='PostgreSQL date format used for aggregations')
  parser.add_argument('--max_changeset_size', dest='max_changeset_size', type=int, default=None, 
      action='store', help='maximum number of edits per changeset')
  parser.add_argument('--min_edits', dest='min_edits', type=int, default=1, 
      action='store', help='minimum number of edits per user')
  parser.add_argument('--region_join', dest='region_join_table', default='view_region_poi_latest', 
      action='store', help='region join table for this query (needs columns: region_id, poi_id), default: view_region_poi_latest')
  parser.add_argument('--edit_stats', dest='region_user_edit_stats_table', default='temp_region_user_edit_stats_20131011', 
      action='store', help='edit stats per region and user (needs columns: region_id, uid, num_edits), default: temp_region_user_edit_stats_20131011')
  args = parser.parse_args()
  
  print "Query with parameters:"
  print "  date_format = %s" % (args.date_format)
  print "  min_edits_per_user = %d" % (args.min_edits or 0)
  print "  max_changeset_size = %d" % (args.max_changeset_size or 0)
  print "  region_join_table = %s" % (args.region_join_table)
  print "  region_user_edit_stats_table = %s" % (args.region_user_edit_stats_table)
  sys.stdout.flush()
  
  query = query_get_community_growth(args.date_format, args.region_join_table, args.region_user_edit_stats_table, args.min_edits, args.max_changeset_size)
  getDb().echo = True
  session = getSession()
  result = session.execute(query)

  print "Writing result to %s" % (args.filename)
  save_result(result, args.filename)
  save_text(query, args.filename + '.query')
