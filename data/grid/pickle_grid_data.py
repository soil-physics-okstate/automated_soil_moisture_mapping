import psycopg2

conn = psycopg2.connect('')
cur = conn.cursor()

columns = 'x,y,mukey,stageiv_x,stageiv_y'
query = 'SELECT %s FROM ok_soil_moisture_grid_cea WHERE inoklahoma = true ORDER BY x, y;' % (columns)

cur.execute(query)

from pandas import DataFrame

df = DataFrame(cur.fetchall(), columns=columns.split(',')).set_index(['x', 'y'])

df.to_pickle('grid.pickle')
df.reset_index().to_csv('grid.csv', columns=['x', 'y'], index=False)
