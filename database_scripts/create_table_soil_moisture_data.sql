CREATE TABLE soil_moisture_data (
       id INTEGER NOT NULL,
       product_valid TIMESTAMP NOT NULL,
       product_name VARCHAR(20) NOT NULL,
       product_depth INTEGER NOT NULL,
       product_value DOUBLE PRECISION,
       PRIMARY KEY (id, product_valid, product_name, product_depth)
);

CREATE INDEX idx_timeseries ON soil_moisture_data (product_valid);
