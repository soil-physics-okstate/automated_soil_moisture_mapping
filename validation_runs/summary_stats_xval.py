from pandas import read_csv
import numpy as np

df = read_csv('output/xval_merged.csv', index_col=[0,1])

def rmse(df, col):
    return np.sqrt(np.mean(df[col]**2))

def mae(df, col):
    return np.mean(np.abs(df[col]))

def bias(df, col):
    return np.mean(df[col])

def corr(df, col1, col2):
    return df[col1].corr(df[col2])

schemes = ['barnes', 'ok', 'rk']
print '\tRMSE\tMAE\tBias\tCorr'
for scheme in schemes:
    col = 'bias_%s' % (scheme)
    print '%s\t' % (scheme),
    print '%.3g\t' % (rmse(df, col)),
    print '%.3g\t' % (mae(df, col)),
    print '%.1g\t' % (bias(df, col)),

    col1 = 'vwc'
    col2 = 'vwc_%s' % (scheme)
    print '%.3g' % (corr(df, col1, col2))
