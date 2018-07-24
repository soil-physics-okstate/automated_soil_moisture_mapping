#!/bin/bash
# Create/rewrite netCDF file of VWC data to go with the publication

start_day="2015-09-01"
#end date is 2017-08-31
num_days="730" 

dates=()
for ((day=0; day<=${num_days}; day++)); do
  dates+=($(date --date="${start_day} +${day} days" +"%Y-%m-%d"))
done

source /opt/soilmapnik/automated_soil_moisture_mapping/venv/bin/activate
python vwc_time_series_to_netcdf.py vwc_2015-09_2017-08.nc /opt/soilmapnik/output/raw_rasters export2 ${dates[@]}
deactivate

