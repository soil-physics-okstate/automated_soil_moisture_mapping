from datetime import datetime, timedelta
import numpy as np

start_date = datetime(2015, 12, 31)
end_date = datetime(2010, 01, 01)
dst_offset = timedelta(hours=6)

seasons = ['dummy'] + ['winter']*2 + ['fall']*3 + ['summer']*3 + ['spring']*3 + ['winter']

# 'date' is Current Date, 0000 UTC
# midnight is at Current Date, 0600 UTC
#date = date + timedelta(hours=6)

# read the Mesonet grid
import cPickle as pickle
meso_df = pickle.load(open('../static_data/mesonet/mesonet_geoinfo_ssurgo_stageiv.pickle'))

# soil moisture filenames
sm_fname = '../dynamic_data/soil_moisture/06Z/sm_data_%s.csv' # (date_str)

# the netCDF files started using a different format on 2014-03-17 0000Z
nc_switch = datetime(2014, 3, 17)

# location where NetCDF files are stored
nc_dir = '/home/OSU/jcpatto/hourly_stageiv_precip_netcdf/'

from netCDF4 import Dataset, MFDataset
from pandas import DataFrame, read_csv, concat

#df = DataFrame()
dfs = []

# NetCDF files' valid times include precip summed over the previous hour
# so data collection should stop at 0500 UTC
nc_hours = range(1, 24 + 1) # will not include 0600!
nc_dh = np.array([timedelta(hours = h) for h in nc_hours])

date = start_date + dst_offset
while date >= end_date:

    print '%s --- %s' % (datetime.now(), date)

    # get list of times and start a list of files
    nc_times = date - nc_dh
    nc_files = [nc_dir + t.strftime('%Y%m%d%H') + '.nc' for t in nc_times]

    # load the files, stitch along timestamp, and pull the precip data
    precips = []

    # the order matters, newer data should be opened first
    # so start with newer netCDF files

    if np.sum(nc_times >= nc_switch): # new netCDF files can be aggregated
        nc = MFDataset(np.array(nc_files)[nc_times >= nc_switch], aggdim='time')
        precips.append(nc.variables['Total_precipitation'][:]) # already in [mm]
        nc.close()

    if np.sum(nc_times < nc_switch): # older netCDF files must be opened one-by-one
        precips_old = []
        for nc_file in np.array(nc_files)[nc_times < nc_switch]: # open one-by-one
            nc = Dataset(nc_file)
        
            # there are two possible ways precip data are stored before nc_switch
            # "amountofprecip"
            if 'amountofprecip' in nc.variables:
                # convert to [mm], append
                precips_old.append(nc.variables['amountofprecip'][:]/100.) 

            # or "Total_precipitation" (like new netCDF files)
            elif 'Total_precipitation' in nc.variables:
                # take first axis, append
                precips_old.append(nc.variables['Total_precipitation'][:][0]) 
                    
            else:
                raise 'Uh oh!'

            nc.close()

        precips.append(np.stack(precips_old)) # combine along new axis

    precip = np.concatenate(precips) # combine new and old (works even if len(precips) == 1)

    # accumulate daily precip
    daily_precip = precip.reshape((24, 159, 335)).sum(axis=0)

    precip_df = DataFrame(daily_precip)
    precip_df.columns.name = 'x'
    precip_df.index.name = 'y'
    precip_df = precip_df.stack().swaplevel('x', 'y').sort_index()
    precip_df.name = 'daily_precip'

    date_str = date.strftime('%Y%m%d')
    sm_df = read_csv(sm_fname % (date_str), header=[0,1], index_col=0)
    sm_df.columns = ['%s_%s' % (col) for col in sm_df.columns.values]
    sm_df = sm_df[['vwc_5', 'vwc_25', 'vwc_60']]

    temp_df = meso_df[['s4x', 's4y']]\
        .join(precip_df, on=['s4x', 's4y'], how='inner')\
        .join(sm_df)\
        .drop(['s4x', 's4y'], axis=1)
    temp_df['Timestamp'] = date
    temp_df['Season'] = seasons[date.month]
    temp_df.index.name = 'STID'
    temp_df = temp_df.reset_index().set_index(['STID', 'Timestamp', 'Season'])

    dfs.append(temp_df)
    date = date - timedelta(days=1)

df = concat(dfs)
df.to_pickle('tmp/meso_precip_sm_data.pickle')
