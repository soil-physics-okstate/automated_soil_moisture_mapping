DROP TABLE soil_moisture_data_raster_xxDEPTHxx_temp;

CREATE TABLE soil_moisture_data_raster_xxDEPTHxx_temp AS 
SELECT 
  ST_Transform(
    ST_Union(
      ST_AsRaster( 
        geom_point, 
      	r.rast, 
      	'32BF', 
	product_value, 
      	-9999
      )
    ), 3857) AS rast
FROM soil_moisture_grid_raster AS r, 
  soil_moisture_grid_opt AS g INNER JOIN soil_moisture_data AS d 
  ON (g.id = d.id)
  WHERE (
    product_valid = 'xxDATExx' AND
    product_name = 'xxVARxx' AND
    product_depth = xxDEPTHxx
  );
