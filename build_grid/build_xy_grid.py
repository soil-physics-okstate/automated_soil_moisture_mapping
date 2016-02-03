## Oklahoma coordinates
#   lats: south, north, center, origin
#   lons: east, west, center, origin
#   origin at corner of Kingfisher, Logan, Canadian, and Oklahoma counties

ok = {
    'lat': {'s': 33.6,  'n': 37.1,   'c': 35.5,  'o': 35.726},
    'lon': {'e': -94.4, 'w': -103.0, 'c': -97.5, 'o': -97.674}
}

# Compute geographic center -- can be useful for lines of scale

ok['lat']['abs_c'] = (ok['lat']['s'] + ok['lat']['n'])/2.
ok['lon']['abs_c'] = (ok['lon']['w'] + ok['lon']['e'])/2.


## Set grid spacing

ds = 800 # grid size [m], approx 1/2 mi


## Define the Cylindrical Equal Area grid

from pyproj import Proj

proj4str = '+proj=%s +a=%d +b=%d +lon_0=%.3f +lat_ts=%.3f +x_0=%.3f +y_0=%.3f +units=%s +no_defs'

proj = 'cea' # Cylindrical Equal Area projection
radius = 6378137 # radius of Earth [m]

lat_ts = ok['lat']['abs_c'] # latitude of true scale
lon_0 = ok['lon']['o'] # longitude of origin

x_0 = 0 # false easting
y_0 = 0 # false northing
units = 'm' # units

# Build our initial projected coordinate system
cea = Proj(proj4str % (proj, radius, radius, lon_0, lat_ts, x_0, y_0, units))

# Adjust origin of projected coordinate system
# by computing a new false easting and northing
[x_0, y_0] = [-x for x in cea(ok['lon']['o'], ok['lat']['o'])]
cea = Proj(proj4str % (proj, radius, radius, lon_0, lat_ts, x_0, y_0, units))


##  Get projected coordinates of Oklahoma edges
sw = cea(ok['lon']['w'], ok['lat']['s'])
nw = cea(ok['lon']['w'], ok['lat']['n'])
ne = cea(ok['lon']['e'], ok['lat']['n'])
se = cea(ok['lon']['e'], ok['lat']['s'])

sc = cea(ok['lon']['o'], ok['lat']['s'])
nc = cea(ok['lon']['o'], ok['lat']['n'])
ec = cea(ok['lon']['e'], ok['lat']['abs_c'])
wc = cea(ok['lon']['w'], ok['lat']['abs_c'])


## Build grid in projected coordinates

import numpy as np

# bounds (inclusive)
xmin = np.around(min([nw[0], sw[0], wc[0]]), -2)
xmax = np.around(max([ne[0], se[0], ec[0]]), -2)
ymin = np.around(min([sw[1], se[1], sc[1]]), -2)
ymax = np.around(max([nw[1], ne[1], nc[1]]), -2)

# x coordinates from xmin to xmax, including 0+ds/2
xleft  = -np.arange(ds/2, abs(xmin)+ds, ds).astype(int)[::-1]
xright =  np.arange(ds/2, xmax+ds, ds).astype(int)
xs = np.concatenate((xleft, xright))

# y coordinates from ymin to ymax, including 0+ds/2
ydown = -np.arange(ds/2, abs(ymin)+ds, ds).astype(int)[::-1]
yup =    np.arange(ds/2, ymax+ds, ds).astype(int)
ys = np.concatenate((ydown, yup))


## Store grid in database

import psycopg2

conn = psycopg2.connect('dbname=soilmapnik')
cur = conn.cursor()

table = 'soil_moisture_grid_id'

query =  'INSERT INTO %s ' % (table)
query += '(id, x, y) VALUES (%s, %s, %s);'

i = 0 # unique id number
for x in xs:
    for y in ys:
        cur.execute(query, (i, x, y))
        i += 1

conn.commit()
cur.close()
conn.close()
