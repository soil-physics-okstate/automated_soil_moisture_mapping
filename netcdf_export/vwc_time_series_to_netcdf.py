#
# Convert consecutive daily sets of soil moisture rasters and related
# outputs from the soil moisture mapping system (all three depths) 
# into a single netCDF file.
#
# This script requires a minimum of three command line arguments:
#     1. output netcdf file
#     2. directory of raster files (.tif)
#     3. directory of model files (.csv)
#     4. directory of rmse files (.csv)
#     5. (and on up) date strings in %Y-%m-%d format
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
version = sys.argv[2]
raster_dir = sys.argv[3]
model_dir = sys.argv[4]
rmse_dir = sys.argv[5]
dates = sys.argv[6:]


def cst2utc_iso(d):
    '''
    Convert a date string in '%Y-%m-%d' format representing CST (i.e.
    'Etc/GMT+6') to the ISO formatted string of the time in UTC.
    '''
    return pytz.timezone('Etc/GMT+6').localize(dt.datetime.strptime(d,'%Y-%m-%d')).astimezone(pytz.utc).isoformat()


# version-specific information
version_references = {
    # References - don't include DOIs for specific code releases
    '1.0.0':'doi:10.1029/2018WR024535 doi:10.5281/zenodo.3717921',
    '1.1.0':'doi:10.1029/2018WR024535 doi:10.5281/zenodo.3717921',
    '1.2.0':'doi:10.1029/2018WR024535 doi:10.5281/zenodo.3717921 doi:10.2136/sssaj2018.12.0481',
}
version_comments = {
    '1.0.0':'This version of the data (1.0.0) was created with the initial soil moisture model code and has known problems. The problems known in this version are corrected in version 1.1.0.',
    '1.1.0':'This version of the data (1.1.0) corrects known problems in version 1.0.0. Model fitting has been improved to enforce non-negative nuggets and the gaussian (gaussV) model has been eliminated.',
    '1.2.0':'This version of the data (1.2.0) is based on an updated soil property database (MesoSoil version 2.0) and an updated sensor calibration for estimating matric potential as described in: Zhang, Y., Ochsner, T. E., Fiebrich, C. A., & Illston, B. G. (2019). Recalibration of Sensors in One of The World\'s Longest Running Automated Soil Moisture Monitoring Networks. Soil Science Society of America Journal, 83(4), 1003-1011. doi:10.2136/sssaj2018.12.0481.',
}
version_dois = {
    # DOIs issued for specific versions of the code
    '1.0.0':'10.5281/zenodo.3717922',
    '1.1.0':'10.5281/zenodo.3875685',
    '1.2.0':'10.5281/zenodo.3945534',
}



now_time = dt.datetime.utcnow()
now_timestamp = str(now_time) + ' UTC'

num_y = len(ok_vwc_grid.lats)
num_x = len(ok_vwc_grid.lons)

#x = ok_vwc_grid.xs
#y = ok_vwc_grid.ys

depths = [5, 25, 60]
num_depths = len(depths)

models = {
    'spherV':1,
    'exponV':2,
    'gaussV':3
}
models_str = str(models).replace("'",'').replace('{','').replace('}','')

basedate = dt.datetime(1900,1,1,0,0,0)

raster_name_pattern = '%s_%s_%scm.tif' # %(date, varname, depth) where date like %Y-%m-%d
model_name_pattern = 'model_%scm_%s.csv' # %(depth, date) where date like %Y%m%d
rmse_name_pattern = 'rmse_%scm_%s.csv' # %(depth, date) where date like %Y%m%d


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
#vwc_var.ancillary_variables = 'kriging_residual kriging_variance'
vwc_var.ancillary_variables = 'kriging_variance'
vwc_var.cell_methods = 'time: depth: y: x: point'
vwc_var.coordinates = 'time depth y x'
vwc_var.coverage_content_type = 'modelResult'  # for ACCD-1.3
vwc_var.grid_mapping = 'crs'
vwc_var.long_name = 'volumetric water content'
vwc_var.standard_name = 'volume_fraction_of_water_in_soil'
vwc_var.units = 'cm3 cm-3'
vwc_var.valid_max = 1;
vwc_var.valid_min = 0;

#kres_var = nc.createVariable('kriging_residual','f4',('time','depth','y','x'), fill_value=-999.0)
#kres_var.cell_methods = 'time: depth: y: x: point'
#kres_var.coordinates = 'time depth y x'
#kres_var.coverage_content_type = 'modelResult'  # for ACCD-1.3
#kres_var.grid_mapping = 'crs'
#kres_var.long_name = 'kriging residual' 

