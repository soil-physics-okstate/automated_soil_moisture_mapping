import glob

interps = ['barnes', 'ok', 'rk']
#depth = 5
#depth = 25
depth = 60

n = len(glob.glob('xval_rk/*_%dcm*.csv' % (depth)))

from pandas import read_csv, concat
from datetime import datetime

dfs = []
for i,interp in enumerate(interps):
    map_var = ['vwc', 'resid'][interp == 'rk']

    temp_dfs = []
    for j,fname in enumerate(glob.glob('xval_%s/*_%dcm*.csv' % (interp,depth))):
        temp_df = read_csv(fname)
        temp_df['bias_%s' % (interp)] = temp_df['%s_%s' % (map_var, interp)] - temp_df[map_var]
        temp_df['date'] = datetime.strptime(fname[-12:-4], '%Y%m%d')
        temp_dfs.append(temp_df)

        print '%d of %d interps, %4d of %4d dates' % (i+1, len(interps)+1, j+1, n)
    
    temp_df = concat(temp_dfs).set_index(['date', 'STID'])
    if interp == 'barnes': temp_df = temp_df.drop(map_var, axis=1)
    
    dfs.append(temp_df)

i += 1
temp_dfs = []
for j,fname in enumerate(glob.glob('xval_rk_vwc/*_%02dcm*.csv' % (depth))):
    temp_df = read_csv(fname)
    temp_df['date'] = datetime.strptime(fname[-12:-4], '%Y%m%d')
    temp_dfs.append(temp_df)
    print '%d of %d interps, %4d of %4d dates' % (i+1, len(interps)+1, j+1, n)
temp_df = concat(temp_dfs).set_index(['date', 'STID'])
dfs.append(temp_df)

df = concat(dfs, axis=1)
df.to_csv('xval_merged_%dcm.csv' % (depth))

