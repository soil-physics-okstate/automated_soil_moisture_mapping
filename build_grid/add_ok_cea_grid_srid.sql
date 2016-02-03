-- This SRID definition will let PostGIS convert any spatial object into our x/y grid

INSERT INTO spatial_ref_sys (
       srid, 
       auth_name, 
       auth_srid, 
       proj4text
) VALUES (
       990001,
       'custom',
       990001,
       '+proj=cea +a=6378137 +b=6378137 +lon_0=-97.674 +lat_ts=35.350 +x_0=-0.000000002310 +y_0=-4566092.606432600878 +units=m +no_defs'
);
