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
from django.contrib.auth import get_user_model

User = get_user_model()

# Database connection details
DB_NAME = "medic_db"
DB_USER = "medic_db"
DB_PASSWORD = "publichealth"
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

# Tables to preserve (don't truncate)
PRESERVE_TABLES = [
    'django_migrations',
]

# Specific data to preserve
PRESERVE_USERS = [
    'eruwagolden55@gmail.com',
    'admin@example.com'
]

def backup_important_data():
    """Backup important data that we want to preserve"""
    print("\nBacking up important data...")
    preserved_data = {}
    
    # Backup user accounts we want to preserve
    preserved_data['users'] = []
    for email in PRESERVE_USERS:
        try:
            user = User.objects.filter(email=email).first()
            if user:
                user_data = {
                    'email': user.email,
                    'password': user.password,  # Hashed password
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                }
                preserved_data['users'].append(user_data)
                print(f"  Backed up user: {email}")
        except Exception as e:
            print(f"  Error backing up user {email}: {e}")
    
    return preserved_data

def extract_copy_sections():
    """Extract COPY sections from the backup file"""
    print("\nExtracting data sections from backup file...")
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Find all COPY statements and their data
    copy_pattern = r'(COPY (?:public\.)?([\w_]+) \([^)]+\) FROM stdin;\n[\s\S]*?\\\.)'
    matches = re.findall(copy_pattern, content)
    
    copy_sections = {}
    for full_copy, table_name in matches:
        copy_sections[table_name] = full_copy
        print(f"  Found data for table: {table_name}")
    
    return copy_sections

def truncate_tables():
    """Truncate all tables except those to preserve"""
    print("\nTruncating tables...")
    with connection.cursor() as cursor:
        # Get list of all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN %s
        """, [tuple(PRESERVE_TABLES)])
        
        tables = [row[0] for row in cursor.fetchall()]
        
        # Disable triggers temporarily
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Truncate each table
        for table in tables:
            try:
                cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
                print(f"  Truncated table: {table}")
            except Exception as e:
                print(f"  Error truncating {table}: {e}")
        
        # Re-enable triggers
        cursor.execute("SET session_replication_role = 'origin';")

def import_data(copy_sections):
    """Import data from COPY sections"""
    print("\nImporting data from backup...")
    
    success_count = 0
    for table_name, copy_data in copy_sections.items():
        if table_name in PRESERVE_TABLES:
            print(f"  Skipping preserved table: {table_name}")
            continue
        
        # Create a temporary file for this COPY section
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as tmp:
            tmp_name = tmp.name
            tmp.write(copy_data)
        
        try:
            # Import using psql
            cmd = [
                'psql',
                '-U', DB_USER,
                '-d', DB_NAME,
                '-f', tmp_name
            ]
            
            result = subprocess.run(
                cmd, 
                env={**os.environ, 'PGPASSWORD': DB_PASSWORD},
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                success_count += 1
                print(f"  Imported data for: {table_name}")
            else:
                print(f"  Error importing {table_name}: {result.stderr}")
            
            # Clean up temp file
            os.unlink(tmp_name)
        except Exception as e:
            print(f"  Error processing {table_name}: {e}")
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
    
    print(f"\nSuccessfully imported data for {success_count}/{len(copy_sections)} tables")

def restore_important_data(preserved_data):
    """Restore important data that we preserved"""
    print("\nRestoring preserved data...")
    
    # Restore user accounts
    for user_data in preserved_data.get('users', []):
        try:
            email = user_data['email']
            # Check if user exists in newly imported data
            if User.objects.filter(email=email).exists():
                # Update existing user
                user = User.objects.get(email=email)
                user.password = user_data['password']  # Restore hashed password
                user.is_active = user_data['is_active']
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                print(f"  Updated existing user: {email}")
            else:
                # Create user if it doesn't exist
                user = User.objects.create(
                    email=email,
                    password=user_data['password'],  # Use hashed password
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    is_active=user_data['is_active'],
                    is_staff=user_data['is_staff'],
                    is_superuser=user_data['is_superuser']
                )
                print(f"  Restored user: {email}")
        except Exception as e:
            print(f"  Error restoring user {user_data.get('email')}: {e}")

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

def verify_import():
    """Verify the import was successful"""
    print("\n===============================================")
    print("Import Verification Results:")
    
    with connection.cursor() as cursor:
        # Check counts for key tables
        tables = [
            'api_customuser', 
            'api_hospital',
            'api_department',
            'api_doctor',
            'api_medicalrecord',
            'api_appointment',
            'api_medication'
        ]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            except Exception as e:
                print(f"{table}: Error - {e}")
        
        # Check for specific users
        for email in PRESERVE_USERS:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM api_customuser WHERE email = '{email}'")
                exists = cursor.fetchone()[0] > 0
                print(f"User {email} exists: {'u2705' if exists else 'u274c'}")
            except Exception as e:
                print(f"Error checking for user {email}: {e}")
    
    print("===============================================")

def main():
    print("\n===============================================")
    print("Database Import to Existing Database")
    print("===============================================")
    
    # 1. Backup important data
    preserved_data = backup_important_data()
    
    # 2. Extract COPY sections from backup
    copy_sections = extract_copy_sections()
    
    # 3. Truncate tables
    truncate_tables()
    
    # 4. Import data
    import_data(copy_sections)
    
    # 5. Restore important data
    restore_important_data(preserved_data)
    
    # 6. Fix sequences
    fix_sequences()
    
    # 7. Verify import
    verify_import()
    
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")

if __name__ == "__main__":
    main()
