#depth = 5
#depth = 25
depth = 60
map_var = 'vwc'
input_dir = 'kriging_prediction/resid/'
output_dir = 'merged_timeseries/'
output_fname = 'vwc_%dcm_residual_kriged.csv'

import glob

fnames = glob.glob(input_dir + '*_%dcm*.csv' % (depth))

import cPickle as pickle
from pandas import read_csv

info_df = pickle.load(open('../locations/all_sites_ssurgo_stageiv.pickle'))
soil_df = pickle.load(open('../../static_data/soil_properties/ssurgo/ssurgo_soil_properties_by_mukey.pickle'))
soil_df.columns = ['%s_%d' % (col) for col in soil_df.columns.values]

api_fname = '../../dynamic_data/precip/stageiv_api/api_%s.csv' # (date_str)
model_fname = '../../dynamic_data/regression/model/model_%s.pickle' # (date_str)

from datetime import datetime

id_strip = lambda s: s.rstrip()
col = '%s_%d' % (map_var, depth)

dfs = []

for fname in sorted(fnames):

    date_str = fname.split('.')[-2][-8:]
    date = datetime.strptime(date_str, '%Y%m%d')

    temp_df = read_csv(fname)
    temp_df['site'] = temp_df['site'].apply(id_strip)
    temp_df = temp_df.set_index(['site', 'station'])

    api_df = read_csv(api_fname % (date_str), index_col=[0,1])
    api_df.columns = ['api_%s' % (c) for c in api_df.columns.values]

    temp_df = temp_df.join(info_df[['mukey', 's4x', 's4y']])\
                     .join(soil_df['sand_%d' % (depth)], on='mukey')\
                     .join(api_df['api_%d' % (depth)], on=['s4x', 's4y'])

    model = pickle.load(open(model_fname % (date_str)))[depth]
    temp_df[col] = ( (model.params * temp_df).sum(axis=1) # sum the model params * values
                     + model.params['Intercept']          # ... the model intercept
                     + temp_df['Z'] )                     # ... and the residuals

    temp_df = temp_df[[col]].transpose()

    temp_df['Timestamp'] = date
    temp_df = temp_df.set_index('Timestamp')

    dfs.append(temp_df)

from pandas import concat

df = concat(dfs)

df.to_csv(output_dir + output_fname % (depth))
