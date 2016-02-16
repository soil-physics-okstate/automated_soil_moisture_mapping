# Oklahoma bounds
# ('o' = origin at corner of Kingfisher/Logan/Canadian/Oklahoma counties)
lats = {'n':  37.1, 's':  33.6,  'c':  35.5, 'o':  35.726}
lons = {'e': -94.4, 'w': -103.0, 'c': -97.5, 'o': -97.674}

buf = 0.05 # plot buffer size [deg]

(dx, dy) = (800, 800) # pixel resolution [m]

res = 'c' # map shapes resolution

# projection parameters
proj = 'cea' # cylindrical equal area
lat_ts = lats['c'] # true scale at geographic center
lon_0 = lons['o']  # x=0 at counties corner
lat_0 = lats['o']  # y=0 at counties corner

# load libraries
from mpl_toolkits.basemap import Basemap

# create the map
m = Basemap(projection = proj, lat_ts = lat_ts, resolution = res,
            urcrnrlon = lons['e'] + buf, urcrnrlat = lats['n'] + buf,
            llcrnrlon = lons['w'] - buf, llcrnrlat = lats['s'] - buf*4,
            fix_aspect = False)

# calculate the offset
offset = m(lon_0, lat_0)

map_params = {
    'lats': lats,
    'lons': lons,
    'buffer': buf,
    'dx': dx,
    'dy': dy,
    'resolution': res,
    'projection': proj,
    'offset': {'x': offset[0], 'y': offset[1]},
    'top': lats['n'] + buf,
    'bottom': lats['s'] - buf*4,
    'left': lons['w'] - buf,
    'right': lons['e'] + buf
}

import pickle

pickle.dump(map_params, open('map_params.pickle', 'w'))
