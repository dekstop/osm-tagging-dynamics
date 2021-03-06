import matplotlib
matplotlib.use('Agg')

import csv
import matplotlib.pyplot as plt
import pandas
import string

import plot_100pc_stacked

# =========
# = Tools =
# =========

def get_data_filename(datadir, max_cs, min_edits):
  if max_cs == None:
    ftempl = string.Template("${datadir}/editing_group_activity_min_edits_${min_edits}.txt")
  else:
    ftempl = string.Template("${datadir}/editing_group_activity_max_cs_${max_cs}_min_edits_${min_edits}.txt")
  return ftempl.substitute(datadir=datadir, max_cs=max_cs, min_edits=min_edits)

# ========
# = Main =
# ========

if __name__ == "__main__":
  datadir = "/home/martind/osm/outputs/20131007-thresholds/data"
  outdir = "/home/martind/osm/outputs/20131007-thresholds"
  
  all_min_edits = [1, 2, 5, 10, 20, 50, 100, 200, 500]
  nrows = len(all_min_edits)
  all_max_cs = [None, 50000, 49500, 49000, 48000, 45000, 40000, 30000, 20000, 10000, 5000, 2000]
  ncols = len(all_max_cs)
  
  groupcol = 'usertype'
  aspectcol = 'region'
  valuecols = ['num_edits', 'num_poi', 'num_users']

  for valuecol in valuecols:
    outfiles = [
      outdir + '/all_countries_%s_volume.png' % (valuecol),
      outdir + '/all_countries_%s_volume.pdf' % (valuecol)]
    
    all = pandas.read_csv(get_data_filename(datadir, None, 1), index_col=None, dialect=csv.excel_tab)
    all_pivot = all.pivot(index=groupcol, columns=aspectcol, values=valuecol)

    fig = plt.figure(figsize=(8*ncols, 6*nrows))
    fig.patch.set_facecolor('white')
    plt.subplots_adjust(hspace=.2, wspace=0.1)
    n = 1
    for min_edits in all_min_edits:
      for max_cs in all_max_cs:
        plt.subplot(nrows, ncols, n)
      
        filename = get_data_filename(datadir, max_cs, min_edits)
        print filename
        df = pandas.read_csv(filename, index_col=None, dialect=csv.excel_tab)
        pivot = df.pivot(index=groupcol, columns=aspectcol, values=valuecol)
        groups = pivot.columns
        aspects = pivot.index.tolist()
      
        pivot_norm = pivot.astype(float) / all_pivot
      
        # Make plot
        plot_100pc_stacked.plot(pivot_norm, groups, aspects, 
          title="Min user edits: %s\nMax changeset size: %s" % (min_edits, max_cs or '-'), 
          nolegend=(n!=1), 
          colors=['#eeeeee', '#a8ddb5', '#a6bddb'])

        n += 1
  
    # Save to file.
    # plt.show()  
    for outfile in outfiles:
      print "saving " + outfile
      plt.savefig(outfile, bbox_inches='tight')
