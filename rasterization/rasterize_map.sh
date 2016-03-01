#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: rasterize_map.sh <date> <map_var> <depth>"
    exit 1
fi

# get commandline vars
date=$1
map_var=$2
depth=$3

# set database
dbname=soilmapnik

# create temporary data table
bash insert_temporary_data.sh $date $map_var $depth

# get data table
datatable=temp_soil_moisture_data_${map_var}_${depth}cm

# set output file
outfile=../output/raster_maps/raster_${date}_${map_var}_${depth}cm.tif

# build query
query="SELECT geom_point AS geom, value \
FROM soil_moisture_grid_opt AS g INNER JOIN $datatable AS d ON (g.id = d.id)"

# basename for temp files
tmpbase=temp_${depth}cm_${map_var}
rm $tmpbase.*

# make shapefile
ogr2ogr -f "ESRI Shapefile" $tmpbase.shp PG:"dbname=$dbname" -sql "$query"

# make raster
gdal_rasterize -a value -tr 800 800 -a_nodata -999 -ot Float32 $tmpbase.shp $tmpbase.tif

# reproject raster
rm $outfile
proj4="+proj=cea +a=6378137 +b=6378137 +lon_0=-97.674 +lat_ts=35.3 \
+x_0=100.000000002310 +y_0=-4563147.606432600878 +units=m +no_defs"
gdalwarp -s_srs "$proj4" -t_srs "EPSG:3857" $tmpbase.tif $outfile
