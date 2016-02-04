CREATE TABLE stageiv_grid (x INTEGER, y INTEGER, PRIMARY KEY (x, y));

SELECT AddGeometryColumn('stageiv_grid', 'geom_pixel', 4326, 'POLYGON', 2);
