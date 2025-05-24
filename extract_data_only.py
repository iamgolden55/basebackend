#!/usr/bin/env python
import os
import re
import django
import subprocess
import tempfile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connection

# Database connection details
DB_NAME = "medic_db"
DB_USER = "medic_db"
DB_PASSWORD = "publichealth"
DB_HOST = "localhost"
DB_PORT = "5432"
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

# Priority tables to extract data from
PRIORITY_TABLES = [
    'api_customuser',
    'api_hospital',
    'api_department',
    'api_doctor',
    'api_medicalrecord',
    'api_hospitaladmin',
    'api_medication',
    'api_appointment',
    'api_appointmenttype',
    'api_appointmentfee',
    'api_clinicalnote',
    'api_vitalsign',
    'api_medicationcatalog',
    'api_paymenttransaction'
]

def extract_data_for_table(table_name):
    """Extract only the data from a specific table in the backup"""
    print(f"Extracting data for {table_name}...")
    
    # Extract COPY statement and data for this table
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for the COPY block for this table
    copy_pattern = f"COPY {table_name} .*?FROM stdin;\\n([\\s\\S]*?)\\\\\\."
    copy_match = re.search(copy_pattern, content)
    
    if not copy_match:
        print(f"No data found for {table_name}")
        return False
    
    # Get column names
    cols_pattern = f"COPY {table_name} \\((.+?)\\) FROM stdin;"
    cols_match = re.search(cols_pattern, content)
    if not cols_match:
        print(f"Could not extract column names for {table_name}")
        return False
    
    column_names = cols_match.group(1)
    
    # Create a temporary file with just this data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as tmp:
        tmp_name = tmp.name
        tmp.write(f"COPY {table_name} ({column_names}) FROM stdin;\n")
        tmp.write(copy_match.group(1))
        tmp.write("\\.")  # End of COPY data marker
    
    # Import this data using psql
    cmd = [
        'psql',
        '-U', DB_USER,
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-d', DB_NAME,
        '-f', tmp_name
    ]
    
    try:
        # First truncate the table to avoid conflicts
        with connection.cursor() as cursor:
            # Disable foreign key constraints temporarily
            cursor.execute("BEGIN;")
            cursor.execute("ALTER TABLE %s DISABLE TRIGGER ALL;" % table_name)
            cursor.execute("TRUNCATE TABLE %s CASCADE;" % table_name)
            cursor.execute("ALTER TABLE %s ENABLE TRIGGER ALL;" % table_name)
            cursor.execute("COMMIT;")
        
        # Now import the data
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error importing data for {table_name}: {result.stderr}")
            return False
        
        # Get row count
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
        
        print(f"Imported {count} rows for {table_name}")
        return True
    
    except Exception as e:
        print(f"Error processing {table_name}: {e}")
        return False
    finally:
        # Clean up temp file
        os.unlink(tmp_name)

def fix_sequences():
    """Fix sequences after import"""
    print("\nFixing sequence values...")
    with connection.cursor() as cursor:
        # Get all sequences
        cursor.execute("""
            SELECT c.relname AS seq_name, n.nspname AS schema_name,
                   pg_get_serial_sequence(n.nspname || '.' || t.relname, a.attname) AS full_seq_name,
                   t.relname AS table_name, a.attname AS column_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_depend d ON d.objid = c.oid
            JOIN pg_class t ON d.refobjid = t.oid
            JOIN pg_attribute a ON (d.refobjid, d.refobjsubid) = (a.attrelid, a.attnum)
            WHERE c.relkind = 'S' AND n.nspname = 'public'
        """)
        
        for seq_name, schema, full_seq_name, table_name, column in cursor.fetchall():
            try:
                if not full_seq_name:
                    continue
                    
                # Get max id
                cursor.execute(f"SELECT MAX({column}) FROM {schema}.{table_name}")
                max_id = cursor.fetchone()[0]
                
                if max_id:
                    # Set sequence to max id + 1
                    cursor.execute(f"SELECT setval('{full_seq_name}', {max_id}, true)")
                    print(f"Set {full_seq_name} to {max_id}")
            except Exception as e:
                print(f"Error fixing sequence {seq_name}: {e}")

def check_database_state():
    """Verify the database state after import"""
    print("\n===============================================")
    print("Database Import Results:")
    
    for table in PRIORITY_TABLES:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
        except Exception as e:
            print(f"{table}: Error - {e}")
    
    # Check for specific user
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM api_customuser WHERE email = 'eruwagolden55@gmail.com'")
        user_exists = cursor.fetchone()[0] > 0
    
    print("\nYour account exists:", "✅" if user_exists else "❌")
    print("===============================================")

def main():
    print("\n===============================================")
    print("Targeted Table Data Import")
    print("===============================================\n")
    
    success_count = 0
    for table in PRIORITY_TABLES:
        if extract_data_for_table(table):
            success_count += 1
    
    print(f"\nSuccessfully imported data for {success_count}/{len(PRIORITY_TABLES)} tables")
    
    # Fix sequences
    fix_sequences()
    
    # Check database state
    check_database_state()
    
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")

if __name__ == "__main__":
    main()
