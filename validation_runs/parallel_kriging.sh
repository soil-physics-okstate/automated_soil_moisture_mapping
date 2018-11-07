#!/usr/bin/env bash

# get current directory
basedir=$(dirname "$(readlink -f "$0")")

# change into directory
cd $basedir

export PATH=$PATH:/usr/local/MATLAB/R2015a/bin/

matlab -nodesktop -r parallel_kriging

