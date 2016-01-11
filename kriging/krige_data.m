function [krigResult] = krige_data(map_date_str,depth)
%% Oklahoma Soil Moisture Mapping 
% This script compiles the functions and scripts to generate state wide
% soil moisture maps in Oklahoma based on the Oklahoma Mesonet.
% 
% Steps for map generation
%
% Step 0: Locate the Soil Physics Toolbox
%
% -- get_data.m --
%
% Step 1: Load daily average temperature differential (deltaT) from the
%         Oklahoma Mesonet internal website.
%
% Step 2: Convert temperature differential into matric potential, and 
%         subsequently into volumetric water content, relative saturation, 
%         and hydraulic conductivity.
%
% -- krige_data.m --
%
% Step 3: Create empirical semivariogram
%
% Step 4: Fit theoretical semivariogram model
%
% Step 5: Interpolate volumentric water content using kriging
%
% Step 6: Plot
%

%% STEP 0 - Set path to Soil Physics Toolbox
spt_path = '../../../../Soil Physics Toolbox';
addpath(genpath(spt_path));

%% Step 1 - Load the grid to be kriged upon
grid_data_file = '../data/grid/grid.csv';
grid = readtable(grid_data_file);

%% Step 2 - Load the residuals to be kriged
% the date is read in as yyyy-mm-dd but files use yyyymmdd
map_date_str = datestr(datenum(map_date_str), 'yyyymmdd');
resid_data_dir = '../data/regression_residuals/';
resid_data = readtable(strcat(resid_data_dir, 'resid_', map_date_str, '.csv'));

%% Step 3: Create empirical semivariogram for three depths
[d,V,N] = empvario(resid_data,depth);

%% Step 4: Fit theoretical semivariogram model
[model,param] = semivarfit2(d,V,N,map_date_str,depth); 

%% Step 5: Interpolate volumentric water content using kriging
[krigResult]=smmkriging(grid,map_date_str,resid_data,depth,model,param);

end