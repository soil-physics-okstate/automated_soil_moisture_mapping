function [krigResult] = krige_vwc_xval(map_date_str,depth)
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
  spt_path = '/home/OSU/jcpatto/geostats_toolbox/';
  addpath(genpath(spt_path));

  %% Step 1 - Load the grid to be kriged upon
  grid = load('locations/all_sites.mat');

  %% Step 2 - Load the residuals to be kriged
  % the date is read in as yyyy-mm-dd but files use yyyymmdd
  map_date_str = datestr(datenum(map_date_str), 'yyyymmdd');
  data_dir = 'tmp/';
  data = readtable(strcat(data_dir, 'meso_soil_moisture_', depth, 'cm_', map_date_str, '.csv'));
  data_type = 'vwc';

  %% Step 3: Create empirical semivariogram for three depths
  [d,V,N] = empvario(depth,data_type,data);

  %% Step 4: Fit theoretical semivariogram model
  [model,param] = semivarfit2(d,V,N);

  %% Step 5: Interpolate volumentric water content using kriging
  [vwc_xval]=kriging_xval(map_date_str,depth,data_type,grid,data,model,param);
  
  vwc = data.(strcat(data_type, '_', depth));
  vwc_i = ~isnan(vwc);
  vwc = vwc(vwc_i);
  stid = data.stid(vwc_i);

  dirOut = 'output/xval_ok/';
  fileName = strcat(dirOut, 'meso_xval_', depth, 'cm_', map_date_str, '.csv');
  fileOut = fopen(fileName, 'w');
  fprintf(fileOut, 'STID,vwc,vwc_ok\n');

  for i=1:length(vwc)
      fprintf(fileOut, '%s,%g,%g\n', stid{i}, vwc(i), vwc_xval(i));
  end
  fclose(fileOut);


end
