#!/bin/bash

/usr/bin/rsync -ave ssh ../outputs/maps/*.png soilmoisture@soilmoisture.okstate.edu:~/soilmoisture.okstate.edu/maps/
