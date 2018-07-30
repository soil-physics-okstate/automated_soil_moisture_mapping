function [model,param]=semivarfit2(d,V,N);

% SEMIVARFIT2 fits and compares variogram models to empirical variograms
% Inputs
%       d is the mean distance of each lag distance class
%       V is the vector of semivariances corresponding to the lag distances
%       N is the number of elements in each bin
%
% Outputs
%       model is a string of the chosen model
%       param is the corresponding parameters for the chosen model, which
%             is in the form of {nugget, [sill range]}. If there are only
%             two elements in param, they are {[sill range]}.
%
% This function is adapted from semivarfit.m created by Andres Patrignani
% Modified by Jingnuo Dong 7/4/2015

  modelnamesgeo = {'spherV','gaussV','exponV'};
  modelnames = {'Spherical','Gaussian','Exponential'};
  modellist = {'sphericalV','gaussianV','exponentialV'};

  % initial guess values for the parameters
  param0 = {0, [mean(V) d(1)]}; % {nugget, [sill range]}
  paramlist = cell(length(modellist),1);
  MSE = nan(length(modellist),1);
  for i=1:length(modellist)
    model = {'nuggetV',modellist{i}};
    [paramlist{i},~]=modelfit(d,V,N,model,param0);
    MSE(i) = mean((feval(modellist{i},d,paramlist{i}{2})-V).^2);
  end

  [~,model_idx] = min(MSE);
  param = paramlist{model_idx};
  model = modelnamesgeo{model_idx};

end
