import sys
from datetime import datetime, timedelta
import numpy as np
from urllib import urlretrieve
from pandas import DataFrame
from os.path import isfile

api_params = { # parameters for the Antecedent Precipitation Index
    05: {'days': 24, 'k': 1.025},
    25: {'days': 24, 'k': 1.006},
    60: {'days': 22, 'k': 0.993}
}
nd = 24 # number of days to download data for (max of API days params)

date_in = sys.argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object

# 'date' is Current Date, 0000 UTC
# midnight is at Current Date, 0600 UTC
date = date + timedelta(hours=6)

url = 'http://www.mesonet.org/data/public/noaa/qpe/abrfc/1hr_netcdf/%04d/%02d/%02d/%s.nc'
# url takes (year, month, day, t_str)

# the netCDF files started using a different format on 2014-03-17 0000Z
nc_switch = datetime(2014, 3, 17)

# set data directories
input_data_dir = '../static_data/'
output_data_dir = '../dynamic_data/'

# location to store NetCDF files temporarily
nc_dir = '/opt/soilmapnik/hourly_stageiv_precip_netcdf/'

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

# load the files, stitch along timestamp, and pull the precip data
precips = []

# the order matters, newer data should be opened first, so start with newer netCDF files

if np.sum(nc_times >= nc_switch): # newer netCDF files can be aggregated
    from netCDF4 import MFDataset
    nc = MFDataset(np.array(nc_files)[nc_times >= nc_switch], aggdim='time')
    precips.append(nc.variables['Total_precipitation'][:]) # already in [mm]
    nc.close()

if np.sum(nc_times < nc_switch): # older netCDF files must be opened one-by-one
    from netCDF4 import Dataset
    precips_old = []
    for nc_file in np.array(nc_files)[nc_times < nc_switch]: # open one-by-one
        nc = Dataset(nc_file)
        
        # there are two possible ways precip data are stored before nc_switch
        # "amountofprecip"
        if 'amountofprecip' in nc.variables:
            precips_old.append(nc.variables['amountofprecip'][:]/100.) # convert to [mm], append

        # or "Total_precipitation" (like new netCDF files)
        elif 'Total_precipitation' in nc.variables:
            precips_old.append(nc.variables['Total_precipitation'][:][0]) # take first axis, append

        # if neither of those are found, exit
        else:
            print 'Could not find precipitation data in %s' % (nc_file)
            sys.exit(1)

        nc.close()

    precips.append(np.stack(precips_old)) # combine along new axis

precip = np.concatenate(precips) # combine new and old (works even if len(precips) == 1)

# accumulate daily precip
daily_precip = precip.reshape((24, nd, 159, 335)).sum(axis=0)

api_df = []
# calculate the antecedent precipitation indicies
for depth in sorted(api_params.keys()):
    scales = api_params[depth]['k']**np.arange(0, -api_params[depth]['days'], -1)
    api_components = []
    for i,scale in enumerate(scales):
        api_components.append(daily_precip[i]*scale)
    api = np.array(api_components).sum(axis=0)

    temp_df = DataFrame(api)
    temp_df.columns.name = 'x'
    temp_df.index.name = 'y'
    temp_df = temp_df.stack().swaplevel('x', 'y').sort_index()
    temp_df.name = depth
    temp_df = DataFrame(temp_df)
    
    if len(api_df) == 0:
        api_df = temp_df
    else:
        api_df = api_df.join(temp_df)
    
# save precipitation to CSV
out_dir = output_data_dir + 'precip/stageiv_api/'
api_df.to_csv(out_dir + 'api_%s.csv' % (date.strftime('%Y%m%d')))
