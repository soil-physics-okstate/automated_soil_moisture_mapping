function [d,V,N] = empvario(depth,data_type,data);

% This function is designed for Oklahoma state-wide soil moisture map using
% data from Mesonet stations
%
% Input:
%       map_date_str = date [yyyymmdd]
%       resid_data = residual data after regression
%       depth = the depth of the soil moisture measurement [cm]
%
% Output:
%       d = the mean distance of each lag distance class
%       V = the vector of semivariances corresponding to the lag distances
%       n = the number of elements in each bin
%

  % load volumetric water content for the designated depth
  Z = data.(strcat(data_type, '_', depth));
  Z_exists = ~isnan(Z);

  % load the coordinates of all Mesonet stations
  X = data.x;
  Y = data.y;

  % exclude the stations with missing data
  Z = Z(Z_exists);
  X = X(Z_exists);
  Y = Y(Z_exists);

  % generate bins of lag distance
  [lagbins,N] = semivarlags(X,Y);

  % calculate the empirical variogram
  [d,V,~] = vario([X,Y],Z,lagbins,'kron');

end
