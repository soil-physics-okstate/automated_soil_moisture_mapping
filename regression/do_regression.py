from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depths = [5, 25, 60]

## Data

# set the base data directory and the date string
input_static_data_dir = '../static_data/'
input_dynamic_data_dir = '../dynamic_data/'
output_data_dir = '../dynamic_data/'
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# load static (pickled) data sources
# Change to migrate from python 2 to 3 (edited by Ali):
# cPickle was merged into pickle in Python 3.
import pickle
# Change to migrate from python 2 to 3 (edited by Ali):
# In Python 3, pickle.load() requires binary mode 'rb' for reading.
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

# give the soil, api, and sm DataFrame column names
# that can be used in OLS formulae
soil_df.columns = ['%s_%d' % (col) for col in soil_df.columns.values]
api_df.columns = ['api_%s' % (col) for col in api_df.columns.values]
sm_df.columns = ['%s_%s' % (col) for col in sm_df.columns.values]

# combine everything into one DataFrame
from pandas import to_numeric
df = meso_df.join(soil_df, on='mukey')\
            .join(api_df, on=['s4x', 's4y'])\
            .join(sm_df)\
            .apply(to_numeric)


## Calculation

import statsmodels.formula.api as smf

# store regression results in a dictionary
results = {}

import statsmodels.formula.api as smf

def run_regressions(df, depths, _date_str, _output_data_dir):
    results = {}

    for d in depths:
        formula = f'vwc_{d} ~ sand_{d} + api_{d}'
        results[d] = smf.ols(formula, data=df).fit()

        df[f'fit_{d}'] = results[d].fittedvalues
        df[f'resid_{d}'] = results[d].resid

    output_vars = ['x', 'y', 'resid_5', 'resid_25', 'resid_60']
    df[output_vars].to_csv(f'{_output_data_dir}regression/residual/resid_{date_str}.csv')

    with open(f'{_output_data_dir}regression/model/model_{_date_str}.pkl', 'wb') as f:
        pickle.dump(results, f)

# Example usage
run_regressions(df, depths=[5, 25, 60], _date_str=date_str, _output_data_dir = output_data_dir)


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
