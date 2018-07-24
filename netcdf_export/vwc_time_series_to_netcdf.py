#
# Convert consecutive daily sets of soil moisture rasters (all 
# three depths) into a single netCDF file.
#
# This script requires a minimum of three command line arguments:
#     1. output netcdf file
#     2. directory of raster files (.tif)
#     3. type of raster ('daily_temp', 'export', or 'web')
#          when the type is daily_temp, we should only expect one date
#          Type         Filename Format
#          -----------------------------------
#          daily_temp   temp_{depth}cm_vwc.tif
#          export       {date}_{depth}.tif
#          export2      {date}_vwc_{depth}cm.tif
#          web          raster_{date}_vwc_{depth}cm.tif
#     4. (and on up) date strings in %Y-%m-%d format
#

import numpy as np
import datetime as dt
import pytz
import os
import gdal
import netCDF4
import ok_vwc_grid # lats and lons
import sys


ncfile = sys.argv[1]
raster_dir = sys.argv[2]
raster_type = sys.argv[3]
dates = sys.argv[4:]


def cst2utc_iso(d):
    '''
    Convert a date string in '%Y-%m-%d' format representing CST (i.e.
    'Etc/GMT+6') to the ISO formatted string of the time in UTC.
    '''
    return pytz.timezone('Etc/GMT+6').localize(dt.datetime.strptime(d,'%Y-%m-%d')).astimezone(pytz.utc).isoformat()



now_time = dt.datetime.utcnow()
now_timestamp = str(now_time) + ' UTC'

num_y = len(ok_vwc_grid.lats)
num_x = len(ok_vwc_grid.lons)

x = ok_vwc_grid.xs
y = ok_vwc_grid.ys

depths = [5, 25, 60]
num_depths = len(depths)

basedate = dt.datetime(1900,1,1,0,0,0)

raster_name_patterns = {
    'daily_temp':'temp_%scm_vwc.tif',
    'export':'%s_%s.tif',
    'export2':'%s_vwc_%scm.tif',
    'web':'raster_%s_vwc_%scm.tif'
}



####################################
#
# Create / Open the netCDF dataset
#
####################################

nc = netCDF4.Dataset(ncfile,'w',clobber=True,format='NETCDF3_CLASSIC')  
#nc = netCDF4.Dataset(ncfile,'w',clobber=True,format='NETCDF4')   # QGIS renders this upside-down



#####################
#
# Create dimensions
#
#####################

nc.createDimension('x',num_x)
nc.createDimension('y',num_y)
nc.createDimension('depth',num_depths)
nc.createDimension('time',None)



#############################################
#
# Create variables and set their properties
#
#############################################

x_var = nc.createVariable('x','i4',('x'))
x_var.axis = 'X'
x_var.standard_name = 'projection_x_coordinate'
x_var.units = 'meters'

y_var = nc.createVariable('y','i4',('y'))
y_var.axis = 'Y'
y_var.standard_name = 'projection_y_coordinate'
y_var.units = 'meters'

depth_var = nc.createVariable('depth','i4',('depth'))
depth_var.axis = 'Z'
depth_var.long_name = 'depth below soil surface'
depth_var.positive = 'down'
depth_var.standard_name = 'depth'
depth_var.units = 'centimeters'

time_var = nc.createVariable('time','f4',('time'))
time_var.axis = 'T'
time_var.long_name = 'time'
time_var.standard_name = 'time'
time_var.calendar = 'gregorian'
#time_var.units = 'days since 1900-01-01 00:00:00 -6:00' # the python netcdf library wants to subtract this instead of recognizing it as a time zone offset
time_var.units = 'days since 1900-01-01 00:00:00 -0600'

lon_var = nc.createVariable('lon','f8',('x'))
lon_var.long_name = 'x coordinate longitude'
lon_var.standard_name = 'longitude'
lon_var.units = 'degrees_east'
lon_var.valid_max = 180.0
lon_var.valid_min = -180.0

