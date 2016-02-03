import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

depths = [5, 25, 60]
columns = 'mukey,depth,sand'
query = 'SELECT %s FROM soil_properties_by_mukey;' % (columns)

cur.execute(query)

from pandas import DataFrame

df = DataFrame(cur.fetchall(), columns=columns.split(','))
df = df.set_index(['mukey', 'depth']).unstack()['sand']
df.columns = depths

df.to_pickle('sand_content.pickle')
