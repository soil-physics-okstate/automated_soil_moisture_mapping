import numpy as np

seasons = [None] + ['winter']*2 + ['spring']*3 + ['summer']*3 + ['fall']*3 + ['winter']
seasons = np.array(seasons)

from pandas import read_csv

fname = 'output/xval_merged.csv'

df = read_csv(fname, parse_dates=True, index_col=0)
