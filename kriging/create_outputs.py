from sys import argv
from datetime import datetime

### Parameters

## Command-line

#map_var = argv[1]
map_var = 'vwc'
date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depth = int(argv[2])

# set the base data directory and the date string
data_dir = '../data/'
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# set the output directory and output file name
output_dir = '../outputs/data/'
output_str = 'oksmm_%s_%02dcm_%s.csv' % (map_var, depth, date_str)

## load static (usually pickle) data sources
import pickle

grid_df = pickle.load(open(data_dir + 'grid/grid.pickle'))
xy2id_df = pickle.load(open(data_dir + 'grid/xy2id_lat_lon.pickle'))
sand_df = pickle.load(open(data_dir + 'soil_properties/ssurgo/sand_content.pickle'))

## load dynamic (usually CSV) data sources

precip_5day_file = data_dir + 'precip/stageiv_5_day/5_day_precip_%s.csv' % (date_str)
precip_30day_file = data_dir + 'precip/stageiv_30_day/30_day_precip_%s.csv' % (date_str)

model_file = data_dir + 'regression_models/model_%s.pickle' % (date_str)

resid_file = data_dir + 'kriging_residuals/daily_OKSMM_kriging_%dcm_%s.csv' % (depth, date_str)

from pandas import read_csv

precip_5day_df = read_csv(precip_5day_file, names=['x','y','precip_5day']).set_index(['x','y'])
precip_30day_df = read_csv(precip_30day_file, names=['x','y','precip_30day']).set_index(['x','y'])

model = pickle.load(open(model_file))[depth]

resid_df = read_csv(resid_file).set_index(['x', 'y']).sort_index()

## combine and clean data

df = grid_df.join(xy2id_df)\
            .join(sand_df[depth], on='mukey')\
            .join(precip_5day_df, on=['stageiv_x', 'stageiv_y'])\
            .join(precip_30day_df, on=['stageiv_x', 'stageiv_y'])\
            .join(resid_df)
df.rename(columns={depth: 'sand_%d' % (depth)}, inplace=True) # set the sand column name
df.sort_index(inplace=True) # sort by (x, y)
df.reset_index(inplace=True) # put (x, y) back into the columns
df.dropna(inplace=True) # drop NaNs

## Predict values from model results
df[map_var] = (model.params * df).sum(axis=1)\
              + model.params['Intercept']\
              + df['Z']

## Output columns of interest
cols = ['id','x','y','longitude','latitude','vwc']
df[cols].to_csv(output_dir + output_str, index=False)
