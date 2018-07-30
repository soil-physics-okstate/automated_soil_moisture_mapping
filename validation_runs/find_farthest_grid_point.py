import cPickle as pickle

grid_df = pickle.load(open('../static_data/grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
meso_df = pickle.load(open('../static_data/mesonet/mesonet_geoinfo_ssurgo_stageiv.pickle'))
meso_i = pickle.load(open('mesosoil_active.pickle'))

grid_df = grid_df.dropna()
meso_df = meso_df.loc[meso_i]

xmin = meso_df.loc['WOOD']['x']
xmax = meso_df.loc['TAHL']['x']
ymin = meso_df.loc['PAUL']['y']
ymax = meso_df.loc['BURB']['y']

#meso_df = meso_df[meso_df['x'] >= xmin]
#meso_df = meso_df[meso_df['x'] <= xmax]
#meso_df = meso_df[meso_df['y'] >= ymin]
#meso_df = meso_df[meso_df['y'] <= ymax]

grid_df = grid_df[grid_df['x'] > xmin]
grid_df = grid_df[grid_df['x'] < xmax]
grid_df = grid_df[grid_df['y'] > ymin]
grid_df = grid_df[grid_df['y'] < ymax]

import numpy as np
#from collections import deque
from collections import defaultdict

#max_dists = deque(5*[0], maxlen=5)
#max_ids = deque([], maxlen=5)
#max_sites = deque([], maxlen=5)

site_dist = defaultdict(int)
site_gid = {}

i = 0

for gid,row in grid_df.iterrows():
    if (i % 1000) == 0:
        print '%6d / %d' % (i, len(grid_df))
    i += 1

    #if row['x'] < xmin: continue
    #if row['x'] > xmax: continue
    #if row['y'] < ymin: continue
    #if row['y'] > ymax: continue

    dists = np.sqrt( (row['x'] - meso_df['x'])**2 + (row['y'] - meso_df['y'])**2 )

    dist = dists.min()
    site = dists.idxmin()

    if dist > site_dist[site]:

        site_dist[site] = dist
        site_gid[site] = gid

        #max_dists.append(dist)
        #max_ids.append(gid)
        #max_sites.append(dists.idxmin())

#print max_ids, max_dists, max_sites

site_order = sorted(site_dist, key=site_dist.get, reverse=True)

sites = []
for site in site_order:
    dist = site_dist[site]
    gid = site_gid[site]

    x, y = grid_df.loc[gid][['x', 'y']].values
    sites.append((x, y, site, gid, dist))

pickle.dump(sites, open('farthest_points.pickle', 'w'))
