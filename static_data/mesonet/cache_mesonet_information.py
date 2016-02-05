dbname = 'soilmapnik'

import psycopg2

conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

import pickle
from os.path import isfile


# Get base grid information

from pandas import DataFrame

fname = 'mesonet_geoinfo.pickle'
if not isfile(fname):

    columns = 'stid,elev'
    query = 'SELECT %s FROM mesonet_geoinfo;' % (columns)

    cur.execute(query)

    df = DataFrame(cur.fetchall(), columns=columns.split(',')).set_index('stid')
    df.to_pickle(fname)

else: 
    
    df = pickle.load(open(fname))


# Get SSURGO mukey

import numpy as np

fname = 'mesonet_geoinfo_ssurgo.pickle'
if not isfile(fname):

    df['mukey'] = np.nan

    for stid in df.index.values:
        query =  'SELECT mukey FROM mesonet_geoinfo, mupolygon '
        query += 'WHERE (stid = %s AND ST_Intersects(ST_Transform(geom, 990002), wkb_geometry));'

        cur.execute(query, (stid,))

        results = cur.fetchall()
        if not results: continue
        if len(results) > 1 or len(results[0]) > 1:
            print 'Multiple results found for id %d:' % (stid)
            print results
            print

        df.loc[stid, 'mukey'] = int(results[0][0])

    df.to_pickle(fname)

else:

    df = pickle.load(open(fname))



# Get StageIV coordinates

fname = 'mesonet_geoinfo_ssurgo_stageiv.pickle'
if not isfile(fname):

    df['s4x'] = np.nan
    df['s4y'] = np.nan

    for stid in df.index.values:
        query =  'SELECT x, y FROM mesonet_geoinfo, stageiv_grid '
        query += 'WHERE (stid = %s AND ST_Intersects(geom, geom_pixel));'

        cur.execute(query, (stid,))

        results = cur.fetchall()
        if not results: continue
        if len(results) > 1:
            print 'Multiple results found for id %d:' % (stid)
            print results
            print

        df.loc[stid, ['s4x', 's4y']] = results[0]

    df.to_pickle(fname)

else:

    df = pickle.load(open(fname))
