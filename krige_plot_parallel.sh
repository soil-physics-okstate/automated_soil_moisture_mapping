# Command-line arguments:
#  1. Date string (yyyy-mm-dd)
#  2. Depth
date=$1
depth=$2
mapvar=vwc

# do kriging
cd kriging

matlab -nodisplay -nodesktop -r "krige_data('$date', '$depth'); exit;" &> log/kriging_${date}_${depth}cm.log

# create output CSV
python create_outputs.py $date $depth &> log/outputting_${date}_${depth}cm.log

cd ..

# do plotting
cd plotting
python plot_soil_moisture_map.py $date $depth &> log/plotting_${date}_${depth}cm.log

cd ..

# upload data to database
cd database_scripts
python upload_soil_moisture_data_to_sql.py $date $depth &> log/db_upload_${date}_${depth}cm.log

# create geotiffs
bash create_geotiff.sh $date $mapvar $depth &> log/create_geotiff_${date}_${depth}cm.log

cd ..
