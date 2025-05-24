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
echo "Complete Database Import Script"
echo "==============================================="

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

echo "Backup file found. Starting import process..."

# Create a cleaned version of the SQL file
CLEANED_FILE="/tmp/cleaned_backup.sql"
echo "Cleaning up the SQL file to avoid permission issues..."
cat "$BACKUP_FILE" | grep -v "session_replication_role" > "$CLEANED_FILE"

# Use psql to run the cleaned SQL file directly
echo "Running direct import with psql..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$CLEANED_FILE"

# Verify that data was imported correctly
echo "\nVerifying import results..."
USER_COUNT=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_customuser;" | tr -d '\n')
HOSPITAL_COUNT=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_hospital;" | tr -d '\n')
DOCTOR_COUNT=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_doctor;" | tr -d '\n')
DEPARTMENT_COUNT=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_department;" | tr -d '\n')
RECORD_COUNT=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_medicalrecord;" | tr -d '\n')

# Check for your user account
USER_EXISTS=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM api_customuser WHERE email = 'eruwagolden55@gmail.com';" | tr -d '\n')

echo "\n==============================================="
echo "Import Verification Results:"
echo "Users: $USER_COUNT"
echo "Hospitals: $HOSPITAL_COUNT"
echo "Doctors: $DOCTOR_COUNT"
echo "Departments: $DEPARTMENT_COUNT"
echo "Medical Records: $RECORD_COUNT"
echo "\nYour account exists: $([ "$USER_EXISTS" -gt 0 ] && echo "u2705" || echo "u274c")"
echo "==============================================="

# If the user account doesn't exist, attempt to run the create_user.py script
if [ "$USER_EXISTS" -eq 0 ]; then
    echo "\nYour account was not found in the imported data."
    echo "Running the user creation script to ensure you can log in..."
    cd /Users/new/Newphb/basebackend && source venv/bin/activate && python create_user.py
fi
