import numpy as np
import pickle
from datetime import datetime

start = 0

df = pickle.load(open('grid.pickle')).dropna()
df['elev'] = np.nan

pts = zip(df.reset_index()['x'].values[start:], df.reset_index()['y'].values[start:])

import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

query = (
    'SELECT ('
    'ST_DumpValues('
    'ST_Union(ST_Clip(rast, ST_Transform(geom_pixel, 4269)))'
    #'ST_Clip(rast, ST_Transform(geom_pixel, 4269))'
    ')'
    ').* '
    'FROM dem_ok, soil_moisture_grid_id '
    'WHERE '
    '(x = %s AND y = %s);'
    )

query2 = (
    'SELECT ('
    'ST_DumpValues('
    #'ST_Union(ST_Clip(rast, ST_Transform(geom_pixel, 4269)))'
    'ST_Clip(rast, ST_Transform(geom_pixel, 4269))'
    ')'
    ').* '
    'FROM dem_ok, soil_moisture_grid_id '
    'WHERE '
    '(x = %s AND y = %s);'
    )

from datetime import datetime
t0 = datetime.now()

for i,(x,y) in enumerate(pts):

    if (i > 0) and (i % 200) == 0:
        dt = (datetime.now()-t0)/200
        print('%6d/%d (%6.3f %%) Est. time remaining: %s' %
              (i, len(pts), 100*(float(i)/len(pts)), dt*(len(pts)-i)))
        t0 = datetime.now()

    try:
        cur.execute(query, (x,y))
        elevs = cur.fetchone()[1]

    except psycopg2.InternalError: # sometimes there's a weird error
        conn.reset() # in which case we need to reset the connection
        cur = conn.cursor() # define another cursor
        cur.execute(query2, (x,y)) # execute the alternate query
        rows = cur.fetchall() # which returns extra rows
        elevs = np.array([]) # that we have to combine together
        for row in rows:
            elevs = np.concatenate((elevs, np.array(row[1]).flatten()))
        print 'had to use alt query, i = %d' % (i)
    except TypeError:
        continue
            
    df.loc[x,y]['elev'] = np.nanmean(np.array(elevs, dtype=np.float))

df['elev'].to_pickle('elevation.pickle')

