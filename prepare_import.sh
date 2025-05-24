#!/bin/bash

# Database connection details
DB_NAME="medic_db"
REGULAR_USER="medic_db"
BACKUP_FILE="/Users/new/Newphb/basebackend/medic_db_backup.sql"

echo "==============================================="
echo "Database Import Preparation Script"
echo "==============================================="

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

echo "Backup file found at $BACKUP_FILE"

# Create a modified backup file without problematic commands
MODIFIED_BACKUP="/tmp/modified_backup.sql"
echo "Creating modified backup file without problematic commands..."
grep -v "session_replication_role" "$BACKUP_FILE" > "$MODIFIED_BACKUP"

# Create instructions for manual import
INSTRUCTIONS_FILE="/Users/new/Newphb/basebackend/import_instructions.txt"

cat > "$INSTRUCTIONS_FILE" << EOF
===============================================
Database Import Instructions
===============================================

To import the complete database with all tables and data, follow these steps:

1. Open Terminal

2. Run the following commands (you'll be prompted for your password):

   # Connect to PostgreSQL as superuser
   sudo -u postgres psql

   # Inside psql, run these commands:
   -- Create a new database
   DROP DATABASE IF EXISTS ${DB_NAME}_new;
   CREATE DATABASE ${DB_NAME}_new WITH TEMPLATE template0 OWNER ${REGULAR_USER};
   \c ${DB_NAME}_new

   -- Disable triggers to allow full import
   SET session_replication_role = 'replica';

   -- Import the backup (use the modified file)
   \i ${MODIFIED_BACKUP}

   -- Fix sequence values
   SELECT setval('public.api_customuser_id_seq', (SELECT MAX(id) FROM public.api_customuser), true);
   SELECT setval('public.api_hospital_id_seq', (SELECT MAX(id) FROM public.api_hospital), true);
   SELECT setval('public.api_department_id_seq', (SELECT MAX(id) FROM public.api_department), true);
   SELECT setval('public.api_doctor_id_seq', (SELECT MAX(id) FROM public.api_doctor), true);
   SELECT setval('public.api_hospitaladmin_id_seq', (SELECT MAX(id) FROM public.api_hospitaladmin), true);
   SELECT setval('public.api_medicalrecord_id_seq', (SELECT MAX(id) FROM public.api_medicalrecord), true);
   
   -- Re-enable triggers
   SET session_replication_role = 'origin';

   -- Check import results
   SELECT COUNT(*) AS user_count FROM public.api_customuser;
   SELECT COUNT(*) AS hospital_count FROM public.api_hospital;
   SELECT COUNT(*) AS doctor_count FROM public.api_doctor;
   SELECT COUNT(*) AS department_count FROM public.api_department;
   SELECT COUNT(*) AS record_count FROM public.api_medicalrecord;
   SELECT COUNT(*) AS appointment_count FROM public.api_appointment;
   
   -- Check for your specific account
   SELECT COUNT(*) FROM public.api_customuser WHERE email = 'eruwagolden55@gmail.com';

   -- Exit psql
   \q

3. After successful import, update your .env file:

   DB_NAME=${DB_NAME}_new

4. Alternatively, you can rename the database:

   sudo -u postgres psql -c "ALTER DATABASE ${DB_NAME}_new RENAME TO ${DB_NAME};"
   (This will replace your existing database)

5. Remember that all security features are preserved:
   - Domain validation for hospital email addresses
   - Required hospital code verification
   - Mandatory 2FA for all hospital admins
   - Enhanced security with trusted device tracking
   - Rate limiting after 3 failed attempts
   - Account lockout for 15 minutes after 5 failed attempts

Note: If you have any issues during import, you can continue using your current database with the
manually created user account (eruwagolden55@gmail.com).
===============================================
EOF

echo "\nModified backup file created at: $MODIFIED_BACKUP"
echo "Instructions created at: $INSTRUCTIONS_FILE"
echo "\nPlease follow the instructions in the file to complete the import."
echo "==============================================="
