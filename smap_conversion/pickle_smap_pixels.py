import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

query = 'SELECT ease_column_index, ease_row_index FROM smap_grid_ok WHERE n_sm_points > 1000;'

cur.execute(query)

smap_pixels = cur.fetchall()

import pickle

pickle.dump(smap_pixels, open('smap_pixels.pickle', 'w'))

query = 'SELECT id FROM soil_moisture_grid_id AS sm, smap_grid_ok AS smap ' +\
        'WHERE (' +\
        'ease_column_index = %s AND ' +\
        'ease_row_index = %s AND ' +\
        'ST_Intersects(smap.geom_pixel, sm.geom_point)' +\
        ');'

pixel2id = {}
for smap_pixel in smap_pixels:
    cur.execute(query, smap_pixel)
    pixel2id[smap_pixel] = zip(*cur.fetchall())[0]
    
#pickle.dump(pixel2id, open('smap_pixel2sm_id.pickle', 'w'))

from pandas import DataFrame, concat

df = DataFrame()
for pixel in pixel2id:
    temp_df = DataFrame(zip(pixel2id[pixel]), columns=['id'])
    temp_df['ease_column_index'] = pixel[0]
    temp_df['ease_row_index'] = pixel[1]
    df = concat((df, temp_df))

df.to_pickle('pixel2id.pickle')
