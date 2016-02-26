function [d,V,N] = empvario(resid_data,depth)

% This function is designed for Oklahoma state-wide soil moisture map using
% data from Mesonet stations
%
% Input:
%       resid_data = residual data after regression
%       depth = the depth of the soil moisture measurement [cm]
%
% Output:
%       d = the mean distance of each lag distance class
%       V = the vector of semivariances corresponding to the lag distances
%       n = the number of elements in each bin
%       

  % load volumetric water content for the designated depth
  resids = resid_data.(strcat('resid_', depth));
  resids_exists = ~isnan(resids);

  % load the coordinates of all Mesonet stations
  X = resid_data.x;
  Y = resid_data.y;

  % exclude the stations with missing data
  resids = resids(resids_exists);
  X = X(resids_exists);
  Y = Y(resids_exists);

  % generate bins of lag distance
  [lagbins,N] = semivarlags(X,Y); 

  % calculate the empirical variogram
  [d,V,~] = vario([X,Y],resids,lagbins,'kron');

end
