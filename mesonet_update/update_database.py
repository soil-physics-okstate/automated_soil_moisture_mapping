# Load latest mesonet station data

print 'Updating Mesonet geoinfo...'

from pandas import read_csv

url = 'http://www.mesonet.org/index.php/api/siteinfo/from_all_active_with_geo_fields/format/csv/'
meso_df = read_csv(url).set_index('stid')

# Connect to database

import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

# --- Update mesonet stations

columns = 'stid,stnm,nlat,elon,elev,datc,datd'
query = 'INSERT INTO mesonet_geoinfo (%s) ' % (columns) +\
        'VALUES (%s, %s, %s, %s, %s, %s, %s);'

for row in meso_df[columns.split(',')[1:]].itertuples():
    try:
        cur.execute(query, row)
    except psycopg2.IntegrityError:
        conn.rollback()
    else:
        conn.commit()

# --- Update mesonet geometry

query = 'UPDATE mesonet_geoinfo SET geom = ST_SetSRID(ST_MakePoint(elon, nlat), 4326) '+\
        'WHERE geom IS NULL;'
cur.execute(query)
conn.commit()

# --- Update mesonet grid points

query = 'UPDATE mesonet_geoinfo SET '+\
        'x = ST_X(ST_Transform(geom, 990001)),'+\
        'y = ST_Y(ST_Transform(geom, 990001)) '+\
        'WHERE (x IS NULL) OR (y IS NULL);'
cur.execute(query)
conn.commit()

# --- Update mesonet mukeys

query = 'UPDATE mesonet_geoinfo SET mukey = CAST(s.mukey AS int) '+\
        'FROM ssurgo_mupolygons_ok AS s '+\
        'WHERE ST_Intersects(geom, s.wkb_geometry);'
cur.execute(query)
conn.commit()

# --- Update mesonet StageIV x/y points

query = 'UPDATE mesonet_geoinfo SET s4x = s4.x, s4y = s4.y '+\
        'FROM stage4_polys AS s4 WHERE ((s4x IS NULL) OR (s4y IS NULL)) '+\
        'AND ST_Intersects(geom, s4.geom_pixel);'
cur.execute(query)
conn.commit()

# ---

conn.close()

print '  Done.'
