#!/bin/bash
set -e

# Check if database dump exists
if [ -f /app/backup/db_dump.dump ]; then
  echo "Database dump found, preparing to import..."

  # Wait for PostgreSQL to be ready
  echo "Waiting for PostgreSQL to be ready..."
  while ! pg_isready -h db -U medic_db; do
    sleep 1
  done

  # Check if database is already populated with tables
  echo "Checking if database is already initialized..."
  TABLES=$(PGPASSWORD=publichealth psql -h db -U medic_db -d medic_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
  
  # Trim whitespace from result
  TABLES=$(echo $TABLES | xargs)
  
  if [ "$TABLES" -eq "0" ]; then
    echo "Database is empty, restoring from dump..."
    PGPASSWORD=publichealth pg_restore -h db -U medic_db -d medic_db -c -v /app/backup/db_dump.dump
    echo "Database restored successfully!"
    
    # Validate hospital admin accounts after restore
    echo "Verifying hospital admin accounts and security settings..."
    python manage.py setup_hospital_admins --verify-only
  else
    echo "Database already has tables, skipping import."
  fi
else
  echo "No database dump found at /app/backup/db_dump.dump, running migrations instead."
  python manage.py migrate
  
  # If we're setting up from scratch, create hospital admin accounts
  echo "Setting up hospital admin accounts and security features..."
  python manage.py setup_hospital_admins
fi

# Run any additional setup needed
python manage.py collectstatic --noinput

# Ensure proper permissions for media and static files
chmod -R 755 /app/media /app/staticfiles

echo "System ready with all hospital admin features and security settings configured!"