lat_var = nc.createVariable('lat','f8',('y'))
lat_var.long_name = 'y coordinate latitude'
lat_var.standard_name = 'latitude'
lat_var.units = 'degrees_north'
lat_var.valid_max = 90.0
lat_var.valid_min = -90.0

vwc_var = nc.createVariable('vwc','f4',('time','depth','y','x'), fill_value=-999.0)
vwc_var.cell_methods = 'time: depth: y: x: point'
vwc_var.coordinates = 'time depth y x'
vwc_var.coverage_content_type = 'modelResult'  # for ACCD-1.3
vwc_var.grid_mapping = 'crs'
vwc_var.long_name = 'volumetric water content'
vwc_var.standard_name = 'volume_fraction_of_water_in_soil'
vwc_var.units = 'cm3 cm-3'
vwc_var.valid_max = 1;
vwc_var.valid_min = 0;


# http://cfconventions.org/wkt-proj-4.html
# http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/build/apf.html
crs_var = nc.createVariable('crs','i2')
# Working in THREDDS and QGIS but not right in ArcGIS
crs_var.grid_mapping_name = 'lambert_cylindrical_equal_area'
crs_var.longitude_of_central_meridian = -97.674
crs_var.standard_parallel = 35.3
crs_var.false_easting = 100.000000002310
crs_var.false_northing = -4534203.106432600878
crs_var.semi_major_axis = 6378137
#crs_var.semi_minor_axis = 6378137
crs_var.inverse_flattening = 298.257223563
crs_var.proj4_params = '+proj=cea +a=6378137 +b=6378137 +lon_0=-97.674 +lat_ts=35.3 +x_0=100.000000002310 +y_0=-4534203.106432600878 +units=m +no_defs'



#########################
#
# Set global attributes
#
#########################

nc.institution = 'Oklahoma State University'
nc.Conventions = 'CF-1.7, ACDD-1.3'
#nc.Metadata_Conventions = 'Unidata Dataset Discovery v1.0' # this is obsoleted by ACDD-1.3
nc.metadata_link = ''
nc.cdm_data_type = 'GRID'
nc.title = 'High Resolution Soil Moisture Mapping for Oklahoma'
nc.comment = 'The maps of soil volumetric water content (VWC) are generated using (1) in-situ soil moisture data from the Oklahoma Mesonet used in a regression kriging routine that incorporates (2) soil texture (percent sand) estimates from USDA-NRCS SSURGO and (3) an antecedent precipitation index computed from NOAA NCEP StageIV precipitation estimates. Each pixel is 800 by 800 meters, which is approximately the same area as one quarter section. The maps are valid at midnight local standard time (0600 UTC).'
nc.acknowledgment = 'This material is based on work supported by the National Science Foundation under Grant No. IIA-1301789. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.'
nc.project = 'Adapting Socio-ecological Systems to Increased Climate Variability'
nc.references = ''
nc.source = 'Model-generated. Code available at https://github.com/soil-physics-okstate/automated_soil_moisture_mapping'
nc.history = 'Export to netCDF at %s' % now_timestamp
# more global attributes for ACDD
nc.summary = ''
nc.keywords = 'soil moisture, volumetric water content, vwc'
nc.keywords_vocabulary = ''
nc.license = ''
nc.standard_name_vocabulary = 'CF Standard Name Table v57'  # http://cfconventions.org/standard-names.html

nc.creator_name = 'Tyson Ochsner'
nc.creator_institution = 'Oklahoma State University'
nc.creator_type = 'person'
nc.creator_email = 'tyson.ochsner@okstate.edu'
nc.creator_url = 'http://soilphysics.okstate.edu/'

nc.contributor_name = 'Tyson Ochsner, Evan Linde, Jason C. Patton'
nc.contributor_role = 'Faculty/PI, Research Computing Staff, Postdoctoral Fellow'

nc.publisher_name = 'Oklahoma State University High Performance Computing Center'
nc.publisher_institution = 'Oklahoma State University'
nc.publisher_type = 'group'
nc.publisher_email = 'hpcc@okstate.edu'
nc.publisher_url = 'http://hpcc.okstate.edu/'

nc.naming_authority = 'edu.okstate.hpcc'
#nc.id= '' 

