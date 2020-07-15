#!/bin/bash
# Create/rewrite netCDF file of VWC data to go with the publication

version="1.2.0"
input_raster_dir="/opt/soilmapnik/output/raw_rasters"
input_model_dir="/opt/soilmapnik/output/semivariogram/model"
input_rmse_dir="/opt/soilmapnik/output/kriging_cross_validation"
output_netcdf_dir="/opt/soilmapnik/output/netcdf/monthly"
venv="/opt/soilmapnik/automated_soil_moisture_mapping/venv/bin/activate"

start_day="2015-09-01"
#end date is 2017-08-31
num_days="730" 

datestr=$(for ((day=0; day<=${num_days}; day++)); do echo "${start_day} +${day} days"; done)
dates=$(date -f - +"%Y-%m-%d" <<< "${datestr}")

source ${venv}
python vwc_time_series_to_netcdf.py vwc_2015-09_2017-08.nc ${version} "${input_raster_dir}" "${input_model_dir}" "${input_rmse_dir}" ${dates}
deactivate