kvar_var = nc.createVariable('kriging_variance','f4',('time','depth','y','x'), fill_value=-999.0)
kvar_var.cell_methods = 'time: depth: y: x: point'
kvar_var.coordinates = 'time depth y x'
kvar_var.coverage_content_type = 'modelResult'  # for ACCD-1.3
kvar_var.grid_mapping = 'crs'
kvar_var.long_name = 'kriging variance' 
kvar_var.units = '(cm3 cm-3)^2'

model_var = nc.createVariable('model','i2',('time','depth'), fill_value=-999)
model_var.ancillary_variables = 'nugget sill range rmse'
model_var.coordinates = 'time depth'
model_var.coverage_content_type = 'modelResult'
model_var.long_name = 'model'
model_var.note = 'Models are encoded as follows: %s. The gaussian (gaussV) model is only used in the 1.0 version of the data.' % (models_str)

nugget_var = nc.createVariable('nugget','f4',('time','depth'), fill_value=-999.0)
nugget_var.coordinates = 'time depth'
nugget_var.coverage_content_type = 'modelResult'
nugget_var.long_name = 'nugget'
nugget_var.units = '(cm3 cm-3)^2'

sill_var = nc.createVariable('sill','f4',('time','depth'), fill_value=-999.0)
sill_var.coordinates = 'time depth'
sill_var.coverage_content_type = 'modelResult'
sill_var.long_name = 'partial sill'
sill_var.units = '(cm3 cm-3)^2'

range_var = nc.createVariable('range','f4',('time','depth'), fill_value=-999.0)
range_var.coordinates = 'time depth'
range_var.coverage_content_type = 'modelResult'
range_var.long_name = 'range'
range_var.units = 'm'

rmse_var = nc.createVariable('rmse','f4',('time','depth'), fill_value=-999.0)
rmse_var.coordinates = 'time depth'
rmse_var.coverage_content_type = 'modelResult'
rmse_var.long_name = 'root mean squared error from leave-one-out cross validation'
rmse_var.units = 'cm3 cm-3'

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
#nc.metadata_link = '' # omit this since we're not keeping a separate store of metadata
nc.cdm_data_type = 'GRID'
nc.title = 'High Resolution Soil Moisture Mapping for Oklahoma'
nc.comment = 'The maps of soil volumetric water content (VWC) are generated using (1) in-situ soil moisture data from the Oklahoma Mesonet used in a regression kriging routine that incorporates (2) soil texture (percent sand) estimates from USDA-NRCS SSURGO and (3) an antecedent precipitation index computed from NOAA NWS Arkansas Red Basin River Forecast Center multisensor precipitation estimates. Each pixel is 800 by 800 meters, which is approximately the same area as one quarter section. The maps are valid at midnight local standard time (0600 UTC).'
nc.acknowledgment = 'This material is based on work supported by the National Science Foundation under Grant No. IIA-1301789. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.'
nc.project = 'Adapting Socio-ecological Systems to Increased Climate Variability'
#nc.references = 'doi:10.1029/2018WR024535 doi:10.5281/zenodo.3717921'
nc.references = version_references[version] + ' ' + version_dois[version]
nc.source = 'Model-generated (version %s, %s). Code available at https://github.com/soil-physics-okstate/automated_soil_moisture_mapping' % (version, version_dois[version])
nc.product_version = version
nc.version_comment = version_comments[version]
#nc.processing_level = ''
nc.history = 'Export to netCDF at %s' % now_timestamp
# more global attributes for ACDD
nc.summary = 'This dataset represents the output of the automated soil moisture mapping system for the state of Oklahoma, USA, as described in Ochsner et al. (2019; doi:10.1029/2018WR024535) and displayed at http://soilmoisture.okstate.edu/.'
nc.keywords = 'soil moisture, volumetric water content, vwc'
#nc.keywords_vocabulary = '' # we're not using a controlled vocabulary that's already defined somewhere
nc.license = '''CC BY-SA. By downloading this dataset you agree to the following terms of use. You agree that you will not copy, share, or redistribute the data in any form. This dataset is provisional, and the creators assume no liability for its contents. You agree that any publication using data from this dataset will cite the following paper:  
 
Ochsner, T.E., E. Linde, M. Haffner and J. Dong. 2019. Mesoscale Soil Moisture Patterns Revealed Using a Sparse In Situ Network and Regression Kriging. Water Resour. Res. 55: 4785-4800. doi:10.1029/2018wr024535.
'''
nc.standard_name_vocabulary = 'CF Standard Name Table v57'  # http://cfconventions.org/standard-names.html

