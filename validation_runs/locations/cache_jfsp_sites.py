from pandas import read_csv

df = read_csv('jfsp_sites.txt', names=['station', 'lat', 'lon'], skiprows=1)
df['site'] = 'JFSP'

with open('soil_moisture_grid_proj4str.txt') as f:
    proj4str = f.read()
proj4str = proj4str.rstrip()

from pyproj import Proj

proj = Proj(proj4str)

lons = df['lon'].values
lats = df['lat'].values

(xs, ys) = proj(lons, lats)

df['x'] = xs
df['y'] = ys

df = df.set_index(['site', 'station'])

df.to_pickle('jfsp_sites.pickle')
