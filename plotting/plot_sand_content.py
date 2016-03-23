from matplotlib import use
use('agg')

from sys import argv

d = int(argv[1])

import numpy as np

depths = [5, 25, 60]
cmap = 'YlOrBr'
(w, h) = (1280, 720) # width, height
dpi = 150. # screens are usually 96 dpi
ticks = np.arange(0, 100.1, 20)

import cPickle as pickle

input_data_dir = '../../../static_data/'
map_cache_dir = '../../../plotting/map_cache/'
input_shapefile_dir = '../../../gis_setup/state_county_shapefiles/'

grid_df = pickle.load(open(input_data_dir +
                           'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
texture_df = pickle.load(open(input_data_dir +
                              'soil_properties/ssurgo/ssurgo_texture_by_mukey.pickle'))

m = pickle.load(open(map_cache_dir + 'oklahoma_basemap.pickle'))
p = pickle.load(open(map_cache_dir + 'map_params.pickle'))

df = grid_df.join(texture_df, on='mukey').sort_index()
df['x'], df['y'] = (df['x'] + p['offset']['x'], df['y'] + p['offset']['y'])

import matplotlib.pyplot as plt

cmap = plt.get_cmap(cmap)
cmap.set_bad('#004444', alpha=1.)

try:
    pc = pickle.load(open('patchcollection.pickle'))
except Exception:
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Rectangle

    xy_pairs = zip(df['x'].values - p['dx']/2., df['y'].values - p['dy']/2.)
    patches = [Rectangle(xy, width=p['dx'], height=p['dy']) for xy in xy_pairs]
    pc = PatchCollection(patches, edgecolor='None')
    patches = None
    pickle.dump(pc, open('patchcollection.pickle', 'w'))

values = np.ma.masked_invalid(df[('sand', d)].astype(np.float32).values)
pc.set_array(values)
pc.set_cmap(cmap)
pc.set_clim([min(ticks), max(ticks)])

size = (w/dpi, h/dpi)    
fig = plt.figure(1, size, dpi=dpi)

ax = fig.add_axes([0, 0, 1, 1])
ax.add_collection(pc)

county_name = 'tl_2014_oklahoma_county'
state_name = 'tl_2014_oklahoma_state'

m.readshapefile(input_shapefile_dir + '%s/%s' % (county_name, county_name),
                county_name, linewidth=0.5)
m.readshapefile(input_shapefile_dir + '%s/%s' % (state_name, state_name),
                state_name, linewidth=2)

m.drawmapboundary(linewidth=0)

cbax = fig.add_axes([0.16, 0.32, 0.1, 0.42])
cbax.set_axis_off()
cb = fig.colorbar(pc, ax = cbax, fraction = 1, aspect = 8,
                  label = '%', spacing = 'proportional')
cb.set_ticks(ticks)

(llx, lly) = m(p['left'], p['bottom'])
(lrx, lry) = m(p['right'], p['bottom'])
ax.text(llx, lly, '%d-cm %s' % (d, 'Sand Content'),
        size = 20, family = 'sans-serif', ha = 'left', va = 'bottom')
ax.text(lrx, lry, 'estimated from USDA-NRCS SSURGO',
        size = 11, family = 'sans-serif', ha = 'right', va = 'bottom')

fig.savefig('sand_content_%dcm_map.png' % (d), dpi=dpi)
