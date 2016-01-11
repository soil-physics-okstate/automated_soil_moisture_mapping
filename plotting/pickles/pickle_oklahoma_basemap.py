## Map 

# Oklahoma bounds 
# ('o' = origin at corner of Kingfisher/Logan/Canadian/Oklahoma counties)
lats = {'n':  37.1, 's':  33.6,  'c':  35.5, 'o':  35.726}
lons = {'e': -94.4, 'w': -103.0, 'c': -97.5, 'o': -97.674}

buf = 0.05 # plot buffer size [deg]

dx = 800 + 0 # pixel resolution [m] (include a small buffer)

res = 'c' # map shapes resolution

# projection parameters
proj = 'cea' # cylindrical equal area
lat_ts = lats['c'] # true scale at geographic center
lon_0 = lons['o']  # x=0 at counties corner
lat_0 = lats['o']  # y=0 at counties corner

## Load libraries
from mpl_toolkits.basemap import Basemap

## Create the map
m = Basemap(projection = proj, lat_ts = lat_ts, resolution = res,
            urcrnrlon = lons['e'] + buf, urcrnrlat = lats['n'] + buf,
            llcrnrlon = lons['w'] - buf, llcrnrlat = lats['s'] - buf*4,
            fix_aspect = False)

## Save the map
import pickle
pickle.dump(m, open('oklahoma_basemap.pickle', 'w'))
