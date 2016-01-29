from sys import argv
from datetime import datetime, timedelta
import numpy as np
from urllib import urlretrieve
from netCDF4 import MFDataset
from pandas import DataFrame
from os.path import isfile

ndays = [5, 30] # number of days to sum over

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object

# 'date' is Current Date, 0000 UTC
# midnight is at Current Date, 0600 UTC
date = date + timedelta(hours=6)

url = 'http://www.mesonet.org/data/public/noaa/qpe/abrfc/1hr_netcdf/%04d/%02d/%02d/%s.nc'
# url takes (year, month, day, t_str)

# set data_dir
data_dir = '../data/'

# location to store NetCDF files temporarily
nc_dir = '/home/jpatton/RFC_StageIV_QPE_nc/temp/'

# loop over list of ndays
for nd in ndays:

    # NetCDF files' valid times include precip summed over the previous hour
    # so data collection should stop at 0500 UTC
    nc_hours = range(1, 24*nd + 1) # will not include 0600!
    nc_dh = np.array([timedelta(hours = h) for h in nc_hours])

    # get list of times and start a list of files
    nc_times = date - nc_dh
    nc_files = []

    # loop over all times
    for t in nc_times:

        # get the time string
        t_str = t.strftime('%Y%m%d%H') # yyyymmddHH

        # get the filename and download the file to local storage
        nc_file = nc_dir + t_str + '.nc'
        if not isfile(nc_file): # check if file already exists
            urlretrieve(url % (t.year, t.month, t.day, t_str), nc_file)
        nc_files.append(nc_file)

    # load the files and pull the precip data
    nc = MFDataset(nc_files, aggdim='time')
    precip = nc.variables['Total_precipitation'][:]
    nc.close()

    # calculate the cumulative precipitation
    cum_precip = np.sum(precip, axis=0)

    # put the precipitation in a table by x and y
    precip_df = DataFrame(cum_precip)
    precip_df.columns.name = 'x'
    precip_df.index.name = 'y'
    precip_df = precip_df.stack().swaplevel('x', 'y').sort_index()
    precip_df.name = 'precip_%dday' % (nd)
    
    # save precipitation to CSV
    out_dir = data_dir + 'precip/stageiv_%d_day/' % (nd)
    precip_df.to_csv(out_dir + '%d_day_precip_%s.csv' % (nd, date.strftime('%Y%m%d')))

