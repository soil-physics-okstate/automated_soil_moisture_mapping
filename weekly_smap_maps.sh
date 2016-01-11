#!/bin/bash

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging

#date0="2015-04-03"
date0="2015-06-14"

step="8 days"
date=$date0
depth=5

while [ `date -d "$date" +"%Y"` -lt 2016 ]; do

    echo "Mapping for $date ..."
    
    # load data
    cd data_retrieval
    python get_soil_moisture_data.py $date
    python get_stageiv_precip_alt_storage.py $date
    cd ..

    # do regression
    cd regression
    python do_regression.py $date
    cd ..

    # do kriging and create output CSVs
    cd kriging
    matlab -nodisplay -nosplash -nodesktop -r "krige_data('$date', '$depth'); exit;"
    python create_outputs.py $date $depth
    cd ..

    # output SMAP data
    cd smap_conversion
    python get_mean_soil_moisture_per_pixel.py $date
    cd ..

    # cleanup old data
    rm /home/jpatton/RFC_StageIV_QPE_nc/temp/`date -d "$date - 2 months" +"%Y%m"`*.nc 2> /dev/null
    
    # increment date
    date=`date -d "$date + $step" +"%Y-%m-%d"`
    
done
