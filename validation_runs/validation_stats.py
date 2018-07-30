map_var = 'vwc'
depth = 5

import numpy as np

seasons = [None] + ['winter']*2 + ['spring']*3 + ['summer']*3 + ['fall']*3 + ['winter']
seasons = np.array(seasons)

from pandas import read_csv

fnames = {
    'data': 'data/clean/%s_%dcm_all_sites.csv',
    'ba': 'output/merged_timeseries/%s_%dcm_barnes.csv',
    'rk': 'output/merged_timeseries/%s_%dcm_residual_kriged.csv',
    'ok': 'output/merged_timeseries/%s_%dcm_ordinary_kriged.csv'
}

# the arguments are the same across all read_csv functions
kwargs = {'header': [0, 1], 'index_col': 0, 'parse_dates': True}

dfs = {}
for f in fnames:
    dfs[f] = read_csv(fnames[f] % (map_var, depth), **kwargs)

interps = ['ba', 'ok', 'rk']
stats = ['rmse', 'bias', 'ubrmse', 'r']
stats_dfs = []

from pandas import Series
for i in interps:
    
    rmse = np.sqrt(np.mean((dfs[i] - dfs['data'])**2))
    rmse.name = '%s_rmse' % (i)

    bias = np.mean(dfs[i] - dfs['data'])
    bias.name = '%s_bias' % (i)

    ubrmse = np.sqrt(np.mean(((dfs[i] - bias) - dfs['data'])**2))
    ubrmse.name = '%s_ubrmse' % (i)

    mae = np.mean(np.abs(dfs[i] - dfs['data']))
    mae.name = '%s_mae' % (i)

    r = Series(index = rmse.index)
    for site in dfs['data'].columns:
        r.loc[site] = dfs[i][site].corr(dfs['data'][site])
    r.name = '%s_r' % (i)

    stats_dfs += [rmse, bias, ubrmse, mae, r]

from pandas import concat

stats_df = concat(stats_dfs, axis=1)
