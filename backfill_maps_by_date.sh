#!/bin/bash

# set directory paths
homedir=/home/OSU/jcpatto/automated_soil_moisture_mapping
precipdir=../hourly_stageiv_precip_netcdf

# check if number of days are set
if [[ $# -ne 2 ]]; then
    echo "Usage: backfill_maps_by_date.sh <end date> <days>"
    exit 1
fi

# change into directory
cd $homedir

# activate virtual environment
source ./venv/bin/activate

# set path for Matlab
export PATH=$PATH:/usr/bin:/usr/local/MATLAB/R2015a/bin/

# set path for parallel
export PATH=$PATH:$HOME/local/bin

# get the number of days to loop over
endDay=$1
days=$2

# set the variable
mapvar="vwc"

# loop over days
for d in `seq 0 $days`; do

    # get date
    date=`date -d "$endDay - $d days" +"%Y-%m-%d"`
    echo "--- `date --rfc-3339=seconds` ---"
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
    parallel --jobs 3 --delay 10 --timeout 3600 "bash krige_plot_parallel.sh $date {1}" ::: 5 25 60

    echo "  Uploading data to soil_moisture_data_table"
    cd database_scripts
    for depth in 5 25 60; do
	bash upload_soil_moisture_data_to_sql.sh $date $mapvar $depth
    done
    cd ..

    if [ $(($d % 5)) -eq 4 ]; then
	echo "  Optimizing soil_moisture_data table..."
	psql soilmapnik -b -c "VACUUM ANALYZE soil_moisture_data;"
    fi

    echo "  Done."

done

echo "Optimizing soil_moisture_data table..."
psql soilmapnik -b -c "VACUUM ANALYZE soil_moisture_data;"
psql soilmapnik -b -c "REINDEX TABLE soil_moisture_data;"

# copy maps to servers
#cd server_functions
#echo "Copying maps to server..."
#bash copy_map_to_server.sh
#echo "  Done."
#cd ..

# cleanup StageIV NetCDF data
echo "Cleaning up old StageIV NetCDF data..."
cd $precipdir

# give files modification dates based on their filenames
for f in `find . -iname "*.nc"`; do
    touch -d "`date -d \"${f:2:4}-${f:6:2}-${f:8:2} ${f:10:2}:00 UTC\"`" $f
done

# remove files older than 25 days
#find . -mtime 25 -exec rm {} \;
echo "  Done."

cd $homedir
deactivate