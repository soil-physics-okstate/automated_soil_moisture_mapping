#!/usr/bin/env bash

depth=5
minstns=80

# get current directory
basedir=$(dirname "$(readlink -f "$0")")

# change into directory
cd $basedir

export PATH=$PATH:/usr/local/MATLAB/R2015a/bin/

startDate=$1
endDate=$2

date=$startDate

while [ "`date -d \"$date\"`" != "`date -d \"$endDate\"`" ]; do

    echo ""
    echo "----"
    echo `date`
    echo $date

    echo '  creating input..'
    python create_temp_soil_moisture_input.py $date $depth
    
    datestr=`date -d "$date" +"%Y%m%d"`
    numstns=`cut -d',' -f4 tmp/meso_soil_moisture_${depth}cm_${datestr}.csv | sort | uniq | wc -l`

    if [ "$numstns" -lt "$minstns" ]; then
	echo '  not enough stations..'
	rm tmp/meso_soil_moisture_${depth}cm_${datestr}.csv
	date=`date -d "$date + 1 day" +"%Y-%m-%d"`
	continue
    fi

    #echo '  running barnes..'
    #python barnes.py $date $depth

    #echo '  running kriging..'
    #matlab -nodesktop -r "krige_resid('$date', '$depth'); krige_vwc('$date', '$depth'); exit"

    date=`date -d "$date + 1 day" +"%Y-%m-%d"`

done

