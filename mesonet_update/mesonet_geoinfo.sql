CREATE TABLE mesonet_geoinfo (
       stid varchar(4) PRIMARY KEY,
       stnm int UNIQUE NOT NULL,
       nlat double precision NOT NULL,
       elon double precision NOT NULL,
       elev double precision NOT NULL,
       datc int NOT NULL,
       datd int NOT NULL,
       x double precision,
       y double precision,
       mukey int,
       s4x int,
       s4y int
       );

SELECT AddGeometryColumn('mesonet_geoinfo', 'geom', 4326, 'POINT', 2);
