# check command-line aguments
if [[ $# -ne 2 ]]; then
    echo "Usage: krige_plot_parallel.sh <date [yyyy-mm-dd]> <depth [cm]>"
    exit 1
fi

# get command-line arguments:
#  1. Date string (yyyy-mm-dd)
#  2. Depth
#  (3. Soil Moisture variable in future)
date=$1
depth=$2
mapvar="vwc"

# do kriging and create CSV
cd kriging
matlab -nodisplay -nodesktop -r "krige_data('$date', '$depth'); exit;" &> log/kriging_${date}_${depth}cm.log
python create_outputs.py $date $depth &> log/outputting_${date}_${depth}cm.log

cd ..

# do plotting
cd plotting
python plot_soil_moisture_map.py $date $depth &> log/plotting_${date}_${depth}cm.log
python plot_api_map.py $date $depth &>> log/plotting_${date}_${depth}cm.log
python plot_kriging_residuals_map.py $date $depth &>> log/plotting_${date}_${depth}cm.log
python plot_regression_stats.py $date $depth &>> log/plotting_${date}_${depth}cm.log

cd ..

# create geotiff rasters
cd rasterization
bash rasterize_map.sh $date $mapvar $depth &> log/rasterize_${date}_${depth}cm.log

cd ..
