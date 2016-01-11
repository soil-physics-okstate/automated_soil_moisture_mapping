### Decouple matplotlib from X
from matplotlib import use
use('agg')

### Parameters

## Command-line

#from sys import argv
#map_var = argv[1]
#depth = int(argv[2])
#date_in = argv[3]

from sys import argv
from datetime import datetime

map_var = 'vwc'
date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depth = int(argv[2])

print 'Creating map for %s...' % (date_in)

### Data

# set the base data directory and the date string
data_dir = '../data/'
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

## load static (usually pickle) data sources
import pickle

# map pickle
m = pickle.load(open('pickles/oklahoma_basemap.pickle')) # map object

grid_df = pickle.load(open(data_dir + 'grid/grid.pickle'))
sand_df = pickle.load(open(data_dir + 'soil_properties/ssurgo/sand_content.pickle'))

## load dynamic (usually CSV) data sources

precip_5day_file = data_dir + 'precip/stageiv_5_day/5_day_precip_%s.csv' % (date_str)
precip_30day_file = data_dir + 'precip/stageiv_30_day/30_day_precip_%s.csv' % (date_str)

model_file = data_dir + 'regression_models/model_%s.pickle' % (date_str)

resid_file = data_dir + 'kriging_residuals/daily_OKSMM_kriging_%dcm_%s.csv' % (depth, date_str)

from pandas import read_csv

precip_5day_df = read_csv(precip_5day_file, names=['x','y','precip_5day']).set_index(['x','y'])
precip_30day_df = read_csv(precip_30day_file, names=['x','y','precip_30day']).set_index(['x','y'])

model = pickle.load(open(model_file))[depth]

resid_df = read_csv(resid_file).set_index(['x', 'y']).sort_index()

## combine and clean data

df = grid_df.join(sand_df[depth], on='mukey')\
            .join(precip_5day_df, on=['stageiv_x', 'stageiv_y'])\
            .join(precip_30day_df, on=['stageiv_x', 'stageiv_y'])\
            .join(resid_df)
df.rename(columns={depth: 'sand_%d' % (depth)}, inplace=True) # set the sand column name
df.sort_index(inplace=True) # sort by (x, y)
df.reset_index(inplace=True) # put (x, y) back into the columns
df.dropna(inplace=True) # drop NaNs

### Parameters

## Map

# Oklahoma bounds 
# ('o' = origin at corner of Kingfisher/Logan/Canadian/Oklahoma counties)
lats = {'n':  37.1, 's':  33.6,  'c':  35.5, 'o':  35.726}
lons = {'e': -94.4, 'w': -103.0, 'c': -97.5, 'o': -97.674}

buf = 0.05 # plot buffer size [deg]

(dx, dy) = (800, 800) # pixel resolution [m]

# projection parameters
lon_0 = lons['o']  # x=0 at counties corner
lat_0 = lats['o']  # y=0 at counties corner

# lat_0 and lon_0 don't work right in Basemap,
# so record the offset here for later use
offset = m(lon_0, lat_0)

