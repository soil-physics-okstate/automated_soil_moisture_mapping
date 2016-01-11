import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

query = 'SELECT x,y,latitude,longitude FROM ok_soil_moisture_grid_cea;'
cur.execute(query)

from pandas import DataFrame

grid_df = DataFrame(cur.fetchall(), columns=['x', 'y', 'latitude', 'longitude'])

grid_df.index.name = 'id'

grid_df = grid_df.reset_index().set_index(['x', 'y'])

grid_df.to_pickle('xy2id_lat_lon.pickle')
