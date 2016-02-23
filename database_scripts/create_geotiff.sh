#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: create_geotiff.sh <date> <map_var> <depth>"
    exit 1
fi

date=$1
map_var=$2
depth=$3

temp_query_file=temp_query/burn_raster_${date}_${map_var}_${depth}cm.sql
output_raster_file=../output/raster_maps/raster_${date}_${map_var}_${depth}cm.tif

sed s/xxDATExx/${date}/ burn_raster_template.sql | \
    sed s/xxVARxx/${map_var}/ | \
    sed s/xxDEPTHxx/${depth}/ \
    > $temp_query_file

dbname='soilmapnik'
table='soil_moisture_data_raster_temp'

psql $dbname -f $temp_query_file

gdal_translate \
    -ot Float32 \
    -strict \
    -a_srs "EPSG:3857" \
    PG:"dbname=$dbname table=$table" \
    $output_raster_file
