map_var = 'vwc'
depth = 5

from pandas import read_csv

# the arguments are the same across all read_csv functions
kwargs = {'header': [0, 1], 'index_col': 0, 'parse_dates': True}

df = read_csv('output/merged_timeseries/%s_%dcm_residual_kriged.csv' % (map_var, depth),
              **kwargs)

df = df[('JFSP', '4')]
