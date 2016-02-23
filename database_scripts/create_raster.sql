CREATE TABLE soil_moisture_grid_raster AS  
  SELECT ST_AsRaster(
    ST_SetSRID(ST_Extent(ST_Transform(geom_pixel, 990001)), 990001),
    800.0, 800.0,
    '32BF'::text,
    -999, -999) AS rast
  FROM soil_moisture_grid;
