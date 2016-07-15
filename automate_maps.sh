#!/bin/bash

# set directory paths
homedir=/opt/soilmapnik/automated_soil_moisture_mapping
cd $homedir

# run backfill for only a single day
bash backfill_maps.sh 0 &> log/automated_map_`date +"%Y-%m-%d"`.log
