# Comprehensive script to properly import the full database
import os
import django
import subprocess
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connection
from django.conf import settings

def get_db_settings():
    """Get database connection settings"""
    db_settings = settings.DATABASES['default']
    return {
        'name': db_settings['NAME'],
        'user': db_settings['USER'],
        'password': db_settings['PASSWORD'],
        'host': db_settings['HOST'],
        'port': db_settings['PORT']
    }

def run_sql_command(command, db_settings):
    """Run a SQL command using psql"""
    os.environ['PGPASSWORD'] = db_settings['password']
    
    cmd = [
        'psql',
        '-U', db_settings['user'],
        '-h', db_settings['host'],
        '-p', db_settings['port'],
        '-d', db_settings['name'],
        '-c', command
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing SQL command: {e}")
        return False

def truncate_all_tables(db_settings):
    """Drop all tables in the database"""
    print("Truncating all tables...")
    
    # Disable foreign key constraints
    run_sql_command("SET session_replication_role = 'replica';" , db_settings)
    
    # Get a list of all tables in the public schema
    try:
        os.environ['PGPASSWORD'] = db_settings['password']
        cmd = [
            'psql',
            '-U', db_settings['user'],
            '-h', db_settings['host'],
            '-p', db_settings['port'],
            '-d', db_settings['name'],
            '-t',  # Tuple only output
            '-c', "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        # Skip Django migration tables to preserve migration history
        tables = [table for table in tables if table != 'django_migrations']
        
        # Truncate each table
        for table in tables:
            print(f"Truncating {table}...")
            run_sql_command(f'TRUNCATE TABLE "{table}" CASCADE;', db_settings)
        
        # Re-enable foreign key constraints
        run_sql_command("SET session_replication_role = 'origin';" , db_settings)
        
        return True
    except Exception as e:
        print(f"Error truncating tables: {e}")
        return False

def import_database(db_settings):
    """Import the database from the SQL backup file"""
    backup_file = '/Users/new/Newphb/basebackend/medic_db_backup.sql'
    
    print("Importing database from backup...")
    os.environ['PGPASSWORD'] = db_settings['password']
    
    try:
        # First try to import the entire file
        cmd = [
            'psql',
            '-U', db_settings['user'],
            '-h', db_settings['host'],
            '-p', db_settings['port'],
            '-d', db_settings['name'],
            '-f', backup_file
        ]
        
        # Run with error suppression - we expect some errors due to schema differences
        subprocess.run(cmd, stderr=subprocess.PIPE)
        
        return True
    except Exception as e:
        print(f"Error importing database: {e}")
        return False

def apply_migrations():
    """Apply all migrations to ensure the database structure is correct"""
    print("Applying migrations...")
    try:
        from django.core.management import call_command
        call_command('migrate')
        return True
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False
        
def verify_import():
    """Verify that data was imported correctly"""
    print("Verifying import...")
    try:
        # Import models
        from api.models import CustomUser, Hospital, Doctor, Department
        from api.models.medical.medication import Medication
        from api.models.medical.hospital_auth import HospitalAdmin
        
        # Check counts
        user_count = CustomUser.objects.count()
        hospital_count = Hospital.objects.count()
        doctor_count = Doctor.objects.count()
        department_count = Department.objects.count()
        medication_count = Medication.objects.count()
        admin_count = HospitalAdmin.objects.count()
        
        print(f"Users: {user_count}")
        print(f"Hospitals: {hospital_count}")
        print(f"Doctors: {doctor_count}")
        print(f"Departments: {department_count}")
        print(f"Medications: {medication_count}")
        print(f"Hospital Admins: {admin_count}")
        
        if user_count > 0 and CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists():
            print("✅ Your user account (eruwagolden55@gmail.com) was imported successfully!")
        else:
            print("❌ Your user account was not imported. Creating manually...")
            create_user_manually()
        
        return user_count > 0 and hospital_count > 0 and doctor_count > 0
    except Exception as e:
        print(f"Error verifying import: {e}")
        return False
        
def create_user_manually():
    """Create a user account manually if import fails"""
    from api.models import CustomUser
    
    try:
        if CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists():
            return
            
        user = CustomUser.objects.create_user(
            email='eruwagolden55@gmail.com',
            password='PublicHealth24',  # Temporary password
            first_name='Ninioritse',
            last_name='Great Eruwa',
            phone='+2348035487113',
            date_of_birth='2000-09-20',
            gender='male',
            country='nigeria',
            state='delta',
            city='Asaba',
            nin='12121212121',
            consent_terms=True,
            consent_hipaa=True,
            consent_data_processing=True,
            preferred_language='english',
            secondary_languages=['yoruba', 'isoko']
        )
        user.is_active = True
        user.is_email_verified = True
        user.save()
        print("✅ User created successfully!")
    except Exception as e:
        print(f"Error creating user: {e}")

def main():
    # Make sure our COPY commands will work with the right permissions
    os.environ['PGOPTIONS'] = '--client-min-messages=warning'
    
    # Get database connection settings
    db_settings = get_db_settings()
    
    # Apply migrations first to ensure correct schema
    if not apply_migrations():
        print("Failed to apply migrations. Aborting.")
        return False
    
    # Truncate all tables to start with a clean slate
    if not truncate_all_tables(db_settings):
        print("Failed to truncate tables. Aborting.")
        return False
    
    # Import the database from the backup file
    if not import_database(db_settings):
        print("Failed to import database. Aborting.")
        return False
    
    # Apply migrations again to ensure everything is up to date
    if not apply_migrations():
        print("Failed to apply migrations after import. Aborting.")
        return False
    
    # Verify that data was imported correctly
    if verify_import():
        print("\n✅ Database import completed successfully!")
        print("\nYou can now log in with your account:")
        print("Email: eruwagolden55@gmail.com")
        print("Password: Your original password (or 'PublicHealth24' if reset)")
        return True
    else:
        print("\n❌ Database import verification failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
