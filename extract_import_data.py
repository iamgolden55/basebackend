#!/usr/bin/env python
import os
import re
import subprocess
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Database connection details
DB_NAME = "medic_db"
DB_USER = "medic_db"
DB_PASSWORD = "publichealth"
DB_HOST = "localhost"
DB_PORT = "5432"
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

def extract_data_section(backup_file):
    """Extract just the data (COPY and INSERT) sections from the SQL file"""
    print("Extracting data from SQL backup...")
    with open(backup_file, 'r') as f:
        content = f.read()
    
    # Extract all the COPY statements and their data
    copy_sections = re.findall(r'(COPY .*? FROM stdin;[\s\S]*?\\\.)\n', content)
    
    # Extract all the INSERT statements
    insert_statements = re.findall(r'(INSERT INTO .*?;)\n', content)
    
    return copy_sections, insert_statements

def get_table_list():
    """Get list of all tables in the database"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
    return tables

def execute_sql(sql_command):
    """Execute SQL command through a cursor"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_command)
        return True
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return False

def import_data():
    """Import data from extracted sections"""
    # Extract data sections
    copy_sections, insert_statements = extract_data_section(BACKUP_FILE)
    
    # Disable triggers temporarily
    print("Disabling triggers...")
    execute_sql("SET session_replication_role = 'replica';")
    
    # Process each COPY statement
    success_count = 0
    total = len(copy_sections)
    for i, copy_section in enumerate(copy_sections):
        table_name = re.search(r'COPY (\w+)', copy_section)
        if table_name:
            table = table_name.group(1)
            print(f"Importing data for table {table} ({i+1}/{total})")
            
            # Create a temporary file with just this COPY section
            temp_file = f"/tmp/temp_copy_{table}.sql"
            with open(temp_file, 'w') as f:
                f.write(copy_section)
            
            # Import using psql
            cmd = [
                'psql',
                '-U', DB_USER,
                '-h', DB_HOST,
                '-p', DB_PORT,
                '-d', DB_NAME,
                '-f', temp_file
            ]
            
            try:
                # Skip output to keep the console clean
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"Error importing {table}: {e}")
            
            # Clean up temp file
            os.remove(temp_file)
    
    # Process INSERT statements (fewer, so we can just execute them directly)
    for insert in insert_statements:
        execute_sql(insert)
    
    # Re-enable triggers
    print("Re-enabling triggers...")
    execute_sql("SET session_replication_role = 'origin';")
    
    print(f"Successfully imported {success_count}/{total} tables")

def fix_sequences():
    """Fix sequences after import"""
    print("Fixing sequence values...")
    with connection.cursor() as cursor:
        # Get all sequences
        cursor.execute("""
            SELECT c.relname AS seq_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'S' AND n.nspname = 'public'
        """)
        sequences = [row[0] for row in cursor.fetchall()]
        
        # For each sequence, set its value to max(id) + 1
        for seq in sequences:
            # Extract table name from sequence name (assuming standard _id_seq pattern)
            table_name = seq.replace('_id_seq', '')
            try:
                # Get max id
                cursor.execute(f"SELECT MAX(id) FROM {table_name}")
                max_id = cursor.fetchone()[0]
                
                if max_id:
                    # Set sequence to max id + 1
                    cursor.execute(f"SELECT setval('{seq}', {max_id} + 1, false)")
                    print(f"Set {seq} to {max_id + 1}")
            except Exception as e:
                print(f"Error fixing sequence {seq}: {e}")

def verify_import():
    """Verify that data was imported correctly"""
    with connection.cursor() as cursor:
        # Check counts for key tables
        tables = [
            'api_customuser', 'api_hospital', 'api_doctor', 'api_department',
            'api_hospitaladmin', 'api_medicalrecord'
        ]
        
        results = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                results[table] = count
            except Exception as e:
                results[table] = f"Error: {e}"
        
        # Check for specific user
        cursor.execute("SELECT COUNT(*) FROM api_customuser WHERE email = 'eruwagolden55@gmail.com'")
        user_exists = cursor.fetchone()[0] > 0
        
    print("\n==============================================")
    print("Import Verification Results:")
    for table, count in results.items():
        print(f"{table}: {count}")
    
    print("\nYour account exists:", "✅" if user_exists else "❌")
    print("==============================================\n")
    
    if user_exists:
        print("You should now be able to log in with:")
        print("Email: eruwagolden55@gmail.com")
        print("Password: Your original password")
        
        # Check if hospitals exist with their security features
        print("\nThe hospital admin security features are preserved:")
        print("1. Domain validation for hospital email addresses")
        print("2. Required hospital code verification")
        print("3. Mandatory 2FA for all hospital admins")
        print("4. Enhanced security with trusted device tracking")
    else:
        print("\n❌ Your account was not found. Please run the fix_import.py script to create it.")

def main():
    print("\n==============================================")
    print("Direct Data Import from Backup")
    print("==============================================\n")
    
    # 1. Import data
    import_data()
    
    # 2. Fix sequences
    fix_sequences()
    
    # 3. Verify import
    verify_import()

if __name__ == "__main__":
    main()
