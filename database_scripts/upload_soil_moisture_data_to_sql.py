dbname = 'soilmapnik'

from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
depth = int(argv[2]) # depth [cm]
#map_var = argv[3] # map variable
map_var = 'vwc' 

# get date into a datetime
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # get date string

# set input data directory
input_data_dir = '../output/kriging_result/'
fname = '%s_%02dcm_%s.csv' % (map_var, depth, date_str)

# load data
from pandas import read_csv

df = read_csv(input_data_dir + fname, index_col=0)
df = df.rename(columns={map_var: 'product_value'})
df['product_valid'] = date
df['product_name'] = map_var
df['product_depth'] = depth

## upload to database
import psycopg2
conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

# clean table first
query = '''
DELETE FROM soil_moisture_data WHERE
((product_valid = %s) AND (product_name = %s) AND (product_depth = %s));
'''
cur.execute(query, (date, map_var, depth))
conn.commit()
conn.close()

# then add data
from sqlalchemy import create_engine
engine = create_engine('postgresql:///%s' % (dbname))
df.to_sql('soil_moisture_data', engine, if_exists='append')
