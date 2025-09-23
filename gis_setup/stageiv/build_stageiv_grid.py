import stageiv_reprojection as s4
import psycopg2

dbname = 'soilmapnik'

conn = psycopg2.connect('dbname=%s' % (dbname), user='postgres', password='Ali292Ali292')
cur = conn.cursor()

query = 'INSERT INTO stageiv_grid (x, y, geom_pixel) VALUES (%s, %s, ST_SetSRID(ST_MakePolygon(ST_GeomFromText(%s)), 4326));'

nx = 335 # number of columns in grid
ny = 159 # number of rows in grid

for x in range(nx):

    for y in range(ny):

        # get the polygon corners
        corners = list(s4.get_stageiv_polygon(x ,y))
        
        # build a string for PostGIS
        linestr = 'LINESTRING('
        for c in corners:
            linestr += '%.8f %.8f,' % c
        linestr += '%.8f %.8f' % corners[0] # return to first point
        linestr += ')'

        cur.execute(query, (x, y, linestr))

conn.commit()

cur.close()
conn.close()
print('Stage IV grid polygons inserted into database.')
