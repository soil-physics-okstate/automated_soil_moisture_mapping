### Decouple matplotlib from X
from matplotlib import use
use('agg')


### Parameters

import numpy as np
cmap = 'BrBG'
ticks = np.arange(-0.3, 0.31, 0.1)

## Command-line

from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
depth = int(argv[2]) # [cm]

### Data

# get the data directories
input_static_data_dir = '../static_data/'
input_kr_data_dir = '../output/kriging_residual/'
input_shapefile_dir = '../gis_setup/state_county_shapefiles/'
map_cache_dir = 'map_cache/'
output_dir = '../output/diagnostics/kriging_residual/'

# get the date string
date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd

## load static data sources
import cPickle as pickle

df = pickle.load(open(input_static_data_dir + 'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
m = pickle.load(open(map_cache_dir + 'oklahoma_basemap.pickle'))
p = pickle.load(open(map_cache_dir + 'map_params.pickle'))

## load dynamic data sources
from pandas import read_csv

# get the kriging residual data
kr_fname = 'kriged_%dcm_%s.csv' % (depth, date_str)
kr_df = read_csv(input_kr_data_dir + kr_fname, index_col=[0, 1])

## Plots

(w, h) = (1280, 720) # width, height
dpi = 150. # screens are usually 96 dpi

### Computation

## Combine data frames, drop NaNs, and sort by id
df = df.join(kr_df, on=['x', 'y']).sort_index()

## Create patch collection if necessary
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from os.path import exists
from hashlib import md5

# hash the grid ids to generate a unique filename for PatchCollection
id_hash = md5(df.index.values).hexdigest()
pc_fname = map_cache_dir + '800m_pixels_%s.pickle' % (id_hash)

if exists(pc_fname): # if that filename exists, load the file
    pc = pickle.load(open(pc_fname)) # patches object

else: # otherwise build a new patch collection

    # put the grid in map coordinates
    df['x'], df['y'] = (df['x'] + p['offset']['x'], df['y'] + p['offset']['y'])

    # create the rectangle patches
    from matplotlib.patches import Rectangle
    xy_pairs = zip(df['x'].values - p['dx']/2., df['y'].values - p['dy']/2.)
    patches = [Rectangle(xy, width=p['dx'], height=p['dy']) for xy in xy_pairs]

    # build PatchCollection from remaining patches
    pc = PatchCollection(patches, edgecolor='None')
    patches = None # clear memory
    pickle.dump(pc, open(pc_fname, 'w')) # save PatchCollection

values = np.ma.masked_invalid(df['Z'].astype(np.float32).values)

# give soil moisture data to the PatchCollection
pc.set_array(values)

# Color patch collection based on soil moisture
cmap = plt.get_cmap(cmap)
cmap.set_bad('#BB00BB', alpha=1.)
pc.set_cmap(cmap) # set color map

# set color map limits
pc.set_clim([min(ticks), max(ticks)])

## Plot the data on the map

# Create the figure
size = (w/dpi, h/dpi)
fig = plt.figure(1, size, dpi=dpi)

# Get the current axes and add the soil moisture collection
ax = fig.add_axes([0, 0, 1, 1])
ax.add_collection(pc)

# Use Oklahoma counties and state shapefile for plot background
county_name = 'tl_2014_oklahoma_county'
state_name = 'tl_2014_oklahoma_state'

m.readshapefile(input_shapefile_dir + '%s/%s' % (county_name, county_name),
                county_name, linewidth=0.5)
m.readshapefile(input_shapefile_dir + '%s/%s' % (state_name, state_name),
                state_name, linewidth=2)

# Initialize the map
m.drawmapboundary(linewidth=0)

# Add the colorbar
cbax = fig.add_axes([0.16, 0.32, 0.1, 0.42])
cbax.set_axis_off()
cb = fig.colorbar(pc, ax = cbax, fraction = 1, aspect = 8,
                  label = 'cm$^3$ cm$^{-3}$', spacing = 'proportional')
cb.set_ticks(ticks)

# Add text info
(llx, lly) = m(p['left'], p['bottom'])
(lrx, lry) = m(p['right'], p['bottom'])
ax.text(llx, lly, '%d-cm %s' % (depth, 'Kriged Soil Moisture Residuals'),
        size = 20, family = 'sans-serif', ha = 'left', va = 'bottom')
ax.text(lrx, lry, 'valid %s CST' % (date.strftime('%-I:%M %p %B %-d, %Y')),
        size = 11, family = 'sans-serif', ha = 'right', va = 'bottom')

# Save the map
fig.savefig(output_dir + 'kr_%02dcm_%s.png' % (depth, date_in), dpi=dpi)
