#depth = 5
#depth = 25
depth = 60
map_var = 'vwc'
input_dir = 'barnes_prediction/'
output_dir = 'merged_timeseries/'
output_fname = 'vwc_%dcm_barnes.csv'

import glob

fnames = glob.glob(input_dir + '*_%dcm*.csv' % (depth))

from pandas import read_csv
from datetime import datetime

#id_strip = lambda s: s.rstrip()
col = '%s_%d' % (map_var, depth)

dfs = []

i = 1
for fname in sorted(fnames):
    
    date_str = fname.split('.')[-2][-8:]
    date = datetime.strptime(date_str, '%Y%m%d')

    temp_df = read_csv(fname)
    #temp_df['site'] = temp_df['site'].apply(id_strip)

    temp_df = temp_df.rename(columns={'Z': col})
    temp_df = temp_df.set_index(['site', 'station'])
    temp_df = temp_df[[col]].transpose()

    temp_df['Timestamp'] = date
    temp_df = temp_df.set_index('Timestamp')

    dfs.append(temp_df)

from pandas import concat

df = concat(dfs)

df.to_csv(output_dir + output_fname % (depth))
