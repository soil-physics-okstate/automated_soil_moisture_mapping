# === USAGE CHECK ===
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <date: YYYY-MM-DD> <data_type: e.g., vwc>"
    exit 1
fi

# === INPUT ARGUMENTS ===
DATE="$1"
DATA_TYPE="$2"

# === CONFIGURATION ===
DB_NAME="soilmapnik"
export PGPASSWORD="Ali292Ali292"
export PGUSER="postgres"

DEPTHS_LIST="5 25 60"

# === CREATE DATABASE AND ENABLE POSTGIS IF NEEDED ===
echo "Checking if database '$DB_NAME' exists"

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "Database '$DB_NAME' already exists"
else
    echo "Creating database '$DB_NAME' and enabling PostGIS"
    createdb "$DB_NAME"
    psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    echo "Database and PostGIS extension created"
fi
echo "I AM HERE...IT IS OK SO FAR"
echo "Starting database setup for $DB_NAME on $DATE with data type $DATA_TYPE"

# === STEP 1: CREATE SOIL MOISTURE DATA TABLE ===
echo "Creating soil moisture data table"
cd ./database_scripts
psql -d "$DB_NAME" -f create_table_soil_moisture_data.sql
echo "soil_moisture_data table created"
cd ../

# === STEP 2: CREATE SOIL MOISTURE GRID TABLE ===
echo "Creating soil moisture grid table"
cd ./gis_setup/soil_moisture_grid
psql -d "$DB_NAME" -f create_soil_moisture_grid.sql
echo "soil_moisture_grid table created"

# === STEP 3: BUILD GRID GEOMETRY AND PROJECTION ===
python build_grid.py
psql -d "$DB_NAME" -f add_soil_moisture_grid_projection.sql
psql -d "$DB_NAME" -f build_grid_geometry.sql
echo "Grid geometry added to soil_moisture_grid table"
cd ../../

# === STEP 4: UPLOAD DATA FOR EACH DEPTH === 
# WE DONT NEED THIS STEP FOR NOW.
# cd ./database_scripts
# for DEPTH_CM in $DEPTHS_LIST; do
#     echo "Uploading soil moisture data for ${DATE}, ${DEPTH_CM}cm"

#     if bash ./upload_soil_moisture_data_to_sql.sh "$DATE" "$DATA_TYPE" "$DEPTH_CM"; then
#         echo "Uploaded data for ${DEPTH_CM}cm"
#     else
#         echo "Upload failed for ${DEPTH_CM}cm" >&2
#     fi
# done
# cd ../../


# === STEP 5: OPTIMIZE GEODATA ===
cd ./database_scripts
echo "Optimizing geospatial tables"
psql -d "$DB_NAME" -f optimize_geodata.sql
echo "All depths processed for $DATE ($DATA_TYPE)"
cd ../