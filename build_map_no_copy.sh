#!/bin/bash

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging

# set path for Matlab
export PATH=$PATH:/usr/bin:/opt/MATLAB-R2015a/bin

# get date
date=`date +"%Y-%m-%d"`
echo "Mapping for ${date}..."

# load data
cd data_retrieval
python get_soil_moisture_data.py $date
python get_stageiv_api.py $date

cd ..

# do regression
cd regression
python do_regression.py $date

cd ..

for depth in 5 25 60; do
    
    # do kriging
    cd kriging
    matlab -nodisplay -nosplash -nodesktop -r "krige_data('$date', '$depth'); exit;"

    # create output CSV
    python create_outputs.py $date $depth
    
    cd ..

    # do plotting
    cd plotting
    python oksmm_mapping.py $date $depth

    cd ..

done
