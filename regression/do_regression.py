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
import cPickle as pickle

meso_df = pickle.load(open(input_static_data_dir + 
                           'mesonet/mesonet_geoinfo_ssurgo_stageiv.pickle'))
texture_df = pickle.load(open(input_static_data_dir + 
                              'soil_properties/ssurgo/ssurgo_texture_by_mukey.pickle'))

# load dynamic (CSV) data sources
from pandas import read_csv

api_file = input_dynamic_data_dir + 'precip/stageiv_api/api_%s.csv' % (date_str)
sm_file = input_dynamic_data_dir + 'soil_moisture/06Z/sm_data_%s.csv' % (date_str)

api_df = read_csv(api_file, index_col=[0,1])
sm_df = read_csv(sm_file, header=[0,1], index_col=0)

# give the texture, api, and sm DataFrame column names
# that can be used in OLS formulae
texture_df.columns = ['%s_%d' % (col) for col in texture_df.columns.values]
api_df.columns = ['api_%s' % (col) for col in api_df.columns.values]
sm_df.columns = ['%s_%s' % (col) for col in sm_df.columns.values]

# combine everything into one DataFrame
from pandas import to_numeric
df = meso_df.join(texture_df, on='mukey')\
            .join(api_df, on=['s4x', 's4y'])\
            .join(sm_df)\
            .apply(to_numeric)


## Calculation

import statsmodels.formula.api as smf

# store regression results in a dictionary
results = {}

# do the fitting for each depth
for d in depths:
    formula = 'vwc_%d ~ sand_%d + api_%d' % (d, d, d)
    results[d] = smf.ols(formula, data=df).fit()

    # save the fitted values and residual values to the dataframe
    df['fit_%d' % (d)] = results[d].fittedvalues
    df['resid_%d' % (d)] = results[d].resid

# output the variables needed for the kriging routine
output_vars = ['x', 'y', 'resid_5', 'resid_25', 'resid_60']
df[output_vars].to_csv(output_data_dir + 
                       'regression/residual/resid_%s.csv' % (date_str))

# save the model results
pickle.dump(results, open(output_data_dir + 
                          'regression/model/model_%s.pickle' % (date_str), 'w'))
