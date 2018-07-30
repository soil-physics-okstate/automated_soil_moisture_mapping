#!/usr/bin/env bash

cd /home/OSU/jcpatto/automated_soil_moisture_mapping/validation_runs/

export PATH=$PATH:/usr/local/MATLAB/R2015a/bin/

#matlab -nodesktop -r parallel_xval

source ../venv/bin/activate

depth=5

export PATH=$PATH:$HOME/local/bin/

#parallel python barnes_xval.py {} $depth :::: dates
parallel python create_outputs_xval.py {} $depth :::: dates
