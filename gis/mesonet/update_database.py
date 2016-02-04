dbname = 'soilmapnik'

# Load latest mesonet station data

print 'Updating Mesonet geoinfo...'

from pandas import read_csv

url = 'http://www.mesonet.org/index.php/api/siteinfo/from_all_active_with_geo_fields/format/csv/'
columns = 'stnm,stid,name,city,rang,cdir,cnty,nlat,elon,elev,cdiv,clas,datc,datd'
df = read_csv(url, usecols=columns.split(',')).set_index('stnm')

# Connect to database

import psycopg2

conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

# Build query 

ncol = len(columns.split(','))
query =  'INSERT INTO mesonet_geoinfo (%s) ' % (columns)
query += 'VALUES (%s);' % (','.join(['%s' for i in xrange(ncol)]))
print query

# Update mesonet stations

for row in df.itertuples():
    #try:
    cur.execute(query, row)
    #except psycopg2.IntegrityError:
    #    conn.rollback()
    #else:
    #    conn.commit()

# Update mesonet geometry

query =  'UPDATE mesonet_geoinfo SET geom = ST_SetSRID(ST_MakePoint(elon, nlat), 4326) '
query += 'WHERE geom IS NULL;'
cur.execute(query)
conn.commit()

cur.close()
conn.close()

print '  Done.'
