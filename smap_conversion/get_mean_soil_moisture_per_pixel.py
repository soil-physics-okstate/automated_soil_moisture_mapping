from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # get date string

# set depths and variables
sm_depths = [5]#[5, 25, 60]
sm_vars = ['vwc']

# set the data directory and filenames
data_dir = '../outputs/data/'
data_fname = 'oksmm_%s_%02dcm_%s.csv' # (var, depth, date)

# load SMAP pixels and pixel2id pickles
import pickle
smap_pixels = pickle.load(open('smap_pixels.pickle'))
pixel2id = pickle.load(open('pixel2id.pickle')).set_index('id')

# load data
from pandas import read_csv
import numpy as np

# loop over depths and vars
for d in sm_depths:
    for v in sm_vars:

        # load file and set index
        df = read_csv(data_dir + data_fname % (v, d, date_str)).set_index('id')

        # add smap_pixels
        df = df.join(pixel2id, how='inner')
        #df[['ease_column_index', 'ease_row_index']] = df[['ease_column_index', 'ease_row_index']].astype(int)
        
        # save mean vwc for each pixel
        vwc = df.groupby(['ease_column_index', 'ease_row_index']).agg(np.mean)['vwc']
        vwc.name = 'map_vwc'
        vwc.to_csv('../outputs/smap/ok_map_%s_%02dcm_%s.csv' % (v, d, date_str), header=True)
