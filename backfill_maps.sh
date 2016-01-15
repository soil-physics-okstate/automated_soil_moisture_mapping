#!/bin/bash

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging
days=3

for d in `seq 1 $days`; do

    # get date
    date=`date -d "-$d days" +"%Y-%m-%d"`
    echo "Mapping for $date (day ${d}/${days})..."
    
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
	
done

# cleanup StageIV NetCDF data
echo Cleaning up old StageIV NetCDF data...
cd /home/jpatton/RFC_StageIV_QPE_nc/temp/

# give files modification dates based on their filenames
for f in `find . -iname "*.nc"`; do
    touch -d "`date -d \"${f:2:4}-${f:6:2}-${f:8:2} ${f:10:2}:00 UTC\"`" $f
done

# remove files older than 25 days
find . -mtime 25 -exec rm {} \;
echo "  Done."

cd /home/jpatton/Dropbox_OSU_Soil_Physics/Patton/Projects/Soil_Moisture_Mapping_Regression_Kriging
