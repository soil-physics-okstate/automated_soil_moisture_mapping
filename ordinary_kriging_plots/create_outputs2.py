from sys import argv
from datetime import datetime
import pickle
from pandas import read_csv

### Parameters

## Command-line

#map_var = argv[1]
map_var = 'vwc'
date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depth = int(argv[2])

# set the date string
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# set the output directory
#output_dir = '../output/'
output_dir = './output/'

# load grid data
grid_df = pickle.load(open('../static_data/grid/soil_moisture_grid_ssurgo_stageiv.pickle'))

# Load ordinary-kriged VWC
prediction_file = output_dir + 'kriging_prediction/vwc/kriged_%dcm_%s.csv' % (depth, date_str)
prediction_df = read_csv(prediction_file, index_col=[0,1])
# Rename the columns
prediction_df.columns = ['vwc','vwc_var']


# combine and clean data
df = grid_df.join(prediction_df, on=['x','y'])
df = df.sort_index() # sort by (x, y)
df = df.reset_index() # put (x, y) back into the columns
df = df.dropna() # drop NaNs


# Output columns of interest
cols = ['id','vwc']
output_fname = '%s_%02dcm_%s.csv' % (map_var, depth, date_str)
df[cols].to_csv(output_dir + 'kriging_result/' + output_fname, index=False)
