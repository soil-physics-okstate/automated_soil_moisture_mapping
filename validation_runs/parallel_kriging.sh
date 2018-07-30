#!/usr/bin/env bash

cd /home/OSU/jcpatto/automated_soil_moisture_mapping/validation_runs/

export PATH=$PATH:/usr/local/MATLAB/R2015a/bin/

matlab -nodesktop -r parallel_kriging

