cd ./gis_setup/soil_moisture_grid
python build_grid.py
psql -d soilmapnik -f build_grid_geometry.sql
psql -d soilmapnik -f add_soil_moisture_grid_projection.sql
cd ../../

cd ./database_scripts
bash ./upload_soil_moisture_data_to_sql.sh 2024-04-17 vwc 5
psql -d soilmapnik -f optimize_geodata.sql
cd ../