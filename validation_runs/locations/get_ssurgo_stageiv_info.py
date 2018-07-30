dbname = 'soilmapnik'

import psycopg2

conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

import cPickle as pickle

# Get base grid information

df = pickle.load(open('all_sites.pickle'))

import numpy as np

df['mukey'] = np.nan
df['s4x'] = np.nan
df['s4y'] = np.nan

for site, row in df.iterrows():

    # Get SSURGO mukey

    point = 'ST_SetSRID(ST_MakePoint(%s, %s), 4326)'

    query =  'SELECT mukey FROM mupolygon '
    query += 'WHERE ST_Intersects(ST_Transform(%s, 990002), wkb_geometry);'
    query = query % (point)

    cur.execute(query, (row['lon'], row['lat']))

    results = cur.fetchall()
    if not results: continue
    if len(results) > 1 or len(results[0]) > 1:
        print 'Multiple results found for id %s %d:' % site
        print results
        print

    df.loc[site, 'mukey'] = int(results[0][0])

    # Get StageIV coordinates

    query =  'SELECT s4.x, s4.y FROM stageiv_grid AS s4 '
    query += 'WHERE ST_Intersects(%s, s4.geom_pixel);'
    query = query % (point)

    cur.execute(query, (row['lon'], row['lat']))

    results = cur.fetchall()
    if not results: continue
    if len(results) > 1:
        print 'Multiple results found for id %s %d:' % site
        print results
        print

    df.loc[site, ['s4x', 's4y']] = results[0]


df.to_pickle('all_sites_ssurgo_stageiv.pickle')
