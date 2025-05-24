# Script to import data while preserving schema structure
import os
import django
import subprocess
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connections
from django.conf import settings

def main():
    print("Starting data import process...")
    
    # Get database connection parameters
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    db_port = db_settings['PORT']
    
    # Set PostgreSQL password environment variable
    os.environ['PGPASSWORD'] = db_password
    
    # Step 1: Extract only the data (no schema) from the backup file
    print("Extracting data from backup file...")
    data_extraction_cmd = [
        'pg_restore',
        '-f', 'data_only.sql',
        '--data-only',
        '/Users/new/Newphb/basebackend/medic_db_backup.sql'
    ]
    
    try:
        subprocess.run(data_extraction_cmd, check=True)
        print("Data extraction completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting data: {e}")
        if not os.path.exists('data_only.sql'):
            print("Failed to create data_only.sql. The backup might not be in pg_dump format.")
            print("Trying alternative approach with direct SQL file...")
            
            # Step 1 (alternative): Truncate all tables to prepare for new data
            print("Truncating all tables...")
            connection = connections['default']
            with connection.cursor() as cursor:
                # Disable foreign key checks
                cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
                
                # Get all tables
                cursor.execute("""SELECT tablename FROM pg_tables WHERE schemaname = 'public';""")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Truncate each table
                for table in tables:
                    if table != 'django_migrations':  # Skip migrations table
                        try:
                            print(f"Truncating {table}...")
                            cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
                        except Exception as e:
                            print(f"Could not truncate {table}: {e}")
            
            # Step 2 (alternative): Import all data directly
            print("Importing data directly from SQL backup...")
            import_cmd = [
                'psql',
                '-U', db_user,
                '-h', db_host,
                '-p', db_port,
                '-d', db_name,
                '-c', f"\\COPY public.api_appointment FROM stdin;",
                '-f', '/Users/new/Newphb/basebackend/medic_db_backup.sql'
            ]
            
            try:
                subprocess.run(import_cmd, check=True)
                print("Data import completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error importing data: {e}")
                return
            
            return
    
    # Step 2: Apply migrations to ensure correct database structure
    print("Applying migrations to ensure correct database structure...")
    try:
        from django.core.management import call_command
        call_command('migrate')
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return
    
    # Step 3: Import the data
    print("Importing data...")
    import_cmd = [
        'psql',
        '-U', db_user,
        '-h', db_host,
        '-p', db_port,
        '-d', db_name,
        '-f', 'data_only.sql'
    ]
    
    try:
        subprocess.run(import_cmd, check=True)
        print("Data import completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error importing data: {e}")
        return
    
    print("Database import process completed!")
    print("Note: You may need to run migrations again if there are any inconsistencies.")

if __name__ == "__main__":
    main()
