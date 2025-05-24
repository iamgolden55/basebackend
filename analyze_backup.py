#!/usr/bin/env python
import os
import re

# Path to SQL backup file
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

def analyze_backup_structure():
    """Analyze the structure of the backup file to determine its format"""
    print("Analyzing backup file structure...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for table creation patterns
    create_tables = re.findall(r'CREATE TABLE ([\w_]+)', content)
    print(f"Found {len(create_tables)} CREATE TABLE statements")
    
    # Look for COPY statements
    copy_statements = re.findall(r'COPY ([\w_]+)', content)
    print(f"Found {len(copy_statements)} COPY statements")
    
    # Look for INSERT statements
    insert_statements = re.findall(r'INSERT INTO ([\w_]+)', content)
    print(f"Found {len(insert_statements)} INSERT statements")
    
    # Sample a few important tables
    tables_to_check = ['api_customuser', 'api_hospital', 'api_doctor', 'api_department', 'api_medicalrecord']
    for table in tables_to_check:
        # Check COPY format
        copy_pattern = f"COPY {table} \\((.+?)\\) FROM stdin;"
        copy_match = re.search(copy_pattern, content)
        if copy_match:
            columns = copy_match.group(1).split(', ')
            print(f"\nTable {table} COPY format:")
            print(f"Columns: {', '.join(columns)}")
            
            # Get a sample of data if available
            data_pattern = f"COPY {table} .*?FROM stdin;\\n([\\s\\S]*?)\\\\\\."
            data_match = re.search(data_pattern, content)
            if data_match:
                data_lines = data_match.group(1).strip().split('\n')
                print(f"Data rows: {len(data_lines)}")
                if data_lines:
                    print(f"Sample row: {data_lines[0]}")
        
        # Check INSERT format
        insert_pattern = f"INSERT INTO {table}.*?VALUES \\((.+?)\\);"
        insert_match = re.search(insert_pattern, content)
        if insert_match:
            print(f"\nTable {table} INSERT format:")
            print(f"Sample values: {insert_match.group(1)}")

def extract_key_records():
    """Extract key records from the backup file"""
    print("\nExtracting key records from backup file...")
    
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for specific data of interest
    # 1. Find your user account
    user_pattern = r"INSERT INTO api_customuser.*?VALUES \(.*?'eruwagolden55@gmail\.com'.*?\);"
    user_match = re.search(user_pattern, content)
    if user_match:
        print("\nFound your user account in INSERT statement:")
        print(user_match.group(0))
    
    # 2. Find any hospital records
    hospital_pattern = r"INSERT INTO api_hospital.*?VALUES \((.+?)\);"
    hospital_matches = re.findall(hospital_pattern, content)
    if hospital_matches:
        print(f"\nFound {len(hospital_matches)} hospital records:")
        for i, match in enumerate(hospital_matches[:3]):  # Show first 3
            print(f"Hospital {i+1}: {match}")
    
    # 3. Find any department records
    dept_pattern = r"INSERT INTO api_department.*?VALUES \((.+?)\);"
    dept_matches = re.findall(dept_pattern, content)
    if dept_matches:
        print(f"\nFound {len(dept_matches)} department records:")
        for i, match in enumerate(dept_matches[:3]):  # Show first 3
            print(f"Department {i+1}: {match}")
    
    # 4. Find any doctor records
    doctor_pattern = r"INSERT INTO api_doctor.*?VALUES \((.+?)\);"
    doctor_matches = re.findall(doctor_pattern, content)
    if doctor_matches:
        print(f"\nFound {len(doctor_matches)} doctor records:")
        for i, match in enumerate(doctor_matches[:3]):  # Show first 3
            print(f"Doctor {i+1}: {match}")

def main():
    print("\n===============================================")
    print("SQL Backup File Analysis")
    print("===============================================\n")
    
    analyze_backup_structure()
    extract_key_records()
    
    print("\n===============================================")
    print("Based on this analysis, we can create a more targeted")
    print("import script to extract the specific data you need.")
    print("===============================================")

if __name__ == "__main__":
    main()
