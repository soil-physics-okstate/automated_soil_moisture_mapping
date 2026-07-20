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

# give the soil, api, and sm DataFrame column names
# that match the model results
import pandas as pd
import numpy as np

# --------------------------------------------------
# Fix soil_df: first column is mukey, not the index
# --------------------------------------------------

soil_df = soil_df.copy()

soil_key_col = soil_df.columns[0]
soil_df = soil_df.rename(columns={soil_key_col: "mukey"})

# Remove metadata/depth row where mukey is missing
soil_df = soil_df[soil_df["mukey"].notna()].copy()

replace_map = {"0": "10", "1": "30", "2": "60", "3": "90"}

new_cols = []
for col in soil_df.columns:
    col = str(col)

    if col == "mukey":
        new_cols.append("mukey")
    else:
        if "." in col:
            base, suffix = col.split(".", 1)
        else:
            base, suffix = col, "0"

        depth_name = replace_map.get(suffix, suffix)
        new_cols.append(f"{base}_{depth_name}")

soil_df.columns = new_cols

# Make mukey type consistent
soil_df["mukey"] = pd.to_numeric(soil_df["mukey"], errors="coerce").astype("Int64")
grid_df["mukey"] = pd.to_numeric(grid_df["mukey"], errors="coerce").astype("Int64")

soil_df = soil_df.dropna(subset=["mukey"])
soil_df = soil_df.drop_duplicates(subset=["mukey"])
soil_df = soil_df.set_index("mukey")

# Rename API columns
api_df.columns = [f"api_{col}" for col in api_df.columns.values]

print("\nCreate outputs check:")
print(f"sand_{depth} exists:", f"sand_{depth}" in soil_df.columns)
print(f"sand_{depth} non-NaN in soil_df:", soil_df[f"sand_{depth}"].notna().sum())

# --------------------------------------------------
# Combine grid, soil, API, and kriged residual
# --------------------------------------------------

df = grid_df.join(soil_df[f"sand_{depth}"], on="mukey") \
            .join(api_df[f"api_{depth}"], on=["s4x", "s4y"]) \
            .join(resid_df, on=["x", "y"])

print("Rows before dropna:", df.shape[0])
print("NaN count before dropna:")
print(df[[f"sand_{depth}", f"api_{depth}", "Z", "Zvar"]].isna().sum())

df = df.sort_index()
df = df.reset_index()
df = df.dropna()

print("Rows after dropna:", df.shape[0])

if df.shape[0] == 0:
    raise RuntimeError(
        f"create_outputs.py produced zero rows for {depth} cm. "
        f"Check sand_{depth}, api_{depth}, and kriged residual join."
    )




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
