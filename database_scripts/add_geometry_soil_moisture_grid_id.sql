SELECT AddGeometryColumn('soil_moisture_grid_id', 'geom_point', 4326, 'POINT', 2);
SELECT AddGeometryColumn('soil_moisture_grid_id', 'geom_pixel', 4326, 'POLYGON', 2);

UPDATE soil_moisture_grid_id
       SET geom_point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

UPDATE soil_moisture_grid_id 
       SET geom_pixel = ST_Transform(ST_Expand(ST_Transform(geom_point, 990001), 400), 4326);
