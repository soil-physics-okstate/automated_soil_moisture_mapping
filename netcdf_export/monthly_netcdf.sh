#!/bin/bash
# Create/rewrite netCDF file of VWC data for the given month

month="$1"  # e.g. "2018-07"

if [[ "${month}" == "$(date +%Y-%m)" ]]; then
  num_days=$(($(date +%d) - 1))
else
  num_days=$(($(date --date="${month}-01 +1 month -1 day" +%d) - 1))
fi

dates=()
for ((day=0; day<=${num_days}; day++)); do
  dates+=($(date --date="${month}-01 +${day} days" +"%Y-%m-%d"))
done

source /opt/soilmapnik/automated_soil_moisture_mapping/venv/bin/activate
python vwc_time_series_to_netcdf.py vwc_${month}.nc /opt/soilmapnik/output/raw_rasters export2 ${dates[@]}
deactivate

