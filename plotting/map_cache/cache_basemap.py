import pickle

p = pickle.load(open('map_params.pickle'))

## Load libraries
from mpl_toolkits.basemap import Basemap

## Create the map
m = Basemap(projection = p['projection'],
            lat_ts = p['lats']['c'],
            resolution = p['resolution'],
            urcrnrlon = p['right'], urcrnrlat = p['top'],
            llcrnrlon = p['left'], llcrnrlat = p['bottom'],
            fix_aspect = False)

pickle.dump(m, open('oklahoma_basemap.pickle', 'w'))