nc.creator_name = 'Tyson Ochsner'
nc.creator_institution = 'Oklahoma State University'
nc.creator_type = 'person'
nc.creator_email = 'tyson.ochsner@okstate.edu'
nc.creator_url = 'http://soilphysics.okstate.edu/'

nc.contributor_name = 'Tyson Ochsner, Evan Linde, Jason C. Patton, Matthew Haffner, Jingnuo Dong'
nc.contributor_role = 'Faculty/PI, Research Computing Staff, Postdoctoral Fellow, Graduate Research Assistant, Graduate Research Assistant'

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

x_var[:] = ok_vwc_grid.xs
y_var[:] = ok_vwc_grid.ys[::-1] # reverse the array because qgis/gdal interprets netcdf upside-down
depth_var[:] = depths
lat_var[:] = ok_vwc_grid.lats[::-1] # reverse the array because qgis/gdal interprets netcdf upside-down
lon_var[:] = ok_vwc_grid.lons



##########################
#
# Add time and vwc values
#
###########################

itime=0  # index of the time value (always start at zero)
for date_str in dates:
    # Get date string without dashes (for some file names)
    date_str2 = date_str.replace('-','')
    # Convert date string to a datetime object
    date = dt.datetime.strptime(date_str, '%Y-%m-%d')
    # Calculate number of days since basedate
    dtime = (date - basedate).total_seconds() / 86400.
    # Add the time value to the netCDF file
    time_var[itime] = dtime
    # Add vwc data for the current time value
    for d in depths:
        idepth = depths.index(d)  # index of the depth value

        # initialize non-grid variables with na values
        # these will get replaced with real data if it exists
        model_var[itime,idepth] = -999
        nugget_var[itime,idepth] = -999.0
        sill_var[itime,idepth] = -999.0
        range_var[itime,idepth] = -999.0
        rmse_var[itime,idepth] = -999.0

        # pull in model, nugget, sill, range, rmse
        model_filename = model_name_pattern % (str(d), date_str2)
        model_file = os.path.join(model_dir, model_filename)
        with open(model_file, 'r') as fh:
            model_data = fh.read().replace('\r','').replace('\n',',').split(',')
            model_var[itime,idepth] = models[model_data[0]]
            nugget_var[itime,idepth] = float(model_data[1])
            sill_var[itime,idepth] = float(model_data[2])
            range_var[itime,idepth] = float(model_data[3])

        rmse_filename = rmse_name_pattern % (str(d), date_str2)
        rmse_file = os.path.join(rmse_dir, rmse_filename)
        with open(rmse_file, 'r') as fh:
            rmse_data = fh.read().replace('\r','').replace('\n','')
            #rmse_data = np.loadtxt(rmse_file) # should only contain a single floating point number
            rmse_var[itime,idepth] = float(rmse_data)

        #for v in ['vwc','residual','variance']:
        for v in ['vwc','variance']:
            raster_filename = raster_name_pattern % (date_str, v, str(d))
            raster_file = os.path.join(raster_dir, raster_filename)
            # When the ground temperature is below freezing, there's no VWC value
            # and rasters might not be the usual 973x470, so instead of directly
            # reading the raster into an array, create an "empty" array (actually
            # filled with -999) of the correct size, then use gdal's GeoTransform
            # data to figure out the offsets needed to put the data in the right
            # place.
            #a = ds.ReadAsArray()
            a = np.full( (470,973), -999.0, dtype=float ) # Create array of -999
            # Read in the raster file for the current date and depth
            ds = gdal.Open(raster_file)
            if (ds != None):
                # The GeoTransform on a good/full raster file should be:
                # (-484000, 800, 0, 140000, 0, -800) as floating point numbers.
                xoffset = abs(-484000 - int(ds.GetGeoTransform()[0]))/800
                yoffset = (140000 - int(ds.GetGeoTransform()[3]))/800
                xend = xoffset + ds.RasterXSize
                yend = yoffset + ds.RasterYSize
                a[yoffset:yend, xoffset:xend] = ds.ReadAsArray()
            # Add the raster data to the netCDF file
            if(v == 'vwc'):
                vwc_var[itime,idepth,:,:] = a
                #vwc_var[itime,idepth,:,:] = a[::-1,:]
            if(v == 'residual'):
                kres_var[itime,idepth,:,:] = a
            if(v == 'variance'):
                kvar_var[itime,idepth,:,:] = a
    # End of the depths loop, back in the main dates loop
    # Increment the time index
    itime += 1



################################
#
# Close the netCDF dataset
# i.e. finish writing the file
#
################################

nc.close()