## Variables
map_vars = {
    'vwc': {
        'name': 'Volumetric Water Content', 
        'units': 'cm$^3$ cm$^{-3}$',
        'ticks': [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    },
    'MP': {
        'name': 'Matric Potential', 
        'units': 'kPa',
        'ticks': [-1000, -100, -10, -1]
    },
    'Se': {
        'name': 'Effective Saturation', 
        'units': 'fraction',
        'ticks': [0, 0.2, 0.4, 0.6, 0.8, 1]
    },
    'K': {
        'name': 'Hydraulic Conductivity', 
        'units': 'cm day$^{-1}$',
        'ticks': [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35]
    }
}

## Plots

(w, h) = (1280, 720) # width, height
dpi = 150. # screens are usually 96 dpi

cmap = 'RdYlBu' # color map

map_dir = '../outputs/maps/'
map_file = map_dir + 'oksmm_%sV2_%02dcm_%s.png' % (map_var, depth, date_in)

### Computation

## Predict values from model results
df[map_var] = (model.params * df).sum(axis=1)\
              + model.params['Intercept']\
              + df['Z']

## Put the grid in map coordinates
df['x'], df['y'] = (df['x'] + offset[0], df['y'] + offset[1])

## Create patch collection if necessary
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from os.path import exists

p_file = 'pickles/800m_patches_%dcm.pickle' % (depth)
if exists(p_file):
    p = pickle.load(open(p_file)) # patches object
else:
    xy_pairs = zip(df['x'].values - dx/2., df['y'].values - dy/2.)
    patches = [Rectangle(xy, width=dx, height=dx) for xy in xy_pairs]
    p = PatchCollection(patches, edgecolor='None')
    patches = None # clear memory
    pickle.dump(p, open(p_file, 'w'))

## Color patch collection based on soil moisture
#from negative_normalize import NegLogNorm

from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list('sm', ((1,0.95,0.7), (0.9,0.75,0.6), (0.3,0.5,1), (0,0,0.4)), N=60)

p.set_cmap(cmap) # set color map
if(map_vars[map_var]['ticks']):
    p.set_clim([min(map_vars[map_var]['ticks']), max(map_vars[map_var]['ticks'])]) # set color map limits
    if(map_var == 'MP'):
        p.set_norm(NegLogNorm(vmin = min(map_vars[map_var]['ticks']), vmax = max(map_vars[map_var]['ticks'])))
p.set_array(df[map_var].values) # determine colors based on sm values

## Get the RMSE from cross-validation
rmse = float(open('../outputs/cross_validation/oksmm_rmse_%dcm_%s.csv' % (depth, date_str)).read().rstrip())

## Plot the data on the map
import matplotlib.pyplot as plt

# Create the figure
size = (w/dpi, h/dpi)
fig = plt.figure(1, size, dpi=dpi)

# Get the current axes and add the soil moisture collection
ax = fig.add_axes([0, 0, 1, 1])
ax.add_collection(p)

# Use Oklahoma counties and state shapefile for plot background
m.readshapefile(data_dir + 'shapefiles/tl_2014_oklahoma_county/tl_2014_oklahoma_county', 'county', linewidth=0.5)
m.readshapefile(data_dir + 'shapefiles/tl_2014_oklahoma_state/tl_2014_oklahoma_state', 'state', linewidth=2)

# Initialize the map
m.drawmapboundary(linewidth=0)

# Add the colorbar
cbax = fig.add_axes([0.16, 0.32, 0.1, 0.42])
cbax.set_axis_off()
cb = fig.colorbar(p, ax = cbax, fraction = 1, aspect = 8, label = map_vars[map_var]['units'], spacing = 'proportional')
if(map_vars[map_var]['ticks']):
    cb.set_ticks(map_vars[map_var]['ticks'])

# Add text info
(llx, lly) = m(lons['w'] - buf, lats['s'] - buf*4)
(lrx, lry) = m(lons['e'] + buf, lats['s'] - buf*4)
ax.text(llx, lly, '%d-cm %s' % (depth, map_vars[map_var]['name']),
        size = 20, family = 'sans-serif', ha = 'left', va = 'bottom')
ax.text(lrx, lry, date_in,
        size = 14, family = 'sans-serif', ha = 'right', va = 'bottom')

# RMSE
#(rlat, rlon) = (36.332523, -101.501693)
(rlat, rlon) = (35.35, -102.35)
(rx, ry) = m(rlon, rlat)
ax.text(rx, ry, 'Cross-validation RMSE:\n%.3f %s' % (rmse, map_vars[map_var]['units']),
        size = 8, family = 'sans-serif', ha = 'center', va = 'center')

# Save the map
fig.savefig(map_file, dpi=dpi)

print '  Done.'
