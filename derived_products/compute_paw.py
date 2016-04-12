import sys
from datetime import datetime

### Parameters

## Command-line

if len(sys.argv) != 2:
    print 'Usage: compute_paw.py <yyyy-mm-dd>'
    sys.exit(1)

date_in = sys.argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# set the soil depths and layer thicknesses
depths = [5, 25, 60] # [cm]
thicks = [(10-0), (40-10), (80-40)] # [cm]

# set the output directory
output_dir = '../output/'

# load static data sources
import pickle

input_static_data_dir = '../static_data/'
grid_df = pickle.load(open(input_static_data_dir + 
                           'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
soil_df = pickle.load(open(input_static_data_dir + 
                              'soil_properties/ssurgo/ssurgo_soil_properties_by_mukey.pickle'))

# load dynamic data sources
from pandas import read_csv, concat
input_vwc_dir = '../output/kriging_result/'
input_vwc_fname = 'vwc_%02dcm_%s.csv' # (depth, date_str)

temp_dfs = []
for d in depths:
    temp_df = read_csv(input_vwc_dir + input_vwc_fname % (d, date_str))
    temp_df = temp_df.set_index('id')
    temp_df.columns = ['vwc_%02d' % (d)]
    temp_dfs.append(temp_df)
vwc_df = concat(temp_dfs, axis = 1)

# give the soil DataFrame column names based on depth
soil_df.columns = ['%s_%02d' % (col) for col in soil_df.columns.values]

# combine data
df = grid_df.join(soil_df, on='mukey')\
            .join(vwc_df)
df = df.sort_index() # sort by (x, y)

# compute PAW to 80 cm
import numpy as np
vwc_cols = ['vwc_%02d' % (d) for d in depths]
pwp_cols = ['pwp_%02d' % (d) for d in depths]
df = df.dropna(subset = vwc_cols + pwp_cols)
df['paw_80'] = np.sum(np.array(thicks)*np.maximum(df[vwc_cols].values - df[pwp_cols].values/100, 0), axis = 1)*10 # PAW reported in [mm]

# write to CSV
cols = ['id', 'paw_80']
df.reset_index()[cols].to_csv(output_dir + 'paw/paw_80cm_%s.csv' % (date_str), index=False)