nc.date_created = now_time.isoformat()
nc.date_modified = now_time.isoformat()
nc.date_issued = now_time.isoformat()

nc.geospatial_lat_max = max(ok_vwc_grid.lats)
nc.geospatial_lat_min = min(ok_vwc_grid.lats)
nc.geospatial_lon_max = max(ok_vwc_grid.lons)
nc.geospatial_lon_min = min(ok_vwc_grid.lons)
nc.geospatial_vertical_max = 60
nc.geospatial_vertical_min = 5
nc.geospatial_vertical_units = 'centimeters'
nc.geospatial_vertical_positive = 'down'
nc.time_coverage_resolution = 'P1D'
nc.time_coverage_start = cst2utc_iso(dates[0])
nc.time_coverage_end = cst2utc_iso(dates[-1])
nc.time_coverage_duration = 'P%dD' % (len(dates) - 1)



#########################################
#
# Assign values to coordinate variables
#
#########################################

#x_var[:] = x
x_var[:] = ok_vwc_grid.xs
#y_var[:] = y[::-1] # qgis/gdal interprets netcdf upside-down
#y_var[:] = y
y_var[:] = ok_vwc_grid.ys[::-1]
#y_var[:] = ok_vwc_grid.ys
depth_var[:] = depths
#lat_var[:] = ok_vwc_grid.lats # qgis/gdal interprets netcdf upside-down
lat_var[:] = ok_vwc_grid.lats[::-1]
lon_var[:] = ok_vwc_grid.lons



##########################
#
# Add time and vwc values
#
###########################

itime=0  # index of the time value (always start at zero)
for date_str in dates:
    # Convert date string to a datetime object
    date = dt.datetime.strptime(date_str, '%Y-%m-%d')
    # Calculate number of days since basedate
    dtime = (date - basedate).total_seconds() / 86400.
    # Add the time value to the netCDF file
    time_var[itime] = dtime
    # Add vwc data for the current time value
    for d in depths:
        idepth = depths.index(d)  # index of the depth value
        # Set the name of the raster file based on raster_type
        # We're going to assume 'export' if it's not 'daily_temp'
        if raster_type == 'daily_temp':
            #raster_filename = 'temp_' + str(d) + 'cm_vwc.tif'
            raster_filename = raster_name_patterns[raster_type] % (str(d))
        else:
            #raster_filename = date_str + '_' + str(d) + '.tif'
            raster_filename = raster_name_patterns[raster_type] % (date_str, str(d))
        raster_file = os.path.join(raster_dir, raster_filename)
        # Read in the raster file for the current date and depth
        ds = gdal.Open(raster_file)
        # When the ground temperature is below freezing, there's no VWC value
        # and rasters might not be the usual 973x470, so instead of directly
        # reading the raster into an array, create an "empty" array (actually
        # filled with -999) of the correct size, then use gdal's GeoTransform
        # data to figure out the offsets needed to put the data in the right
        # place.
        #a = ds.ReadAsArray()
        a = np.full( (470,973), -999.0, dtype=float ) # Create array of -999
        # The GeoTransform on a good/full raster file should be:
        # (-484000, 800, 0, 140000, 0, -800) as floating point numbers.
        xoffset = abs(-484000 - int(ds.GetGeoTransform()[0]))/800
        yoffset = (140000 - int(ds.GetGeoTransform()[3]))/800
        xend = xoffset + ds.RasterXSize
        yend = yoffset + ds.RasterYSize
        a[yoffset:yend, xoffset:xend] = ds.ReadAsArray()
        # Add the raster data to the netCDF file
        vwc_var[itime,idepth,:,:] = a
        #vwc_var[itime,idepth,:,:] = a[::-1,:]
    # End of the depths loop, back in the main dates loop
    # Break out of the loop if the raster type is 'daily_temp'
    # since multiple dates don't make sense here
    if raster_type == 'daily_temp':
        break
    # Increment the time index
    itime += 1



################################
#
# Close the netCDF dataset
# i.e. finish writing the file
#
################################

nc.close()

