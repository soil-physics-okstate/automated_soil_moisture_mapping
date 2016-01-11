function [krigResult]=smmkriging(grid,map_date_str,resid_data,depth,model,param)
% smmkriging.m          
%
% This function imports data from functions created by Andres and Geano and
% then calls upon the kriging function from the Geostats library. It was 
% created for the Statewide Soil Moisture Mapping project.
% 
% Author: Matthew Haffner 7/3/2015
%
%%%%% Contents %%%%%
% 1. Get Mesonet station information
% 2. Import grid
% 3. Convert from lat-lon to x-y
% 4. Supply kriging inputs
% 5. Kriging
% 6. Cross Validation
% 7. Export data
%
%%%%% Inputs %%%%%
% moisture_data = structure containing daily soil information from the
%   Mesonet 
% variable = nx3 cell; 'MP', 'vwc', 'Se', or 'K'
% depth = 1, 2, or 3; column number in 'MP', 'vwc', 'Se', 'K' indicating
%   depth
% model = variogram model selected in semivarfit2.m
% param = parameters calculated in semivarfit2.m
%
%%%%% Outputs %%%%%
% krigResult = nx4 double with kriging results;
%     col1 = predicted values using kriging
%     col2 = kriging variances
%     col3 = x coordinates (CEA)
%     col4 = y coordinates (CEA)
% 'daily_SMM_kriging.csv' (with appropriate depth inserted before file
%   extension; 1, 2, or 2)

%disp(sprintf('Interpolating values for %s at depth %d',variable,depth)) % Display current iteration 
warning('off','all'); % Suppress warnings; warnings from matrices being singular or badly scaled severely slows down the calculations

%% 1. Get Mesonet station information
%mesLat = cell2mat(moisture_data.geoinfo(:,3)); % Latitude of Mesonet stations
%mesLon = cell2mat(moisture_data.geoinfo(:,4)); % Longitude of Mesonet stations
%zVar = moisture_data.(variable)(:,depth); % Z Variable

%mesInfo = [mesLat mesLon zVar];                 % Extract needed variables for Mesonet stations
%mesInfo = mesInfo(~any(isnan(mesInfo),2),:);    % Remove NaNs (missing soil moisture measurements)

%mesLat = mesInfo(:,1);                          % Extract latitiude        
%mesLon = mesInfo(:,2);                          % Extract longitude
%zVar = mesInfo(:,3);                            % Extract volumetric water content
%depths = [5 25 60];
%depth_str = num2str(depths(depth), '%02d');

%depth = num2str(depth);
zVar = resid_data.(strcat('resid_', depth));

mesX = resid_data.x;
mesY = resid_data.y;

% remove missing data
zVar = zVar(~isnan(zVar));
mesX = mesX(~isnan(zVar));
mesY = mesY(~isnan(zVar));

%% 2. Import grid
%grid = readtable('ok_cea_grid.csv');            % Grid for estimated points
gridX = grid.x;                                 % Extract x
gridY = grid.y;                                 % Extract y

%% 3. Convert from lat-lon to x-y
%[mesX, mesY] = latlon2cea(mesLat,mesLon);      % Convert lat-lon to x-y (CEA)
%mesX = resid_data.x;
%mesY = resid_data.y;

%% 4. Supply kriging inputs
obs = [mesX mesY zVar];         % Mesonet x coordinates, Mesonet y coordinates, soil moisture variable
pred = [gridX gridY];           % Grid x-y coordinates
beta = cell2mat(param(2));      % Variogram parameters (from Geano); may need to convert to 2x1 array
maxpoints = 10;                  % Maximum number of observed locations to consider; Will this be consistent everday?
maxdist = 200000;               % Maximum distance (m) between an unsampled location and an observed station; Will this be consistent everyday?
Gmodel = model;                 % Make notation conistent with krig.m function
Kmodel = 'ordinary';            % Kriging method; 'ordinary' is default
nugget = 0.0000;                 % Nugget not currently in use due to poor results

%% 5. Kriging

% Check memory to see if kriging needs to be run in parts, then run kriging
if checkmemory(pred) == 0
    [Zpred,Vpred,x,y]=krig_in_parts(obs,pred,beta,maxpoints,maxdist,Gmodel,Kmodel,nugget); % If you have insufficient memory, run the function in parts
else
    [Zpred,Vpred,x,y]=krig(obs,pred,beta,maxpoints,maxdist,Gmodel,Kmodel,nugget); % Run kriging like normal if enough memory is available
end
   
krigResult = [x y Zpred Vpred];
%% 6. Cross validation

% Leave one out cross validation; produces RMSE
[RMSE,RMSEn,RMSEz]=crossvalidation(obs,beta,maxpoints,maxdist,Gmodel,Kmodel,nugget); 
dirOut = '../outputs/cross_validation/';
fileName = strcat(dirOut,'oksmm_rmse_',depth,'cm_',map_date_str,'.csv');
fileOut = fopen(fileName, 'w');
fprintf(fileOut, '%g', RMSE);
fclose(fileOut);

%% 7. Export data 

%Export results of kriging with x-y coordinates of estimated points for plotting
%If you get an error here, make sure your current working directory is kriging/
dirOut = '../data/kriging_residuals/';                        % Directory to store data
%formatOut = 'yyyymmdd';                         % Date format
fileName = strcat(dirOut,'daily_OKSMM_kriging_',depth,'cm_',map_date_str,'.csv'); % Create variable with .csv file name

columnHeaders = {'x', 'y', 'Z', 'Zvar'}; % Specify column headers

fileOut = fopen(fileName, 'w');                 % Open file
fprintf(fileOut, '%s,', columnHeaders{1:end-1});% Append file with column headers
fprintf(fileOut, '%s\n', columnHeaders{end});   % Line break at end of last header
fclose(fileOut);

dlmwrite(fileName, krigResult, 'precision', '%g', '-append');

% Save RMSE results

%temp_data_dir = 'temp_data/';
%if exist(strcat(temp_data_dir,'kriging_RMSE_',map_date_str,'.mat')) % Load the existing structure to keep from creating a new structure each time
%    load(strcat(temp_data_dir,'kriging_RMSE_',map_date_str,'.mat')) % Load the structure if it exists; otherwise, create it
%end
%kriging_RMSE.(variable).(sprintf('depth%d',depth)) = RMSEn; % Record RMSE in structure
%save(strcat(temp_data_dir, 'kriging_RMSE_', map_date_str, '.mat'), 'kriging_RMSE'); % Save as a .mat for future reference

% Save RMSEn results (Normalized root mean squared error)
%temp_data_dir = 'temp_data/';
%if exist(strcat(temp_data_dir,'kriging_RMSEn_',map_date_str,'.mat')) % Load the existing structure to keep from creating a new structure each time
%    load(strcat(temp_data_dir,'kriging_RMSEn_',map_date_str,'.mat')) % Load the structure if it exists; otherwise, create it
%end
%kriging_RMSEn.(variable).(sprintf('depth%d',depth)) = RMSEn; % Record the normalized RMSE (called RMSEn here) in structure
%save(strcat(temp_data_dir, 'kriging_RMSEn_', map_date_str, '.mat'), 'kriging_RMSEn'); % Save as a .mat for future reference

end