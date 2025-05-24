# Script to properly import user data from the SQL dump
import os
import django
import subprocess
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connection
from api.models import CustomUser

def reset_db():
    """Clear all data from relevant tables without dropping schema"""
    with connection.cursor() as cursor:
        # Disable foreign key checks to allow truncating tables with foreign key relationships
        cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
        
        # List of tables to truncate
        tables = [
            'api_customuser',
            'api_hospital',
            'api_hospitaladmin',
            'api_doctor',
            'api_appointment',
            'api_department',
            'api_medication',
            # Add other important tables here
        ]
        
        for table in tables:
            try:
                print(f"Truncating {table}...")
                cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
            except Exception as e:
                print(f"Could not truncate {table}: {e}")

def extract_insert_statements():
    """Extract INSERT statements for CustomUser from the SQL dump"""
    sql_file = '/Users/new/Newphb/basebackend/medic_db_backup.sql'
    
    # Read the SQL file and find user data insert statements
    with open(sql_file, 'r') as f:
        content = f.read()
    
    # Extract all COPY statements and their data
    custom_user_copy = re.search(r'COPY public\.api_customuser[\s\S]+?\\\\\.',  content)
    
    if not custom_user_copy:
        print("Could not find CustomUser data in SQL file")
        return None
    
    # Format the statement for direct execution
    copy_statement = custom_user_copy.group(0)
    
    # Save to a temporary file
    with open('user_data.sql', 'w') as f:
        f.write(copy_statement)
    
    return 'user_data.sql'

def import_user_data():
    """Import user data directly using psql"""
    data_file = extract_insert_statements()
    if not data_file:
        return False
    
    # Get database connection details
    db_settings = connection.settings_dict
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    db_port = db_settings['PORT']
    
    # Set environment variables for psql
    os.environ['PGPASSWORD'] = db_password
    
    # Use psql to execute the SQL file
    cmd = [
        'psql',
        '-U', db_user,
        '-h', db_host,
        '-p', str(db_port),
        '-d', db_name,
        '-f', data_file
    ]
    
    try:
        print("Importing user data...")
        subprocess.run(cmd, check=True)
        print("User data imported successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error importing user data: {e}")
        return False

def create_user_manually():
    """Create a single user manually if import fails"""
    try:
        if CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists():
            print("User already exists, skipping manual creation")
            return
            
        print("Creating user manually...")
        user = CustomUser.objects.create_user(
            email='eruwagolden55@gmail.com',
            password='PublicHealth24',  # You can change this password later
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
        print("User created successfully!")
    except Exception as e:
        print(f"Error creating user: {e}")

def main():
    # Check current user count
    initial_count = CustomUser.objects.count()
    print(f"Initial user count: {initial_count}")
    
    # Try to import from SQL dump
    if initial_count == 0:
        # First try direct import
        if not import_user_data():
            # If that fails, create a user manually
            create_user_manually()
    
    # Verify the result
    final_count = CustomUser.objects.count()
    print(f"Final user count: {final_count}")
    print(f"User 'eruwagolden55@gmail.com' exists: {CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists()}")

if __name__ == "__main__":
    main()
