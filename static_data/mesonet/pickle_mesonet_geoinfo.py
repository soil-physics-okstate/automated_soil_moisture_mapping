import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

columns = 'stid,x,y,mukey,s4x,s4y'

query = 'SELECT %s FROM mesonet_geoinfo;' % (columns)

cur.execute(query)

from pandas import DataFrame

df = DataFrame(cur.fetchall(), columns=columns.split(',')).set_index('stid')

df.to_pickle('mesonet_geoinfo.pickle')
