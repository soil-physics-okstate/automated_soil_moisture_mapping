dbname = 'soilmapnik'

import psycopg2

conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

import pickle
from os.path import isfile


# Get base grid information

from pandas import DataFrame

fname = 'soil_moisture_grid.pickle'
if not isfile(fname):

    query =  'SELECT id, x, y FROM soil_moisture_grid, tl_2014_oklahoma_state '
    query += 'WHERE ST_Intersects(geom_pixel, ST_Transform(wkb_geometry, 4326));'

    cur.execute(query)

    df = DataFrame(cur.fetchall(), columns=['id', 'x', 'y']).set_index('id')
    df.to_pickle(fname)

else: 
    
    df = pickle.load(open(fname))

# Get SSURGO mukey

import numpy as np

fname = 'soil_moisture_grid_ssurgo.pickle'
if not isfile(fname):

    df['mukey'] = np.nan

    for gid in df.index.values:
        query =  'SELECT mukey FROM soil_moisture_grid, mupolygon '
        query += 'WHERE (id = %s AND ST_Intersects(ST_Transform(geom_point, 990002), wkb_geometry));'

        cur.execute(query, (gid,))

        results = cur.fetchall()
        if not results: continue
        if len(results) > 1 or len(results[0]) > 1:
            print 'Multiple results found for id %d:' % (gid)
            print results
            print

        df.loc[gid, 'mukey'] = int(results[0][0])

    df.to_pickle(fname)

else:

    df = pickle.load(open(fname))


# Get StageIV coordinates

fname = 'soil_moisture_grid_ssurgo_stageiv.pickle'
if not isfile(fname):

    df['s4x'] = np.nan
    df['s4y'] = np.nan

    for gid in df.index.values:
        query =  'SELECT s4.x, s4.y FROM soil_moisture_grid, stageiv_grid AS s4 '
        query += 'WHERE (id = %s AND ST_Intersects(geom_point, s4.geom_pixel));'

        cur.execute(query, (gid,))

        results = cur.fetchall()
        if not results: continue
        if len(results) > 1:
            print 'Multiple results found for id %d:' % (gid)
            print results
            print

        df.loc[gid, ['s4x', 's4y']] = results[0]

    df.to_pickle(fname)

else:

    df = pickle.load(open(fname))

# save a matfile for Matlab
from scipy.io import savemat

df = df.dropna()
output_dict = {'x': df['x'].values, 'y': df['y'].values}
savemat('soil_moisture_grid.mat', output_dict, oned_as='column')
