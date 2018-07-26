#!/bin/bash

# set directory paths
homedir=/opt/soilmapnik/automated_soil_moisture_mapping
precipdir=../hourly_stageiv_precip_netcdf

# check if number of days are set
if [[ $# -ne 1 ]]; then
    echo "Usage: backfill_maps.sh <number of days>"
    exit 1
fi

# change into directory
cd $homedir

# activate virtual environment
source ./venv/bin/activate

# set path for Matlab
export PATH=$PATH:/usr/bin:/usr/local/MATLAB/R2015a/bin/

# set path for parallel
export PATH=$PATH:/opt/soilmapnik/local/bin

# get the number of days to loop over
days=$1

# set the variable
mapvar="vwc"

# array to collect months where we'll need to (re)build netCDF files
months=()

# loop over days
for d in `seq 0 $days`; do

    # get date
    date=`date -d "-$d days" +"%Y-%m-%d"`
    echo "--- `date --rfc-3339=seconds` ---"
    echo "Mapping for $date (day ${d}/${days})..."

    # add the month to the months array if it isn't already in there
    [[ ! ${months[@]} =~ ${date:0:7} ]] && months+=(${date:0:7})
    
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
    parallel --jobs 3 --timeout 5000 "bash krige_plot_parallel.sh $date {1}" ::: 5 25 60

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

# (re)write netcdf file for every month where at least one day was processed
cd netcdf_export
for month in ${months[@]}; do
    bash monthly_netcdf.sh ${month}
done
cd ..

echo "Optimizing soil_moisture_data table..."
echo `date`
psql soilmapnik -b -c "VACUUM ANALYZE soil_moisture_data;"
echo `date`
psql soilmapnik -b -c "REINDEX TABLE soil_moisture_data;"
echo `date`

echo "  Done."

cd $homedir
deactivate
