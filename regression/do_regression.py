from sys import argv
from datetime import datetime
import numpy as np

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depths = [10, 30, 60, 90] # depths for API

## Data

# set the base data directory and the date string
input_static_data_dir = '../static_data/'
input_dynamic_data_dir = '../dynamic_data/'
output_data_dir = '../dynamic_data/'
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# load static (pickled) data sources
import cPickle as pickle

meso_df = pickle.load(open(input_static_data_dir + 
                           'mesonet/mesonet_geoinfo_ssurgo_stageiv_py3.pkl', 'rb'))
soil_df = pickle.load(open(input_static_data_dir + 
                              'soil_properties/ssurgo/ssurgo_soil_properties_by_mukey_py3.pkl', 'rb'))

# load dynamic (CSV) data sources
from pandas import read_csv

api_file = input_dynamic_data_dir + 'precip/stageiv_api/api_%s.csv' % (date_str)
sm_file = input_dynamic_data_dir + 'soil_moisture/06Z/sm_data_%s.csv' % (date_str)

api_df = read_csv(api_file, index_col=[0,1])
sm_df = read_csv(sm_file, header=[0,1], index_col=0)

# # give the soil, api, and sm DataFrame column names
# # that can be used in OLS formulae
# print(soil_df.head())

# # soil_df.columns = ['%s_%d' % (col) for col in soil_df.columns.values]
# soil_df.columns = [
#     f"{col.split('.')[0]}_{col.split('.')[1] if '.' in col else 0}"
#     for col in soil_df.columns
# ]
# replace_map = {"0": "10", "1": "30", "2": "60", "3": "90"}

# new_cols = []
# for col in soil_df.columns:
#     base, suffix = col.split("_")
#     new_cols.append(f"{base}_{replace_map.get(suffix, suffix)}")

# soil_df.columns = new_cols
# api_df.columns = ['api_%s' % (col) for col in api_df.columns.values]
# sm_df.columns = ['%s_%s' % (col) for col in sm_df.columns.values]
# print(soil_df.columns)
# # combine everything into one DataFrame
# from pandas import to_numeric
# df = meso_df.join(soil_df, on='mukey')\
#             .join(api_df, on=['s4x', 's4y'])\
#             .join(sm_df)\
#             .apply(to_numeric)

# print(df.head())
# give the soil, api, and sm DataFrame column names
# that can be used in OLS formulae
import pandas as pd
from pandas import to_numeric

print(soil_df.head())

# --------------------------------------------------
# Fix soil_df: first column is the mukey, not the index
# --------------------------------------------------

soil_df = soil_df.copy()

# The first column appears to contain the mukey values
soil_key_col = soil_df.columns[0]
soil_df = soil_df.rename(columns={soil_key_col: "mukey"})

# Remove the first metadata/depth row if mukey is missing
soil_df = soil_df[soil_df["mukey"].notna()].copy()

# Rename soil-property columns to depth-specific names
# Example:
# sand   -> sand_10
# sand.1 -> sand_30
# sand.2 -> sand_60
# sand.3 -> sand_90
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

        depth = replace_map.get(suffix, suffix)
        new_cols.append(f"{base}_{depth}")

soil_df.columns = new_cols

# Make mukey type consistent between meso_df and soil_df
soil_df["mukey"] = pd.to_numeric(soil_df["mukey"], errors="coerce").astype("Int64")
meso_df["mukey"] = pd.to_numeric(meso_df["mukey"], errors="coerce").astype("Int64")

# Remove bad or duplicate mukeys in soil table
soil_df = soil_df.dropna(subset=["mukey"])
soil_df = soil_df.drop_duplicates(subset=["mukey"])

# Use mukey as soil_df index so meso_df.join(..., on="mukey") works correctly
soil_df = soil_df.set_index("mukey")

print("\nCorrected soil_df columns:")
print(soil_df.columns)

print("\nSoil_df index sample:")
print(soil_df.index[:10])

# Rename API and soil moisture columns
api_df.columns = [f"api_{col}" for col in api_df.columns.values]
sm_df.columns = [f"{col[0]}_{col[1]}" for col in sm_df.columns.values]

# combine everything into one DataFrame
df = meso_df.join(soil_df, on="mukey") \
            .join(api_df, on=["s4x", "s4y"]) \
            .join(sm_df) \
            .apply(to_numeric)

print("\nCombined dataframe preview:")
print(df.head())

print("\nCheck soil variables after merge:")
for d in [10, 30, 60, 90]:
    print(f"sand_{d} non-NaN:", df[f"sand_{d}"].notna().sum())





## Calculation

import statsmodels.formula.api as smf

# store regression results in a dictionary
results = {}

# do the fitting for each depth
# for d in depths:
#     formula = 'vwc_%d ~ sand_%d + api_%d' % (d, d, d)
#     results[d] = smf.ols(formula, data=df).fit()

#     # save the fitted values and residual values to the dataframe
#     df['fit_%d' % (d)] = results[d].fittedvalues
#     df['resid_%d' % (d)] = results[d].resid

# # output the variables needed for the kriging routine
# output_vars = ['x', 'y', 'resid_5', 'resid_25', 'resid_60']
# df[output_vars].to_csv(output_data_dir + 
#                        'regression/residual/resid_%s.csv' % (date_str))

# save the model results
# Change to migrate from python 2 to 3 (edited by Ali):
# In Python 3, pickle.dump() requires binary mode 'wb' for writing.
# pickle.dump(results, open(output_data_dir + 
#                           'regression/model/model_%s.pickle' % (date_str), 'wb'))
