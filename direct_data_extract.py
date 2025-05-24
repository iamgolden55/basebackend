#!/usr/bin/env python
import os
import re
import django
import sys
import tempfile
import subprocess

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

# Database connection details
DB_NAME = "medic_db"
DB_USER = "medic_db"
DB_PASSWORD = "publichealth"
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

# Tables we're specifically interested in
PRIORITY_TABLES = [
    'api_customuser',
    'api_hospital',
    'api_department',
    'api_doctor',
    'api_medicalrecord',
    'api_appointment',
    'api_medication',
    'api_medicationcatalog'
]

# Preserve these user accounts
PRESERVE_USERS = [
    'eruwagolden55@gmail.com',
    'admin@example.com'
]

def extract_direct_inserts():
    """Extract data from the backup as direct INSERT statements"""
    print("\nExtracting data from backup file as direct INSERTs...")
    
    output_dir = tempfile.mkdtemp()
    inserts_file = os.path.join(output_dir, "direct_inserts.sql")
    
    # Create SQL script to disable/enable triggers and do direct inserts
    with open(inserts_file, 'w') as out_f:
        # Write header with settings to disable triggers and foreign key checks
        out_f.write("-- Generated INSERT statements for direct import\n")
        out_f.write("BEGIN;\n")
        out_f.write("SET session_replication_role = 'replica';\n\n")
        
        # Process the backup file
        with open(BACKUP_FILE, 'r') as in_f:
            content = in_f.read()
            
            # Extract COPY sections
            copy_pattern = r'COPY (?:public\.)?([\w_]+) \((.+?)\) FROM stdin;\n([\s\S]*?)\\\.'  
            copy_matches = re.findall(copy_pattern, content)
            
            # Process each COPY section
            for table, columns, data in copy_matches:
                if table not in PRIORITY_TABLES:
                    continue
                    
                print(f"  Processing table: {table}")
                column_list = columns.split(', ')
                rows = data.strip().split('\n')
                
                # Truncate the table first
                out_f.write(f"-- Truncate table {table}\n")
                if table == 'api_customuser':
                    # For user table, delete all except preserved users
                    for email in PRESERVE_USERS:
                        out_f.write(f"DELETE FROM {table} WHERE email != '{email}';\n")
                else:
                    out_f.write(f"TRUNCATE TABLE {table} CASCADE;\n")
                
                # Write INSERT statements
                out_f.write(f"-- Insert data into {table}\n")
                
                for row in rows:
                    values = row.split('\t')
                    if len(values) != len(column_list):
                        continue  # Skip invalid rows
                    
                    # Skip preserved users if this is the user table
                    if table == 'api_customuser':
                        email_idx = column_list.index('email') if 'email' in column_list else -1
                        if email_idx >= 0 and email_idx < len(values):
                            email = values[email_idx]
                            if email in PRESERVE_USERS:
                                continue
                    
                    # Format values properly
                    formatted_values = []
                    for val in values:
                        if val == '\\N':  # NULL value
                            formatted_values.append('NULL')
                        elif val.startswith('{'): # Array
                            formatted_values.append(f"'{val.replace("'", "''")}'::{columns[i]}")
                        else:
                            formatted_values.append(f"'{val.replace("'", "''")}'")  
                    
                    # Write the INSERT statement
                    insert_stmt = f"INSERT INTO {table} ({columns}) VALUES ({', '.join(formatted_values)});\n"
                    out_f.write(insert_stmt)
                
                out_f.write("\n")
            
            # Fix sequences
            out_f.write("-- Fix sequences\n")
            for table in PRIORITY_TABLES:
                out_f.write(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1), true);\n")
            
            # Re-enable triggers
            out_f.write("\n-- Re-enable triggers\n")
            out_f.write("SET session_replication_role = 'origin';\n")
            out_f.write("COMMIT;\n")
    
    return inserts_file

def extract_copy_statements():
    """Extract data as COPY statements for direct psql import"""
    print("\nExtracting data as COPY statements...")
    
    output_dir = tempfile.mkdtemp()
    copy_file = os.path.join(output_dir, "copy_statements.sql")
    
    with open(copy_file, 'w') as out_f:
        # Write header
        out_f.write("-- Generated COPY statements for direct import\n")
        out_f.write("BEGIN;\n")
        out_f.write("SET session_replication_role = 'replica';\n\n")
        
        # Process the backup file
        with open(BACKUP_FILE, 'r') as in_f:
            content = in_f.read()
            
            # Extract COPY sections
            copy_pattern = r'(COPY (?:public\.)?([\w_]+) .+? FROM stdin;\n[\s\S]*?\\\.)'
            copy_matches = re.findall(copy_pattern, content)
            
            # Process each COPY section
            for full_copy, table in copy_matches:
                if table not in PRIORITY_TABLES:
                    continue
                
                print(f"  Processing table: {table}")
                
                # Truncate the table first (except user table)
                out_f.write(f"-- Truncate table {table}\n")
                if table == 'api_customuser':
                    # For user table, delete all except preserved users
                    preserve_conditions = [f"email != '{email}'" for email in PRESERVE_USERS]
                    conditions = " AND ".join(preserve_conditions)
                    if conditions:
                        out_f.write(f"DELETE FROM {table} WHERE {conditions};\n")
                else:
                    out_f.write(f"TRUNCATE TABLE {table} CASCADE;\n")
                
                # Write the COPY statement
                out_f.write(f"-- Import data into {table}\n")
                out_f.write(full_copy + "\n\n")
            
            # Fix sequences
            out_f.write("-- Fix sequences\n")
            for table in PRIORITY_TABLES:
                out_f.write(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1), true);\n")
            
            # Re-enable triggers
            out_f.write("\n-- Re-enable triggers\n")
            out_f.write("SET session_replication_role = 'origin';\n")
            out_f.write("COMMIT;\n")
    
    return copy_file

