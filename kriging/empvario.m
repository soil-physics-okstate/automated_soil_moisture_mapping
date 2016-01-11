function [d,V,N] = empvario(resid_data,depth)

% This function is designed for Oklahoma state-wide soil moisture map using
% data from Mesonet stations
%
% Input:
%       moisture_data = the output of the function deltat2vwc.m containing:
%           - MP = matric potential [kPa]
%           - vwc = volumetric water content [cm^3/cm^3]
%           - Se = relative saturation [dimensionless]
%           - K = hydraulic conductivity [cm/d]
%           - geoinfo = Location information for each active Oklahoma Mesonet
%       variable = 'MP', 'vwc', 'Se', 'K'
%       depth = one of the three depths of soil moisture data; 1, 2, or 3
%
% Output:
%       d = the mean distance of each lag distance class
%       V = the vector of semivariances corresponding to the lag distances
%       n = the number of elements in each bin
%       
%
% load volumetric water content for the designated depth

%if depth == 5 || 25 || 60
%    depth_str = num2str(depth);
    resids = resid_data.(strcat('resid_', depth));
%else
%    error('Wrong input values: The depth must be 5, 25, or 60.')
%end

% load the coordinates of all Mesonet stations
X = resid_data.x;
Y = resid_data.y;
%lat = cell2mat(moisture_data.geoinfo(:,3));
%lon = cell2mat(moisture_data.geoinfo(:,4));

% exclude the stations with missing data
resids = resids(~isnan(resids));
X = X(~isnan(resids));
Y = Y(~isnan(resids));

%lat = lat(~isnan(mois));
%lon = lon(~isnan(mois));

% convert the coordinates to northings and eastings
%[X,Y,~] = latlon2utm(lat,lon);

% generate bins of lag distance
[lagbins,N] = semivarlags(X,Y); 

% calculate the empirical variogram
[d,V,~] = vario([X,Y],resids,lagbins,'kron');