#!/usr/bin/env bash

# get current directory
basedir=$(dirname "$(readlink -f "$0")")

# change into directory
cd $basedir

export PATH=$PATH:/usr/local/MATLAB/R2015a/bin/

#matlab -nodesktop -r parallel_xval

source ../venv/bin/activate

#depth=5
#depth=25
depth=60

export PATH=$PATH:$HOME/local/bin/

parallel python barnes_xval.py {} $depth :::: dates
parallel python create_outputs_xval.py {} $depth :::: dates
