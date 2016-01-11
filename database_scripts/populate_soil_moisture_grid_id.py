data_dir = '../data/'

import pickle

grid_df = pickle.load(open(data_dir + 'grid/xy2id_lat_lon.pickle'))

import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

query = 'INSERT INTO soil_moisture_grid_id ' + \
        '(id, x, y, longitude, latitude) VALUES ' + \
        '(%s, %s, %s, %s, %s);'

for row in grid_df.reset_index().iterrows():

    grid_id = int(row[1]['id'])
    x = int(row[1]['x'])
    y = int(row[1]['y'])
    lon = row[1]['longitude']
    lat = row[1]['latitude']

    cur.execute(query, (grid_id, x, y, lon, lat))

conn.commit()
cur.close()
conn.close()
