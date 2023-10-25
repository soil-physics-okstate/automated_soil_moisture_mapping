#!/bin/bash
# Create/rewrite netCDF file of VWC data for the given month

month="$1"  # e.g. "2018-07"

version="1.2.0"
input_raster_dir="/opt/soilmapnik/output/raw_rasters"
input_model_dir="/opt/soilmapnik/output/semivariogram/model"
input_rmse_dir="/opt/soilmapnik/output/kriging_cross_validation"
output_netcdf_dir="/opt/soilmapnik/output/netcdf/monthly"
venv="/opt/soilmapnik/automated_soil_moisture_mapping/venv/bin/activate"

if [[ "${month}" == "$(date +%Y-%m)" ]]; then
  num_days=$(($(date +%-d) - 1))
else
  num_days=$(($(date --date="${month}-01 +1 month -1 day" +%d) - 1))
fi

datestr=$(for ((day=0; day<=${num_days}; day++)); do echo "${month}-01 +${day} days"; done)
dates=$(date -f - +"%Y-%m-%d" <<< "${datestr}")

source ${venv}
ncfile="vwc_${month}.nc"
python vwc_time_series_to_netcdf.py ${ncfile} ${version} "${input_raster_dir}" "${input_model_dir}" "${input_rmse_dir}" ${dates}
deactivate

cp ${ncfile} ${output_netcdf_dir}/ && rm ${ncfile}

