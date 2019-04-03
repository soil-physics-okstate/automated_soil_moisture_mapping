#!/usr/bin/env bash

# get current directory
basedir=$(dirname "$(readlink -f "$0")")

# check if date is set
if [[ $# -ne 1 ]]; then
    echo "Usage: ordinary_kriging_plots.sh <date>"
    echo "    <date> should be in yyyy-mm-dd format, e.g. 2016-03-09"
    exit 1
fi

date=$1

#
# Make files with measured VWC from Mesonet sites
#
# Create temp dir
T=$(mktemp -d)
dt2=${date//-/}  # ${date} with dashes removed

# Extract mesonet VWC data
echo "stid,vwc_5,vwc_25,vwc_60" > ${T}/smdata_${dt2}.tmp
awk -F, -vOFS=, 'FNR>3{print $1,$8,$9,$10}' ../dynamic_data/soil_moisture/06Z/sm_data_${dt2}.csv | sort >> ${T}/smdata_${dt2}.tmp

# Grab station coordinates
echo "stid,x,y" > ${T}/xy.tmp
awk -F, -vOFS=, 'FNR>1{print $1,$2,$3}' ../dynamic_data/regression/residual/resid_${dt2}.csv | sort >> ${T}/xy.tmp

# Combine the coordinates with the VWC data
join -t , ${T}/xy.tmp ${T}/smdata_${dt2}.tmp > ${T}/smdata_${dt2}.csv

# Create separate files for each depth (final files)
awk -F, -vOFS=, '{print $1,$2,$3,$4}' ${T}/smdata_${dt2}.csv > ./dynamic_data/soil_moisture/smdata_5cm_${dt2}.csv
awk -F, -vOFS=, '{print $1,$2,$3,$5}' ${T}/smdata_${dt2}.csv > ./dynamic_data/soil_moisture/smdata_25cm_${dt2}.csv
awk -F, -vOFS=, '{print $1,$2,$3,$6}' ${T}/smdata_${dt2}.csv > ./dynamic_data/soil_moisture/smdata_60cm_${dt2}.csv

# Delete the temp dir
rm -rf ${T}


source ../venv/bin/activate
PATH=$PATH:/usr/bin:/usr/local/MATLAB/R2015a/bin/
for depth in 5 25 60; do

    # Perform ordinary kriging using mesonet station vwc values
    # and produce files with x,y coordinates and predicted vwc values
    # covering the entire state
    matlab -nodisplay -nodesktop -singleCompThread -r "krige_data('$date', '$depth'); exit;"

    # Join the kriged values to the grid info and create output files 
    # with point IDs and vwc values
    python create_outputs2.py $date $depth

    # Create a map using the point IDs and vwc values
    python plot_soil_moisture_map.py $date $depth
done
deactivate

