%depth = '5';
%depth = '25';
depth = '60';
dates = textread('dates', '%s', 'delimiter', '\n');

parfor idate = 1:length(dates)

  map_date_str = char(dates(idate));

  %dstr = datestr(datenum(map_date_str), 'yyyymmdd');
  %if exist(strcat('output/kriging_prediction/vwc/kriged_', depth, 'cm_', dstr, '.csv', 'file')) == 2
  %   continue
  %end

  try
    krige_resid_xval(map_date_str, depth);
    krige_vwc_xval(map_date_str, depth);
  catch
    fprintf('error for date: %s', map_date_str);
  end

end

exit;
