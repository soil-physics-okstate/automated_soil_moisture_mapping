CREATE TABLE soil_moisture_timeseries (
       id INTEGER NOT NULL,
       valid TIMESTAMP NOT NULL,
       depth INTEGER NOT NULL,
       vwc DOUBLE PRECISION,
       PRIMARY KEY (id, valid, depth)
);
