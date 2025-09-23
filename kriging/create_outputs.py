from sys import argv
from datetime import datetime
import statsmodels.formula.api as smf

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

# set the output directory
output_dir = '../output/'

# load static data sources
import pickle

input_static_data_dir = '../static_data/'
# Change to migrate from python 2 to 3 (edited by Ali):
# Python 3 requires binary mode ('rb') when opening files for pickle.load(). 
print("start 0 ...")

grid_df = pickle.load(open(input_static_data_dir + 
                           'grid/soil_moisture_grid_ssurgo_stageiv_py3.pkl', 'rb'))
print("start 1 ..")

soil_df = pickle.load(open(input_static_data_dir + 
                              'soil_properties/ssurgo/ssurgo_soil_properties_by_mukey_py3.pkl', 'rb'))

# load dynamic data sources
input_dynamic_data_dir = '../dynamic_data/'
# Change to migrate from python 2 to 3 (edited by Ali):
# Python 3 requires binary mode ('rb') when opening files for pickle.load(). 

print("start..." + input_dynamic_data_dir + 'regression/model/model_%s.pkl' % (date_str))
def load_model(date_str):
    with open(input_dynamic_data_dir + 
              'regression/model/model_%s.pkl' % (date_str), 'rb') as f:
        return pickle.load(f)
    
model = load_model(date_str)

# model = pickle.load(open(input_dynamic_data_dir + 
#                         'regression/model/model_%s.pickle' % (date_str), 'rb'))
print("middle step ...")
model = model[depth] # choose only the model for the current depth
print(model)
api_file = input_dynamic_data_dir + 'precip/stageiv_api/api_%s.csv' % (date_str)
resid_file = output_dir + 'kriging_residual/kriged_%dcm_%s.csv' % (depth, date_str)

from pandas import read_csv

api_df = read_csv(api_file, index_col=[0,1])
resid_df = read_csv(resid_file, index_col=[0,1])
print(api_df.head())
print(resid_df.head())
# give the soil, api, and sm DataFrame column names
# that match the model results
soil_df.columns = ['%s_%d' % (col) for col in soil_df.columns.values]
api_df.columns = ['api_%s' % (col) for col in api_df.columns.values]

# combine and clean data
df = grid_df.join(soil_df['sand_%d' % (depth)], on='mukey')\
            .join(api_df['api_%d' % (depth)], on=['s4x', 's4y'])\
            .join(resid_df, on=['x', 'y'])
df = df.sort_index() # sort by (x, y)
df = df.reset_index() # put (x, y) back into the columns
df = df.dropna() # drop NaNs

# Predict values from model results
df[map_var] = ( (model.params * df).sum(axis=1) # sum the model params * values
                + model.params['Intercept']     # ... the model intercept
                + df['Z'] )                     # ... and the residuals
print ("Model prediction done.")
# Output columns of interest
cols = ['id','vwc']
output_fname = '%s_%02dcm_%s.csv' % (map_var, depth, date_str)
print("P1:" + output_dir + 'kriging_result/' + output_fname)
df[cols].to_csv(output_dir + 'kriging_result/' + output_fname, index=False)

cols = ['id','Z']
output_fname = '%s_%02dcm_%s.csv' % ('residual', depth, date_str)
df[cols].to_csv(output_dir + 'kriging_result/' + output_fname, index=False)
print("P1:" + output_dir + 'kriging_result/' + output_fname)

cols = ['id','Zvar']
output_fname = '%s_%02dcm_%s.csv' % ('variance', depth, date_str)
df[cols].to_csv(output_dir + 'kriging_result/' + output_fname, index=False)
print("P1:" + output_dir + 'kriging_result/' + output_fname)
