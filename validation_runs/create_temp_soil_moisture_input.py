import sys

if len(sys.argv) != 3:
    print 'Usage: create_temp_soil_moisture_input.py <date> <depth>'
    sys.exit(1)

date = sys.argv[1]
depth = int(sys.argv[2])
map_var = 'vwc'

from datetime import datetime

date = datetime.strptime(date, '%Y-%m-%d')
date_str = date.strftime('%Y%m%d')

sm_input_dir = '../dynamic_data/soil_moisture/06Z/'
sm_input_fname = 'sm_data_%s.csv' # (yyyymmdd)

grid_input_dir = '../static_data/mesonet/'
grid_input_fname = 'mesonet_geoinfo_ssurgo_stageiv.pickle'

import cPickle as pickle

grid_df = pickle.load(open(grid_input_dir + grid_input_fname))

from pandas import read_csv

sm_df = read_csv(sm_input_dir + sm_input_fname % (date_str), header=[0,1], index_col=0)

df = grid_df[['x', 'y']].join(sm_df[map_var, str(depth)])
df.columns = ['x', 'y', '%s_%d' % (map_var, depth)]

output_dir = 'tmp/'
output_fname = 'meso_soil_moisture_%dcm_%s.csv' # (depth, date_str)

df.to_csv(output_dir + output_fname % (depth, date_str))
