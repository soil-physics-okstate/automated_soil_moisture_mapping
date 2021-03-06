function [krigResult]=smmkriging(grid,map_date_str,resid_data,depth,model,param)
% smmkriging.m          
%
% This function imports data from functions created by Andres and Geano and
% then calls upon the kriging function from the Geostats library. It was 
% created for the Statewide Soil Moisture Mapping project.
% 
% Author: Matthew Haffner 7/3/2015
% Updated: Jason Patton 2/10/2016
% Updated: Tyson Ochsner 3/6/2020, modified to accommodate semivarfit3.m
%
%%%%% Contents %%%%%
% 1. Set up input for kriging
% 2. Kriging
% 3. Cross Validation
% 4. Export data
%
%%%%% Inputs %%%%%
% grid = structure containing the x/y grid to krige on
% map_date_str = the date string for the current map
% resid_data = structure containing the data to krige
% depth = string for the soil depth [cm] being kriged (5, 25, or 60)
% model = variogram model selected in semivarfit3.m
% param = parameters calculated in semivarfit3.m
%
%%%%% Outputs %%%%%
% krigResult = nx4 double with kriging results;
%     col1 = predicted values using kriging
%     col2 = kriging variances
%     col3 = x coordinates
%     col4 = y coordinates
% 'daily_SMM_kriging.csv' (with appropriate depth inserted before file
%   extension; 1, 2, or 2)

  warning('off','all'); % Suppress warnings; warnings from matrices being singular or badly scaled severely slows down the calculations

  %% 1. Set up inputs for kriging

  % get data
  zVar = resid_data.(strcat('resid_', depth));
  zVar_exists = ~isnan(zVar);
  mesX = resid_data.x;
  mesY = resid_data.y;

  % remove missing data
  zVar = zVar(zVar_exists);
  mesX = mesX(zVar_exists);
  mesY = mesY(zVar_exists);
  obs = [mesX mesY zVar]; % Mesonet x coordinates, Mesonet y coordinates, soil moisture variable

  % get grid
  gridX = double(grid.x);
  gridY = double(grid.y);
  pred = [gridX gridY]; % Grid x-y coordinates

  % set kriging parametes    
  beta = param; % Variogram parameters (from semivarfit3.m); 
  maxpoints = 10; % Maximum number of observed locations to consider
  maxdist = 200000; % Maximum distance [m] between an unsampled location and an observed station
  Gmodel = model; % Variogram model, make notation conistent with krig.m function
  Kmodel = 'ordinary'; % Kriging method; 'ordinary' is default

  %% 2. Kriging

  [Zpred,Vpred,x,y]=krig_in_parts(obs,pred,beta,maxpoints,maxdist,Gmodel,Kmodel);
  krigResult = [x y Zpred Vpred];

  %% 3. Cross validation

  % Leave one out cross validation; produces RMSE
  [RMSE,RMSEn,RMSEz]=crossvalidation(obs,beta,maxpoints,maxdist,Gmodel,Kmodel); 
  dirOut = '../output/kriging_cross_validation/';
  fileName = strcat(dirOut,'rmse_',depth,'cm_',map_date_str,'.csv');
  fileOut = fopen(fileName, 'w');
  fprintf(fileOut, '%g', RMSE);
  fclose(fileOut);

  %% 4. Export data 

  dirOut = '../output/kriging_residual/';
  fileName = strcat(dirOut,'kriged_',depth,'cm_',map_date_str,'.csv');

  columnHeaders = {'x', 'y', 'Z', 'Zvar'}; % Specify column headers

  % Write the header
  fileOut = fopen(fileName, 'w');                 % Open file
  fprintf(fileOut, '%s,', columnHeaders{1:end-1});% Append file with column headers
  fprintf(fileOut, '%s\n', columnHeaders{end});   % Line break at end of last header
  fclose(fileOut);

  % Write the rest of the data
  dlmwrite(fileName, krigResult, 'precision', '%g', '-append');

end
