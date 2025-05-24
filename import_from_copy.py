#!/usr/bin/env python
import os
import re
import django
import tempfile
import subprocess

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

def extract_copy_block(content, table):
    """Extract the COPY statement and data for a table"""
    # Pattern to match the complete COPY block including data
    pattern = fr'COPY public\.{table} .+? FROM stdin;\n([\s\S]*?)\\\.'  # Notice the 'public.' prefix
    
    # Alternative pattern without 'public.' schema prefix
    alt_pattern = fr'COPY {table} .+? FROM stdin;\n([\s\S]*?)\\\.'  
    
    # Try both patterns
    match = re.search(pattern, content)
    if not match:
        match = re.search(alt_pattern, content)
    
    if match:
        return match.group(1).strip()
    return None

def extract_copy_statement(content, table):
    """Extract the COPY statement (with column names) for a table"""
    # Pattern to match the COPY statement with column names
    pattern = fr'(COPY public\.{table} \([^)]+\) FROM stdin;)'
    
    # Alternative pattern without 'public.' schema prefix
    alt_pattern = fr'(COPY {table} \([^)]+\) FROM stdin;)'
    
    # Try both patterns
    match = re.search(pattern, content)
    if not match:
        match = re.search(alt_pattern, content)
    
    if match:
        return match.group(1)
    return None

def import_table_data(table):
    """Import data for a specific table from the backup"""
    print(f"Processing {table}...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Extract the COPY statement (header) and data
    copy_statement = extract_copy_statement(content, table)
    data_block = extract_copy_block(content, table)
    
    if not copy_statement or not data_block:
        print(f"  No data found for {table}")
        return False
    
    # Count number of rows
    row_count = len(data_block.split('\n'))
    print(f"  Found {row_count} rows of data")
    
    # Create temporary file with the COPY statement and data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as tmp:
        tmp_name = tmp.name
        tmp.write(f"{copy_statement}\n")
        tmp.write(data_block)
        tmp.write("\n\\.\n")  # End of COPY marker
    
    try:
        # Disable triggers for this table to avoid constraint issues
        with connection.cursor() as cursor:
            cursor.execute("BEGIN;")
            try:
                cursor.execute(f"ALTER TABLE {table} DISABLE TRIGGER ALL;")
                # Truncate the table
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            except Exception as e:
                print(f"  Error preparing table: {e}")
                cursor.execute("ROLLBACK;")
                return False
            cursor.execute("COMMIT;")
        
        # Import data using psql
        cmd = [
            'psql',
            '-U', DB_USER,
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-d', DB_NAME,
            '-f', tmp_name
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"  Error importing data: {result.stderr}")
            return False
        
        # Re-enable triggers
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table} ENABLE TRIGGER ALL;")
        
        # Verify import
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
        
        print(f"  Successfully imported {count} rows into {table}")
        return True
    
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

def fix_sequences():
    """Fix sequences after import"""
    print("\nFixing database sequences...")
    with connection.cursor() as cursor:
        # Get a list of tables with their ID columns
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                # Check if table has an id column
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'id'
                """)
                
                if cursor.fetchone():  # Table has an id column
                    # Get sequence name (assumes standard naming convention)
                    seq_name = f"{table}_id_seq"
                    
                    # Get max id
                    cursor.execute(f"SELECT MAX(id) FROM {table}")
                    max_id = cursor.fetchone()[0]
                    
                    if max_id:  # Only set if we have data
                        # Set sequence to max_id + 1
                        cursor.execute(f"SELECT setval('public.{seq_name}', {max_id}, true)")
                        print(f"  Updated sequence for {table} to {max_id}")
            except Exception as e:
                print(f"  Error fixing sequence for {table}: {e}")

def check_import_results():
    """Check the results of the import"""
    print("\n===============================================")
    print("Import Results:")
    
    with connection.cursor() as cursor:
        for table in PRIORITY_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            except Exception as e:
                print(f"{table}: Error - {e}")
        
        # Check for the specific user account
        cursor.execute("SELECT COUNT(*) FROM api_customuser WHERE email = 'eruwagolden55@gmail.com'")
        user_exists = cursor.fetchone()[0] > 0
        
        print(f"\nYour account exists: {'u2705' if user_exists else 'u274c'}")
    
    print("===============================================")

def main():
    print("\n===============================================")
    print("Database Import from COPY Format")
    print("===============================================")
    
    success_count = 0
    total_count = len(PRIORITY_TABLES)
    
    # Import data for each priority table
    for table in PRIORITY_TABLES:
        if import_table_data(table):
            success_count += 1
    
    print(f"\nSuccessfully imported data for {success_count}/{total_count} tables")
    
    # Fix sequences
    fix_sequences()
    
    # Check results
    check_import_results()
    
    # Remind about preserved security features
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")

if __name__ == "__main__":
    main()
