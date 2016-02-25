#!/bin/bash

# set directory paths
homedir=/home/OSU/jcpatto/automated_soil_moisture_mapping

# run backfill for only a single day
bash backfill_maps.sh 0 &> log/automated_map_`date +"%Y-%m-%d"`.log
