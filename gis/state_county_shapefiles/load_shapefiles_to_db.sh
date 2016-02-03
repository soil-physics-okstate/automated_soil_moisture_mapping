#!/bin/bash

export PGCLIENTENCODING=LATIN1

for shapefile in tl_*; do
    ogr2ogr -overwrite -f PostgreSQL PG:"dbname=soilmapnik" $shapefile/$shapefile.shp -nlt MULTIPOLYGON
done
