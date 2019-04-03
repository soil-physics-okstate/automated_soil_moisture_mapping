Ordinary Kriging Plots
----------------------

Make soil moisture plots for Oklahoma using Mesonet station VWC
measurements and ordinary kriging (and *not* including soil texture
or any other information).

These plots are useful for comparing to the regular soil moisture plots,
helping to illustrate the more detailed spatial patterns revealed by
incorporating soil texture.

Example:
```bash
bash ordinary_kriging_plots.sh 2016-03-09
```
Resulting plots will be found in the `output/maps/` subdirectory.

The supporting scripts in this directory are modified from others
in this repository.

* `create_outputs2.py` is modified from `create_outputs.py` in the `kriging` directory.
* `plot_soil_moisture_map.py` is modified from the version in the `plotting` directory.
* `krige_data.m` is modified from the version in the `kriging` directory.
* Other matlab scripts are modified from versions in the `validation_runs` directory.


