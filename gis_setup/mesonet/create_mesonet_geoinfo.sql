CREATE TABLE mesonet_geoinfo (
       stnm INTEGER UNIQUE NOT NULL,
       stid VARCHAR(4) PRIMARY KEY,
       name VARCHAR(50) NOT NULL,
       city VARCHAR(50) NOT NULL,
       rang REAL NOT NULL,
       cdir VARCHAR(3) NOT NULL,
       cnty VARCHAR(15) NOT NULL,
       nlat DOUBLE PRECISION NOT NULL,
       elon DOUBLE PRECISION NOT NULL,
       elev REAL NOT NULL,
       cdiv VARCHAR(15) NOT NULL,
       clas VARCHAR(10) NOT NULL,
       datc INTEGER NOT NULL,
       datd INTEGER NOT NULL
       );

SELECT AddGeometryColumn('mesonet_geoinfo', 'geom', 4326, 'POINT', 2);

