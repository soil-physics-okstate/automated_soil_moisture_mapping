import os

import numpy as np

from urllib import urlretrieve
from netCDF4 import MFDataset

from pandas import DataFrame

# location to store NetCDF files temporarily
nc_dir = '/home/jpatton/RFC_StageIV_QPE_nc/api_data/temp/'

# location to store processed data
data_dir = '/home/jpatton/RFC_StageIV_QPE_nc/api_data/'

# Mesonet URL
url = 'http://www.mesonet.org/data/public/noaa/qpe/abrfc/1hr_netcdf/%04d/%02d/%02d/%s.nc'
# url takes (year, month, day, t_str)

# set bounds for years
years = range(2014, 2016)

# set bounds for months (avoid freezing)
month_i = 4  # start in April
month_f = 10 # end in October

# compute daily data starting/ending at midnight CST
hours = range(24)

# 0000 CST is at 0600 UTC
from datetime import timedelta, datetime
cst2utc = timedelta(hours=6)

# load Mesonet locations
import pickle
meso_df = pickle.load(open('../data/grid/mesonet_geoinfo.pickle'))[['s4x', 's4y']]

# loop over years
for year in years:

    # initialize date
    month = month_i
    d = datetime(year, month, 1) + cst2utc

    # loop over months
    while month < month_f:

        # NetCDF files' valid times include precip summed over the previous hour
        # so data collection should stop at 0500 UTC
        nc_dh = np.array([timedelta(hours = h) for h in hours])

        # get list of times and start a list of files
        nc_times = d + nc_dh
        nc_files = []

        # loop over all times
        for t in nc_times:

            # get the time string
            t_str = t.strftime('%Y%m%d%H') # yyyymmddHH

            # get the filename and download the file to local storage
            nc_file = nc_dir + t_str + '.nc'
            print 'Downloading %s... ' % (url % (t.year, t.month, t.day, t_str)),
            urlretrieve(url % (t.year, t.month, t.day, t_str), nc_file)
            print 'Done.'
            nc_files.append(nc_file)

        # load the files and pull the precip data
        nc = MFDataset(nc_files, aggdim='time')
        precip = nc.variables['Total_precipitation'][:]
        nc.close()

        # delete the NetCDF files
        for nc_file in nc_files: os.remove(nc_file)

        # calculate the daily cumulative precipitation
        cum_precip = np.sum(precip, axis=0)

        # put the precipitation in a table by x and y
        precip_df = DataFrame(cum_precip)
        precip_df.columns.name = 'x'
        precip_df.index.name = 'y'
        precip_df = precip_df.stack().swaplevel('x', 'y').sort_index()
        precip_df.name = 'precip'

        # pull out only the data for the Mesonet sites
        df = meso_df.join(precip_df, on=['s4x', 's4y'])['precip']
        df.name = 'precip'
    
        # save precipitation to CSV
        out_dir = data_dir
        df.to_csv(out_dir + 'daily_precip_%s.csv' % (d.strftime('%Y%m%d')))

        # increment day
        d = d + timedelta(days=1)
        month = d.month
