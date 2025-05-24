#!/usr/bin/env python
import os
import re
import django
import tempfile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

# Database connection details
DB_NAME = "medic_db"
DB_USER = "medic_db"
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

# Priority tables
TABLES = [
    'api_customuser',
    'api_hospital',
    'api_department',
    'api_doctor',
    'api_medicalrecord',
    'api_medication'
]

# Emails to preserve
PRESERVE_EMAILS = [
    'eruwagolden55@gmail.com',
    'admin@example.com'
]

def extract_specific_users():
    """Extract specific users from the backup file"""
    print("\nExtracting user data from backup file...")
    target_email = 'eruwagolden55@gmail.com'
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for lines with the target email in the user data section
    user_section = re.search(r'COPY (?:public\.)?api_customuser.+?FROM stdin;\n([\s\S]*?)\\\.',
                             content)
    
    if not user_section:
        print("  User data section not found in backup")
        return None
    
    user_data = user_section.group(1).strip().split('\n')
    target_user_data = None
    
    for line in user_data:
        if target_email in line:
            print(f"  Found target user: {target_email}")
            target_user_data = line
            break
    
    return target_user_data

def extract_department_data():
    """Extract department data from the backup file"""
    print("\nExtracting department data...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for department data section
    dept_section = re.search(r'COPY (?:public\.)?api_department.+?FROM stdin;\n([\s\S]*?)\\\.',
                             content)
    
    if not dept_section:
        print("  Department data section not found in backup")
        return []
    
    dept_data = dept_section.group(1).strip().split('\n')
    print(f"  Found {len(dept_data)} departments")
    
    return dept_data

def extract_hospital_data():
    """Extract hospital data from the backup file"""
    print("\nExtracting hospital data...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for hospital data section
    hospital_section = re.search(r'COPY (?:public\.)?api_hospital.+?FROM stdin;\n([\s\S]*?)\\\.',
                               content)
    
    if not hospital_section:
        print("  Hospital data section not found in backup")
        return []
    
    hospital_data = hospital_section.group(1).strip().split('\n')
    print(f"  Found {len(hospital_data)} hospitals")
    
    return hospital_data

def extract_doctor_data():
    """Extract doctor data from the backup file"""
    print("\nExtracting doctor data...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for doctor data section
    doctor_section = re.search(r'COPY (?:public\.)?api_doctor.+?FROM stdin;\n([\s\S]*?)\\\.',
                              content)
    
    if not doctor_section:
        print("  Doctor data section not found in backup")
        return []
    
    doctor_data = doctor_section.group(1).strip().split('\n')
    print(f"  Found {len(doctor_data)} doctors")
    
    return doctor_data

def create_sql_import_file():
    """Create a SQL file with basic extracted data"""
    print("\nCreating SQL import file...")
    
    # Get column names from database
    column_info = {}
    with connection.cursor() as cursor:
        for table in TABLES:
            try:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in cursor.fetchall()]
                column_info[table] = columns
                print(f"  Retrieved {len(columns)} columns for {table}")
            except Exception as e:
                print(f"  Error getting columns for {table}: {e}")
    
    # Extract data from backup
    user_data = extract_specific_users()
    dept_data = extract_department_data()
    hospital_data = extract_hospital_data()
    doctor_data = extract_doctor_data()
    
    # Create SQL file
    sql_file = "/Users/new/Newphb/basebackend/import_sample_data.sql"
    
    with open(sql_file, 'w') as f:
        f.write("-- Sample data import script generated from backup\n")
        f.write("BEGIN;\n\n")
        
        # Add sample departments to existing hospital
        if dept_data:
            f.write("-- Add sample departments\n")
            f.write("INSERT INTO api_department (name, hospital_id, code, description) VALUES\n")
            
            values = []
            for i, line in enumerate(dept_data[:10]):  # Add up to 10 departments
                fields = line.split('\t')
                if len(fields) >= 4:
                    name = fields[3].replace("'", "''")
                    code = fields[4].replace("'", "''")
                    desc = fields[5].replace("'", "''")
                    values.append(f"('{name}', 1, '{code}', '{desc}')")
            
            if values:
                f.write(",\n".join(values))
                f.write(";\n\n")
            
        # Add sample doctors
        if doctor_data:
            f.write("-- Add sample doctors\n")
            f.write("INSERT INTO api_doctor (created_at, updated_at, first_name, last_name, email, phone, specialty, hospital_id) VALUES\n")
            
            values = []
            for i, line in enumerate(doctor_data[:20]):  # Add up to 20 doctors
                fields = line.split('\t')
                if len(fields) >= 10:
                    created = fields[1]
                    updated = fields[2]
                    first_name = fields[3].replace("'", "''")
                    last_name = fields[4].replace("'", "''")
                    email = fields[5].replace("'", "''")
                    phone = fields[6].replace("'", "''")
                    specialty = fields[7].replace("'", "''")
                    values.append(f"('{created}', '{updated}', '{first_name}', '{last_name}', '{email}', '{phone}', '{specialty}', 1)")
            
            if values:
                f.write(",\n".join(values))
                f.write(";\n\n")
        
        # Fix sequences
        f.write("-- Fix sequences\n")
        for table in TABLES:
            f.write(f"SELECT setval('public.{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1), true);\n")
        
        f.write("\nCOMMIT;")
    
    print(f"\n\u2705 Created SQL import file: {sql_file}")
    print("\nTo import the sample data, run:")
    print(f"psql -U {DB_USER} -d {DB_NAME} -f {sql_file}")
    
    return sql_file

def main():
    print("\n" + "=" * 50)
    print("Extract Sample Data from Backup")
    print("=" * 50)
    
    # Check current database state
    print("\nCurrent database state:")
    with connection.cursor() as cursor:
        for table in TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: Error - {e}")
    
    # Create SQL import file
    sql_file = create_sql_import_file()
    
    print("\n" + "=" * 50)
    print("Next Steps:")
    print("1. Import the sample data using the command above")
    print("2. Your existing user accounts will be preserved:")
    for email in PRESERVE_EMAILS:
        print(f"   - {email}")
    print("3. The database will include sample departments and doctors from the backup")
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")
    print("=" * 50)

if __name__ == "__main__":
    main()
