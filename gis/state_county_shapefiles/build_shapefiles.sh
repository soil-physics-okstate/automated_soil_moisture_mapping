#!/bin/bash

# download US counties shapefile
wget http://www2.census.gov/geo/tiger/TIGER2014/COUNTY/tl_2014_us_county.zip -O tl_2014_us_county.zip

# unzip
unzip -u tl_2014_us_county.zip -d tl_2014_us_county
rm tl_2014_us_county.zip

# extract Oklahoma counties into their own shapefile
input=tl_2014_us_county
output=tl_2014_oklahoma_county
mkdir -p $output
ogr2ogr -overwrite -where 'STATEFP = "40"' $output/$output.shp $input/$input.shp

# dissolve Oklahoma counties into a state shapefile
input=tl_2014_oklahoma_county
output=tl_2014_oklahoma_state
mkdir -p $output
ogr2ogr -overwrite $output/$output.shp $input/$input.shp -dialect sqlite -sql "SELECT ST_Union(geometry,geometry), STATEFP FROM $input GROUP BY STATEFP"