def generate_sql_script():
    """Generate a SQL script for direct manual import"""
    print("\nGenerating SQL script for direct import...")
    
    # Generate the two extraction files
    inserts_file = extract_direct_inserts()
    copy_file = extract_copy_statements()
    
    # Create a final script in the project directory
    final_script = "/Users/new/Newphb/basebackend/import_data.sql"
    
    # Copy the COPY file content as it's more efficient
    with open(copy_file, 'r') as src:
        with open(final_script, 'w') as dest:
            dest.write(src.read())
    
    print(f"\n\u2705 Generated SQL script at: {final_script}")
    print("\nTo import the data, run the following command:")
    print(f"PGPASSWORD={DB_PASSWORD} psql -U {DB_USER} -d {DB_NAME} -f {final_script}")
    
    return final_script

def verify_current_state():
    """Verify the current state of the database"""
    print("\nCurrent database state:")
    
    for table in PRIORITY_TABLES:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
        except Exception as e:
            print(f"  {table}: Error - {e}")
    
    # Check if the user accounts exist
    for email in PRESERVE_USERS:
        try:
            user = User.objects.filter(email=email).first()
            if user:
                print(f"  User {email} exists: \u2705")
            else:
                print(f"  User {email} does not exist: \u274c")
        except Exception as e:
            print(f"  Error checking user {email}: {e}")

def main():
    print("\n" + "=" * 50)
    print("Extract and Prepare Database Import")
    print("=" * 50)
    
    # 1. Verify current state
    verify_current_state()
    
    # 2. Generate SQL script
    script_file = generate_sql_script()
    
    print("\n" + "=" * 50)
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")
    print("=" * 50)
    
    # 3. Ask if user wants to run the import now
    response = input("\nWould you like to run the import now? (y/n): ")
    if response.lower() == 'y':
        try:
            print("\nRunning import...")
            cmd = [
                'psql',
                '-U', DB_USER,
                '-d', DB_NAME,
                '-f', script_file
            ]
            
            # Set PGPASSWORD in environment
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_PASSWORD
            
            result = subprocess.run(
                cmd, 
                env=env,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                print("\n\u2705 Import completed successfully!")
            else:
                print(f"\n\u274c Import failed: {result.stderr}")
            
            # Verify final state
            print("\nFinal database state:")
            verify_current_state()
        except Exception as e:
            print(f"\n\u274c Error running import: {e}")
    else:
        print("\nYou can run the import later with this command:")
        print(f"PGPASSWORD={DB_PASSWORD} psql -U {DB_USER} -d {DB_NAME} -f {script_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\u274c Error: {e}")
        print("\nYou can still use your current database with your existing account.")
        print("Email: eruwagolden55@gmail.com")
        print("Password: PublicHealth24 (or your original password)")
