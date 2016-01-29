#!/bin/bash

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging

# set path for Matlab
export PATH=$PATH:/usr/bin:/opt/MATLAB-R2015a/bin

# get date
date=`date --utc +"%Y-%m-%d"`
echo "Mapping for ${date}..."

# load data
cd data_retrieval
echo "  Getting Mesonet soil moisture data for ${date}..."
python get_soil_moisture_data.py $date > log/soil_moisture_${date}.log
echo "  Getting StageIV antecedent precipitation data for ${date}..."
python get_stageiv_api.py $date > log/stageiv_api_${date}.log
cd ..

# do regression
cd regression
echo "  Building regression models for ${date}..."
python do_regression.py $date > log/regression_${date}.log
cd ..

echo "  Kriging, creating output, and plotting depths in parallel for ${date}..."
parallel --gnu -P 3 "bash krige_plot_parallel.sh $date {1}" ::: 5 25 60
echo "  Done."

# copy maps to servers
cd server_functions
echo "Copying maps to server..."
bash copy_map_to_server.sh
echo "  Done."
cd ..
    
# cleanup StageIV NetCDF data
echo "Cleaning up old StageIV NetCDF data..."
cd /home/jpatton/RFC_StageIV_QPE_nc/temp/

# give files modification dates based on their filenames
for f in `find . -iname "*.nc"`; do
    touch -d "`date -d \"${f:2:4}-${f:6:2}-${f:8:2} ${f:10:2}:00 UTC\"`" $f
done

# remove files older than 25 days
find . -mtime +25 -exec rm {} \;
echo "  Done."

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging
