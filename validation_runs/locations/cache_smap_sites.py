cols = ['site', 'station', 'lat', 'lon']
data = dict(zip(cols, [[] for c in cols]))

for line in open('smap_core_validation_sites.txt'):
    col = line.rstrip().split(',')
    if col[0] == 'Site': continue
    try:
        int(col[0])
    except ValueError:
        site = col[0]
        continue

    data['site'].append(site)
    data['station'].append(int(col[0]))
    data['lat'].append(float(col[1]))
    data['lon'].append(float(col[2]))

from pandas import DataFrame

df = DataFrame(data=data).set_index(['site', 'station']).sort_index()

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

df.to_pickle('smap_sites.pickle')
