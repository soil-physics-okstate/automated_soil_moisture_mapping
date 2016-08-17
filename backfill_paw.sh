#!/usr/bin/env bash

cd /opt/mapnik/automated_soil_moisture_mapping

startDate=$1
endDate=$2

date=$startDate

while [ "`date -d \"$date\"`" != "`date -d \"$endDate\"`" ]; do

    echo $date

    cd derived_products
    echo Computing PAW
    python compute_paw.py $date
    cd ..

    cd plotting
    echo Plotting PAW
    python plot_paw_map.py $date 80
    cd ..

    date=`date -d "$date + 1 day" +"%Y-%m-%d"`

done

