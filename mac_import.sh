#!/bin/bash

# Database connection details
DB_NAME="medic_db"
DB_USER="medic_db"
DB_PASSWORD="publichealth"
BACKUP_FILE="/Users/new/Newphb/basebackend/medic_db_backup.sql"
MODIFIED_BACKUP="/tmp/modified_backup.sql"

echo "==============================================="
echo "macOS PostgreSQL Import Script"
echo "==============================================="

echo "\nThis script will guide you through importing the database on macOS.\n"

# First, check connection to PostgreSQL
echo "Checking connection to PostgreSQL..."
psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "\n\u274C Error: Could not connect to PostgreSQL with user $DB_USER"
    echo "Please make sure PostgreSQL is running and your credentials are correct."
    exit 1
fi

echo "\u2705 Successfully connected to PostgreSQL"

# Create PostgreSQL commands file
PSQL_COMMANDS="/tmp/import_commands.sql"

cat > "$PSQL_COMMANDS" << EOF
-- Create a new database for the import
DROP DATABASE IF EXISTS ${DB_NAME}_new;
CREATE DATABASE ${DB_NAME}_new WITH TEMPLATE template0;
\c ${DB_NAME}_new

-- Import the backup file
\i ${MODIFIED_BACKUP}

-- Fix sequences
SELECT setval('public.api_customuser_id_seq', (SELECT MAX(id) FROM public.api_customuser), true);
SELECT setval('public.api_hospital_id_seq', (SELECT MAX(id) FROM public.api_hospital), true);
SELECT setval('public.api_department_id_seq', (SELECT MAX(id) FROM public.api_department), true);
SELECT setval('public.api_doctor_id_seq', (SELECT MAX(id) FROM public.api_doctor), true);
SELECT setval('public.api_hospitaladmin_id_seq', (SELECT MAX(id) FROM public.api_hospitaladmin), true);
SELECT setval('public.api_medicalrecord_id_seq', (SELECT MAX(id) FROM public.api_medicalrecord), true);

-- Check import results
SELECT COUNT(*) AS user_count FROM public.api_customuser;
SELECT COUNT(*) AS hospital_count FROM public.api_hospital;
SELECT COUNT(*) AS doctor_count FROM public.api_doctor;
SELECT COUNT(*) AS department_count FROM public.api_department;
SELECT COUNT(*) AS record_count FROM public.api_medicalrecord;
SELECT COUNT(*) AS appointment_count FROM public.api_appointment;

-- Check for specific account
SELECT EXISTS(SELECT 1 FROM public.api_customuser WHERE email = 'eruwagolden55@gmail.com') AS user_exists;
EOF

echo "\nCreated PostgreSQL commands at $PSQL_COMMANDS"

echo "\nManual Import Instructions:\n"
echo "1. Run the following command in your terminal:\n"
echo "   psql -U $DB_USER postgres -f $PSQL_COMMANDS"
echo "\n2. After successful import, update your .env file:\n"
echo "   DB_NAME=${DB_NAME}_new"
echo "\nOr you can run this command to replace your existing database:\n"
echo "   psql -U $DB_USER postgres -c \"ALTER DATABASE ${DB_NAME}_new RENAME TO ${DB_NAME};\""

echo "\nRemember that all hospital admin security features are preserved:"
echo "- Domain validation for hospital email addresses"
echo "- Required hospital code verification"
echo "- Mandatory 2FA for all hospital admins"
echo "- Enhanced security with trusted device tracking"
echo "- Rate limiting after 3 failed attempts"
echo "- Account lockout for 15 minutes after 5 failed attempts"

echo "\nWould you like me to attempt the import now? (y/n)"
read -p "> " IMPORT_NOW

if [ "$IMPORT_NOW" = "y" ]; then
    echo "\nAttempting to import the database..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER postgres -f "$PSQL_COMMANDS"
    
    if [ $? -eq 0 ]; then
        echo "\n\u2705 Database import completed successfully!"
        echo "\nTo start using the new database, update your .env file:"
        echo "DB_NAME=${DB_NAME}_new"
    else
        echo "\n\u274C Database import failed. Please check the error messages above."
    fi
else
    echo "\nYou can run the import later using the command:\n"
    echo "PGPASSWORD=$DB_PASSWORD psql -U $DB_USER postgres -f \"$PSQL_COMMANDS\""
fi
