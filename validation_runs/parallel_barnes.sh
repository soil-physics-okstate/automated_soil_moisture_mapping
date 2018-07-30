#!/usr/bin/env bash

depth=5

export PATH=$PATH:$HOME/local/bin/

parallel python barnes.py {} $depth :::: dates
