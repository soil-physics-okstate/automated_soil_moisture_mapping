#!/usr/bin/env bash

depth=5

startDate=$1
endDate=$2

date=$startDate

while [ "`date -d \"$date\"`" != "`date -d \"$endDate\"`" ]; do
    
    datestr=`date -d "$date" +"%Y%m%d"`

    if [ -f output/kriging_prediction/resid/kriged_${depth}cm_${datestr}.csv ]; then
	date=`date -d "$date + 1 day" +"%Y-%m-%d"`
	continue
    fi

    if [ -f tmp/meso_soil_moisture_${depth}cm_${datestr}.csv ]; then
	echo $date
    fi

    date=`date -d "$date + 1 day" +"%Y-%m-%d"`

done

