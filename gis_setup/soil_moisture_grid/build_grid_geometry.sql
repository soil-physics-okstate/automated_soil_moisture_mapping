-- add point and pixel geometry columns
SELECT AddGeometryColumn('soil_moisture_grid', 'geom_point', 4326, 'POINT', 2);
SELECT AddGeometryColumn('soil_moisture_grid', 'geom_pixel', 4326, 'POLYGON', 2);

-- build point geometries
UPDATE soil_moisture_grid SET 
       geom_point = ST_Transform( ST_SetSRID( ST_MakePoint(x, y), 990001 ), 4326);

-- build pixel geometries (800 m pixels = expand by 400 m)
UPDATE soil_moisture_grid SET
       geom_pixel = ST_Transform( ST_Expand( ST_Transform(geom_point, 990001), 400 ), 4326);

