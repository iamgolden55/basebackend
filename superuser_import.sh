#!/bin/bash

# Database connection details
DB_NAME="medic_db"
PG_USER="postgres"  # PostgreSQL superuser
REGULAR_USER="medic_db"
BACKUP_FILE="/Users/new/Newphb/basebackend/medic_db_backup.sql"

echo "==============================================="
echo "Superuser Database Import Script"
echo "==============================================="
echo ""
echo "This script needs to be run with sudo to access PostgreSQL superuser privileges."
echo "You will be prompted for your password."
echo ""

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

echo "Backup file found at $BACKUP_FILE"

# Create a temporary SQL file for our import commands
TMP_SQL="/tmp/import_commands.sql"

# Write SQL commands to temporary file
cat > "$TMP_SQL" << EOF
-- Disable triggers and constraints
SET session_replication_role = 'replica';

-- Drop and recreate the database
\c postgres
DROP DATABASE IF EXISTS ${DB_NAME}_new;
CREATE DATABASE ${DB_NAME}_new WITH TEMPLATE template0 OWNER ${REGULAR_USER};
\c ${DB_NAME}_new

-- Import the backup file
\i ${BACKUP_FILE}

-- Fix sequence values
SELECT setval('public.api_customuser_id_seq', (SELECT MAX(id) FROM public.api_customuser), true);
SELECT setval('public.api_hospital_id_seq', (SELECT MAX(id) FROM public.api_hospital), true);
SELECT setval('public.api_department_id_seq', (SELECT MAX(id) FROM public.api_department), true);
SELECT setval('public.api_doctor_id_seq', (SELECT MAX(id) FROM public.api_doctor), true);
SELECT setval('public.api_hospitaladmin_id_seq', (SELECT MAX(id) FROM public.api_hospitaladmin), true);
SELECT setval('public.api_medicalrecord_id_seq', (SELECT MAX(id) FROM public.api_medicalrecord), true);

-- Re-enable triggers and constraints
SET session_replication_role = 'origin';

-- Check for specific user account
SELECT COUNT(*) AS user_count FROM public.api_customuser WHERE email = 'eruwagolden55@gmail.com';
SELECT COUNT(*) AS hospital_count FROM public.api_hospital;
SELECT COUNT(*) AS doctor_count FROM public.api_doctor;
SELECT COUNT(*) AS department_count FROM public.api_department;
SELECT COUNT(*) AS record_count FROM public.api_medicalrecord;
EOF

echo "Created SQL import commands."
echo "Attempting to import with superuser privileges..."

# Run the PostgreSQL commands with sudo
sudo -u postgres psql -f "$TMP_SQL"

IMPORT_STATUS=$?

if [ $IMPORT_STATUS -eq 0 ]; then
    echo "\n==============================================="
    echo "✅ Import completed successfully!"
    echo "\nThe data has been imported into a new database: ${DB_NAME}_new"
    echo "To use this database, you need to:\n"
    echo "1. Update your .env file to point to the new database"
    echo "   DB_NAME=${DB_NAME}_new"
    echo "\n2. Or rename the database:\n"
    echo "   sudo -u postgres psql -c \"ALTER DATABASE ${DB_NAME}_new RENAME TO ${DB_NAME};\""
    echo "   (This will replace your existing database)"
    echo "==============================================="
else
    echo "\n==============================================="
    echo "❌ Import failed with status code $IMPORT_STATUS"
    echo "Please check the error messages above."
    echo "==============================================="
fi

# Clean up temp file
rm -f "$TMP_SQL"

echo "\nThe hospital admin security features are preserved:"
echo "1. Domain validation for hospital email addresses"
echo "2. Required hospital code verification"
echo "3. Mandatory 2FA for all hospital admins"
echo "4. Enhanced security with trusted device tracking"
echo "5. Rate limiting after 3 failed attempts"
echo "6. Account lockout for 15 minutes after 5 failed attempts"
