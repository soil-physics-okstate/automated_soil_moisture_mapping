function [krigResult] = krige_data(map_date_str,depth)
%% Oklahoma Soil Moisture Mapping 
% This script compiles the functions and scripts to generate state wide
% soil moisture maps in Oklahoma based on the Oklahoma Mesonet.
% 
% Steps for map generation
%
% Step 0: Locate the Soil Physics Toolbox
%
% Step 1: Load the grid
%
% Step 2: Load the Mesonet data
%
% Step 3: Create empirical semivariogram
%
% Step 4: Fit theoretical semivariogram model
%
% Step 5: Interpolate using kriging


  %% STEP 0 - Set path to Geostats Toolbox
  spt_path = '/home/OSU/jpatto/geostats_toolbox';
  addpath(genpath(spt_path));

  %% Step 1 - Load the grid to be kriged upon
  grid = load('../static_data/grid/soil_moisture_grid.mat');

  %% Step 2 - Load the residuals to be kriged
  % the date is read in as yyyy-mm-dd but files use yyyymmdd
  map_date_str = datestr(datenum(map_date_str), 'yyyymmdd');
  resid_data_dir = '../dynamic_data/regression/residual/';
  resid_data = readtable(strcat(resid_data_dir, 'resid_', map_date_str, '.csv'));

  %% Step 3: Create empirical semivariogram for three depths
  [d,V,N] = empvario(resid_data,depth);

  %% Step 4: Fit theoretical semivariogram model
  [model,param] = semivarfit2(d,V,N,map_date_str,depth); 

  %% Step 5: Interpolate volumentric water content using kriging
  [krigResult]=smmkriging(grid,map_date_str,resid_data,depth,model,param);

end
