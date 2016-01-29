#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Usage: backfill_maps.sh <number of days>"
    exit 1
fi

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging
days=$1

# set path for Matlab
export PATH=$PATH:/usr/bin:/opt/MATLAB-R2015a/bin

for d in `seq 0 $days`; do

    # get date
    date=`date -d "-$d days" +"%Y-%m-%d"`
    echo "Mapping for $date (day ${d}/${days})..."
    
    # load data
    cd data_retrieval
    echo "  Getting Mesonet soil moisture data for ${date}..."
    python get_soil_moisture_data.py $date
    echo "  Getting StageIV antecedent precipitation data for ${date}..."
    python get_stageiv_api.py $date
    cd ..

    # do regression
    cd regression
    echo "  Building regression models for ${date}..."
    python do_regression.py $date
    cd ..

    echo "  Kriging, creating output, and plotting depths in parallel for ${date}..."
    parallel --gnu -P 3 "bash krige_plot_parallel.sh $date {1}" ::: 5 25 60

    echo "  Done."
	
done

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
find . -mtime 25 -exec rm {} \;
echo "  Done."

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging
