from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object

print 'Regressing soil moisture against sand content and precipitation for %s...' % (date_in)

## Data

# set the base data directory and the date string
data_dir = '../data/'
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# load static (pickled) data sources
import pickle

meso_df = pickle.load(open(data_dir + 'grid/mesonet_geoinfo.pickle'))
sand_df = pickle.load(open(data_dir + 'soil_properties/ssurgo/sand_content.pickle'))

# load dynamic (CSV) data sources

precip_5day_file = data_dir + 'precip/stageiv_5_day/5_day_precip_%s.csv' % (date_str)
precip_30day_file = data_dir + 'precip/stageiv_30_day/30_day_precip_%s.csv' % (date_str)
sm_file = data_dir + 'soil_moisture/midnight/sm_data_%s.csv' % (date_str)

from pandas import read_csv

precip_5day_df = read_csv(precip_5day_file, names=['x','y','precip_5day']).set_index(['x','y'])
precip_30day_df = read_csv(precip_30day_file, names=['x','y','precip_30day']).set_index(['x','y'])
sm_df = read_csv(sm_file, header=[0,1], index_col=0)

# need to fix the soil moisture DataFrame columns to have integer depths
# the levels are sorted by string value, which is why 25 comes first
sm_df.columns.set_levels(level=1, levels=[25,5,60], inplace=True)

# combine data
df = meso_df.join(sand_df, on='mukey')\
            .join(sm_df['vwc'], lsuffix='_sand', rsuffix='_vwc')\
            .join(precip_5day_df, on=['s4x', 's4y'])\
            .join(precip_30day_df, on=['s4x', 's4y'])

depths = [5, 25, 60]
for d in depths: # OLS function cannot handle leading numbers in variables
    df.rename(inplace=True, columns={'%d_vwc' % (d): 'vwc_%d' % (d),
                                     '%d_sand' % (d): 'sand_%d' % (d)})

## Calculation

import statsmodels.formula.api as smf

# store regression results in dictionary
results = {}

# do the fitting for each depth
for d in depths:
    formula = 'vwc_%d ~ x + y + sand_%d + precip_5day + precip_30day' % (d, d)
    results[d] = smf.ols(formula, data=df).fit()

    # save the fitted values and residual values to the dataframe
    df['fit_%d' % (d)] = results[d].fittedvalues
    df['resid_%d' % (d)] = results[d].resid

# output the variables needed for the kriging routine
output_vars = ['x', 'y', 'resid_5', 'resid_25', 'resid_60']
df[output_vars].to_csv(data_dir + 'regression_residuals/resid_%s.csv' % (date_str))

# save the model results
pickle.dump(results, open(data_dir + 'regression_models/model_%s.pickle' % (date_str), 'w'))

print '  Done.'
