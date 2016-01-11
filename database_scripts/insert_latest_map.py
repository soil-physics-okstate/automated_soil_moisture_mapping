from sys import argv
from datetime import datetime

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date.strftime('%Y%m%d') # get date string

# set depths and variables
sm_depths = [5, 25, 60]
sm_vars = ['vwc']

# set the data directory and filenames
data_dir = '../outputs/data/'
data_fname = 'oksmm_%s_%02dcm_%s.csv' # (var, depth, date)

import psycopg2

# open connection to database
conn = psycopg2.connect('')
cur = conn.cursor()

# build query
query = 'INSERT INTO soil_moisture_timeseries (id, valid, depth, vwc) VALUES (%s, %s, %s, %s);'

from pandas import read_csv

# loop over depths and vars
for d in sm_depths:
    for v in sm_vars:

        # load file
        df = read_csv(data_dir + data_fname % (v, d, date_str))

        # loop over file and insert into database
        for row in df.iterrows():
            cur.execute(query, (row[1]['id'], date, d, row[1]['vwc']))

        # commit inserts after each file
        conn.commit()

# close database connection
conn.close()

