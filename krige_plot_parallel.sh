# Command-line arguments:
#  1. Date string (yyyy-mm-dd)
#  2. Depth
date=$1
depth=$2

# do kriging
cd kriging
matlab -nodisplay -nosplash -nodesktop -r "krige_data('$date', '$depth'); exit;" > log/kriging_${date}_${depth}cm.log

# create output CSV
python create_outputs.py $date $depth > log/outputting_${date}_${depth}cm.log

cd ..

# do plotting
cd plotting
python oksmm_mapping.py $date $depth > log/plotting_${date}_${depth}cm.log

cd ..
