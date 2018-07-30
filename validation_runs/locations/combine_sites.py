sites = ['smap', 'jfsp']

import os
import cPickle as pickle

mat_dict = {'site': [], 'station': [], 'x': [], 'y': []}
dfs = []

for site in sites:
    f = '%s_sites.pickle' % (site)
    df = pickle.load(open(f)).reset_index()
    dfs.append(df)

    for col in mat_dict:
        mat_dict[col] = mat_dict[col] + list(df[col].values)

from scipy.io import savemat
savemat('all_sites.mat', mat_dict)

from pandas import concat
df = concat(dfs).set_index(['site', 'station'])
df.to_pickle('all_sites.pickle')
df.to_csv('all_sites.csv')
