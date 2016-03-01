#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: upload_soil_moisture_data_to_sql.sh <date> <map_var> <depth>"
    exit 1
fi

# get commandline vars
date=$1
map_var=$2
depth=$3

# set database
dbname=soilmapnik

# set table
table=temp_soil_moisture_data_${map_var}_${depth}cm

# set query
query="CREATE TABLE $table ( \
id INTEGER PRIMARY KEY, \
product_valid TIMESTAMP DEFAULT '$date', \
product_name VARCHAR(20) DEFAULT '$map_var', \
product_depth INTEGER DEFAULT $depth, \
product_value DOUBLE PRECISION \
);"

# create table
psql $dbname -c "DROP TABLE ${table};"
psql $dbname -c "$query"

# get CSV filename
depth=`printf %02d $depth`
csv=${map_var}_${depth}cm_${date//-/}.csv

# insert data
cat ../output/kriging_result/$csv | psql $dbname -c "COPY $table (id, product_value) FROM stdin CSV HEADER;"

# copy to soil_moisture_data
query="INSERT INTO soil_moisture_data (SELECT * FROM ${table}) \
ON CONFLICT ON CONSTRAINT soil_moisture_data_pkey \
DO UPDATE SET product_value = EXCLUDED.product_value;"
psql $dbname -c "$query"
