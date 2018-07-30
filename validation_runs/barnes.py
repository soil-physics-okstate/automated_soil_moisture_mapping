from sys import argv

# get parameters
date_in = argv[1] # current date passed in as yyyy-mm-dd
depth = int(argv[2]) # depth to compute
map_var = 'vwc' # variable to compute
passes = 2 # number of passes in Barnes scheme

## Data

# set the base data directory and the date string
input_static_data_dir = '../static_data/'
input_dynamic_data_dir = '../dynamic_data/'
output_data_dir = '../output/barnes/'

from datetime import datetime
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

# load static (pickled) data sources
import cPickle as pickle

meso_df = pickle.load(open(input_static_data_dir +
                           'mesonet/mesonet_geoinfo_ssurgo_stageiv.pickle'))
#grid_df = pickle.load(open(input_static_data_dir + 
#                           'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
#grid_df = grid_df[['x', 'y']] # subset just the grid
grid_df = pickle.load(open('locations/all_sites.pickle'))

# load dynamic (CSV) data sources
from pandas import read_csv

sm_file = input_dynamic_data_dir + 'soil_moisture/06Z/sm_data_%s.csv' % (date_str)
sm_df = read_csv(sm_file, header=[0,1], index_col=0)

# combine header rows into single row
sm_df.columns = ['%s_%s' % (col) for col in sm_df.columns.values]

# combine everything into one DataFrame
from pandas import to_numeric
meso_df = meso_df.join(sm_df).apply(to_numeric)

import numpy as np

col = '%s_%d' % (map_var, depth)

# use only stations that reported soil moisture
meso_df = meso_df.dropna(subset=[col])

# grab the x, y, and variable (z) values for each station
(mxo, myo, mzo) = (meso_df['x'].values, meso_df['y'].values, meso_df[col].values)
mx = np.ma.array(mxo, mask=False)
my = np.ma.array(myo, mask=False)
mz = np.ma.array(mzo, mask=False)

# initialize storage for station distances
#Dxs = np.array([])
#Dys = np.array([])
Dns = np.array([])

# find and store nearest neighboring station distances
for i in xrange(len(mx)):

    # mask the current station from computation
    mx.mask[i] = True
    my.mask[i] = True

    # take the minimum distance from all other stations
    #Dxs = np.append(Dxs, np.min(np.abs(mxo[i] - mx)))
    #Dys = np.append(Dys, np.min(np.abs(myo[i] - my)))
    Dns = np.append(Dns, np.min(np.sqrt((mxo[i]-mx)**2 + (myo[i]-my)**2)))

    # unmask the current station
    mx.mask[i] = False
    my.mask[i] = False
    
# get the mean nearest neighbor distance
#Dx = np.mean(Dxs)
#Dy = np.mean(Dys)
Dn = np.mean(Dns)

# compute the falloff parameter
#kappa0_x = 5.052*(2 * Dx/np.pi)**2
#kappa0_y = 5.052*(2 * Dy/np.pi)**2
kappa0_n = 5.052*(2 * Dn/np.pi)**2

# interpolation to grid points
def barnes_interp((gx, gy)):

    # first pass
    gamma = 1
    w = np.exp(-((mxo-gx)**2 + (myo-gy)**2)/(kappa0_n * gamma))
    gz = np.sum(w*mzo)/np.sum(w)

    # subsequent passes
    gamma = 0.2
    w = np.exp(-((mxo-gx)**2 + (myo-gy)**2)/(kappa0_n * gamma))
    for ipass in xrange(passes-1):
        gz = gz + np.sum((mzo - gz)*w)/np.sum(w)    

    return gz

# leave-one-out cross-validation at station points
def barnes_crossval(i):

    # get station coordinates
    gx = mxo[i]
    gy = myo[i]

    # copy data arrays locally
    mzz = mz.copy()
    mxx = mx.copy()
    myy = my.copy()

    # mask station points
    mxx.mask[i] = True
    myy.mask[i] = True
    mzz.mask[i] = True

    # first pass
    gamma = 1
    w = np.exp(-((mxx-gx)**2 + (myy-gy)**2)/(kappa0_n * gamma))
    gz = np.sum(w*mzz)/np.sum(w)

    # subsequent passes
    gamma = 0.2
    w = np.exp(-((mxx-gx)**2 + (myy-gy)**2)/(kappa0_n * gamma))
    for ipass in xrange(passes-1):
        gz = gz + np.sum((mzz - gz)*w)/np.sum(w)    

    return gz

# get a list of all grid points
gxy = zip(grid_df['x'].values, grid_df['y'].values)

# set up the multiprocessing pool
#from multiprocessing import Pool
#pool = Pool(3)

# compute interpolation using pool
#grid_df[col] = pool.map(barnes_interp, gxy)
grid_df[col] = map(barnes_interp, gxy)

# compute cross-validation using pool
#meso_df[col + '_interp'] = pool.map(barnes_crossval, range(len(meso_df)))
meso_df[col + '_interp'] = map(barnes_crossval, xrange(len(meso_df)))
rmse = np.sqrt(np.mean((meso_df[col] - meso_df[col + '_interp'])**2))

# save
#grid_df.to_csv(output_data_dir + 'data/barnes_%dcm_%s.csv' % (depth, date_str))

output_dir = 'output/barnes_prediction/'
output_fname = 'barnes_%dcm_%s.csv'
grid_df.to_csv(output_dir + output_fname % (depth, date_str))

output_dir = 'output/barnes_rmse/'
output_fname = 'rmse_%dcm_%s.csv'
with open(output_dir + output_fname % (depth, date_str), 'w') as f:
    f.write('%f' % (rmse))
