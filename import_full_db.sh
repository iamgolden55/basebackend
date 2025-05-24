#!/bin/bash

# Database connection details
DB_NAME="medic_db"
DB_USER="medic_db"
DB_PASSWORD="publichealth"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_FILE="/Users/new/Newphb/basebackend/medic_db_backup.sql"

# Export password for psql commands
export PGPASSWORD="$DB_PASSWORD"

echo "==============================================="
echo "Full Database Import Script"
echo "==============================================="

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

echo "Backup file found. Starting import process..."

# Option 1: Try to drop and recreate the database (requires superuser)
echo "\nOption 1: Attempting to drop and recreate database..."
if dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME 2>/dev/null && \
   createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME 2>/dev/null; then
    echo "Database dropped and recreated successfully."
    echo "Importing backup..."
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f "$BACKUP_FILE"
    echo "Import completed with Option 1."
    exit 0
fi

echo "Option 1 failed. Moving to Option 2..."

# Option 2: Try to truncate all tables in the database
echo "\nOption 2: Attempting to truncate all tables..."

# Get a list of all tables in public schema
TABLES=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';")

# Disable foreign key checks
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "BEGIN; SET CONSTRAINTS ALL DEFERRED;"

# Truncate each table
for TABLE in $TABLES; do
    # Skip the django migrations table
    if [ "$TABLE" != "django_migrations" ]; then
        echo "Truncating $TABLE..."
        psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "TRUNCATE TABLE \"$TABLE\" CASCADE;"
    fi
done

# Re-enable foreign key checks
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "COMMIT;"

echo "All tables truncated. Importing backup..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f "$BACKUP_FILE"

echo "Import completed with Option 2."

# Verify that data was imported correctly
USER_COUNT=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -t -c "SELECT COUNT(*) FROM api_customuser;" | tr -d '\n')
HOSPITAL_COUNT=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -t -c "SELECT COUNT(*) FROM api_hospital;" | tr -d '\n')
DOCTOR_COUNT=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -t -c "SELECT COUNT(*) FROM api_doctor;" | tr -d '\n')

echo "\n==============================================="
echo "Import Verification Results:"
echo "Users: $USER_COUNT"
echo "Hospitals: $HOSPITAL_COUNT"
echo "Doctors: $DOCTOR_COUNT"
echo "\nIf these numbers are greater than 0, the import was successful."
echo "\nYou should now be able to log in with:"
echo "Email: eruwagolden55@gmail.com"
echo "Password: Your original password"
echo "==============================================="
