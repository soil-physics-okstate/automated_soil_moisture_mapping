#!/bin/bash

# set dbname
dbname="soilmapnik"

# download the gSSURGO dataset, then change this filename
fname="soils_GSSURGO_ok_2939077_01.zip"

# unzip
unzip -u $fname -d gSSURGO
unzip -u gSSURGO/soils/gssurgo_g_ok.zip

# load mupolygons, component, and chorizon sets
ogr2ogr -overwrite -f PostgreSQL PG:"dbname=${dbname}" gSSURGO_OK.gdb mupolygon
ogr2ogr -overwrite -f PostgreSQL PG:"dbname=${dbname}" gSSURGO_OK.gdb component
ogr2ogr -overwrite -f PostgreSQL PG:"dbname=${dbname}" gSSURGO_OK.gdb chorizon

# cleanup
rm -rf gSSURGO
