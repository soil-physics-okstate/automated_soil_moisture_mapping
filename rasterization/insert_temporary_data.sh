#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: insert_temporary_data.sh <date> <map_var> <depth>"
    exit 1
fi

# get commandline vars
date=$1
map_var=$2
depth=$3

# set database
dbname=soilmapnik
export PGUSER="postgres"
export PGPASSWORD="Ali292Ali292"

# set table
table=temp_soil_moisture_data_${map_var}_${depth}cm

# create table
psql -d $dbname -c "DROP TABLE ${table};"
psql -d $dbname -c "CREATE TABLE $table (id INTEGER PRIMARY KEY, value DOUBLE PRECISION);"

# get CSV filename
depth=`printf %02d $depth`
csv=${map_var}_${depth}cm_${date//-/}.csv

# insert data
cat ../output/kriging_result/$csv | psql -d $dbname -c "COPY $table FROM stdin CSV HEADER"
echo "insert_temporary_data.sh done"
