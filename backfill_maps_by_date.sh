#!/usr/bin/env bash

# get current directory
basedir=$(dirname "$(readlink -f "$0")")

# set path for Matlab
export PATH=$PATH:/usr/bin:/usr/local/MATLAB/R2015a/bin/

# set path for GNU parallel
export PATH=$PATH:$HOME/local/bin

# check if number of days are set
if [[ $# -ne 2 ]]; then
    echo "Usage: backfill_maps_by_date.sh <end date> <days>"
    exit 1
fi

# get the number of days to loop over
endDay=$1
days=$2

# set soil moisture variables (may be set on commandline in future)
mapvar="vwc"
depths="5 25 60"

# change into directory
cd $basedir

# activate virtual environment
source ./venv/bin/activate

# loop over days
for d in `seq 0 $days`; do

    # get date
    date=`date -d "$endDay - $d days" +"%Y-%m-%d"`
    echo "--- `date --rfc-3339=seconds` ---"
    echo "Mapping for $date (day ${d}/${days})..."
    
    # get data
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

    # do kriging and plotting
    echo "  Kriging, creating output, and plotting depths in parallel for ${date}..."
    parallel --jobs 3 --delay 15 --timeout 3600 "bash krige_plot_parallel.sh $date {1}" ::: $depths

    # upload data to postgres
    echo "  Uploading data to soil_moisture_data_table"
    cd database_scripts
    for depth in $depths; do
	bash upload_soil_moisture_data_to_sql.sh $date $mapvar $depth
    done
    cd ..

    # after every 5th iteration, "optimize" the data table
    if [ $(($d % 5)) -eq 4 ]; then
	echo "  Optimizing soil_moisture_data table..."
	psql soilmapnik -b -c "VACUUM ANALYZE soil_moisture_data;"
    fi

    echo "  Done."

done

# "optimize" the data table
echo "Optimizing soil_moisture_data table..."
psql soilmapnik -b -c "VACUUM ANALYZE soil_moisture_data;"
psql soilmapnik -b -c "REINDEX TABLE soil_moisture_data;"

echo "  Done."

# cleanup
cd $basedir
deactivate
