#!/bin/bash
# Create/rewrite netCDF file of VWC data for the given month

month="$1"  # e.g. "2018-07"

input_raster_dir="/opt/soilmapnik/output/raw_rasters"
output_netcdf_dir="/opt/soilmapnik/output/netcdf/monthly"
venv="/opt/soilmapnik/automated_soil_moisture_mapping/venv/bin/activate"

if [[ "${month}" == "$(date +%Y-%m)" ]]; then
  num_days=$(($(date +%d) - 1))
else
  num_days=$(($(date --date="${month}-01 +1 month -1 day" +%d) - 1))
fi

dates=()
for ((day=0; day<=${num_days}; day++)); do
  dates+=($(date --date="${month}-01 +${day} days" +"%Y-%m-%d"))
done

source ${venv}
python vwc_time_series_to_netcdf.py vwc_${month}.nc ${input_raster_dir} export2 ${dates[@]}
deactivate

cp vwc_${month}.nc ${output_netcdf_dir}/ && rm vwc_${month}.nc

