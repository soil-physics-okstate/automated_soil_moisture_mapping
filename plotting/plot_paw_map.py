### Parameters

## Command-line
from sys import argv, exit
if len(argv) != 3: exit('Usage: plot_soil_moisture_map.py <date yyyy-mm-dd> <depth [cm]>')
date_in = argv[1] # current date passed in as yyyy-mm-dd
depth = int(argv[2]) # [cm]
map_var = 'paw_80' # variable to plot (this will become a command-line variable in the future)

## Plot options
(w, h) = (1280, 720) # width, height [px]
dpi = 150 # [px/in]

## Soil moisture variable definitions
map_vars = {
    'vwc': {
        'name': 'Volumetric Water Content',
        'units': 'cm$^3$ cm$^{-3}$',
        'ticks': [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    },
    'paw_80': {
        'name': 'Plant Available Water',
        'units': 'mm',
        'ticks': [0, 50, 100, 150, 200, 250, 300, 350, 400]
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

### Data

# set the data directories
input_static_data_dir = '../static_data/'
input_paw_dir = '../output/paw/'
input_shapefile_dir = '../gis_setup/state_county_shapefiles/'
map_cache_dir = 'map_cache/'
output_dir = '../output/'

# get the date string
from datetime import datetime
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

## load static data sources
import cPickle as pickle

# grid
df = pickle.load(open(input_static_data_dir + 'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))

# map object and map parameters dict
m = pickle.load(open(map_cache_dir + 'oklahoma_basemap.pickle'))
p = pickle.load(open(map_cache_dir + 'map_params.pickle'))

# colormap
cmap = pickle.load(open(map_cache_dir + 'cmap.pickle'))

## load dynamic data sources
from pandas import read_csv

# soil moisture data
sm_fname = '%scm_%s.csv' % (map_var, date_str)
sm_df = read_csv(input_paw_dir + sm_fname, index_col=0)

### Computation

## Combine data, drop NaNs, and sort by index ('id')
df = df.join(sm_df).dropna().sort_index()

## Open (or create, if necessary) the PatchCollection
from os.path import exists
from hashlib import md5

# hash the sorted grid ids to generate a filename for each unique set of ids
id_hash = md5(df.index.values).hexdigest()
pc_fname = map_cache_dir + '800m_pixels_%s.pickle' % (id_hash)

if exists(pc_fname): # if that filename exists, load the PatchCollection
    pc = pickle.load(open(pc_fname)) # Caution: about 2.5 GB in RAM!

else: # otherwise build a new PatchCollection

    # This takes a long time (about 1.25 minutes)
    # and takes a lot of RAM (about 4.5 GB)
    # which is why we prefer to load PatchCollection from disk.

    # put the grid in map coordinates
    df['x'], df['y'] = (df['x'] + p['offset']['x'], df['y'] + p['offset']['y'])

    # create the individual Patches
    from matplotlib.patches import Rectangle

    # Rectangle() has its lower left corner at (x, y),
    # but each (x, y) grid point in the DataFrame is defined at its center,
    # so generate xy pairs by shifting down and left by (dx/2, dy/2)
    xy_pairs = zip(df['x'].values - p['dx']/2., df['y'].values - p['dy']/2.)
    patches = [Rectangle(xy, width=p['dx'], height=p['dy']) for xy in xy_pairs]

    # build PatchCollection from the Patches
    from matplotlib.collections import PatchCollection
    pc = PatchCollection(patches, edgecolor='None')
    patches = None # patches is huge (~2 GB!), so clear it from RAM ASAP
    pickle.dump(pc, open(pc_fname, 'w')) # cache PatchCollection so it can be reused

# give soil moisture data to the PatchCollection
pc.set_array(df[map_var].values)

# color the PatchCollection based on soil moisture
pc.set_cmap(cmap) # set color map
if 'ticks' in map_vars[map_var].keys(): # set color map limits based on min/max tick values
    pc.set_clim([min(map_vars[map_var]['ticks']),
                max(map_vars[map_var]['ticks'])])

## Plot the map
from matplotlib import use
use('agg') # prevent matplotlib from using interactive mode

import matplotlib.pyplot as plt

# create the figure
size = (w/float(dpi), h/float(dpi)) # convert to from pixels to inches
fig = plt.figure(1, size, dpi=dpi)

# create axes and add the PatchCollection
ax = fig.add_axes([0, 0, 1, 1]) # fill the whole figure
ax.add_collection(pc)

# plot Oklahoma counties and state outlines from shapefiles
county_name = 'tl_2014_oklahoma_county'
state_name = 'tl_2014_oklahoma_state'

m.readshapefile(input_shapefile_dir + '%s/%s' % (county_name, county_name),
                county_name, linewidth=0.5)
m.readshapefile(input_shapefile_dir + '%s/%s' % (state_name, state_name),
                state_name, linewidth=2)

# fill the rest of the map background
m.drawmapboundary(linewidth=0) # no border

# add the colorbar
cbax = fig.add_axes([0.16, 0.32, 0.1, 0.42]) # place it underneath the OK Panhandle
cbax.set_axis_off() # turn off axis ticks
cb = fig.colorbar(pc, ax = cbax, fraction = 1, aspect = 8,
                  label = map_vars[map_var]['units'], spacing = 'proportional')
if 'ticks' in map_vars[map_var].keys(): # add colorbar ticks
    cb.set_ticks(map_vars[map_var]['ticks'])

# add text info
(llx, lly) = m(p['left'], p['bottom'])  # get the lower left and lower right
(lrx, lry) = m(p['right'], p['bottom']) # corners in plot coordinates
ax.text(llx, lly, '%d-cm %s' % (depth, map_vars[map_var]['name']),
        size = 20, family = 'sans-serif', ha = 'left', va = 'bottom')
ax.text(lrx, lry, 'valid %s CST' % (date.strftime('%-I:%M %p %B %-d, %Y')),
        size = 11, family = 'sans-serif', ha = 'right', va = 'bottom')

# save the map
fig.savefig(output_dir +
            'paw_maps/%scm_%s.png' % (map_var, date_in),
            dpi=dpi)
