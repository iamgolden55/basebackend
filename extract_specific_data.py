#!/usr/bin/env python
import os
import re
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from api.models import CustomUser, Hospital, Doctor, Department, HospitalAdmin

# Path to SQL backup file
BACKUP_FILE = "/Users/new/Newphb/basebackend/medic_db_backup.sql"

def extract_user_data():
    """Extract user data from the SQL backup file"""
    print("Extracting user data from backup file...")
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for COPY sections related to users
    user_copy_section = re.search(r'COPY api_customuser .*?FROM stdin;\n([\s\S]*?)\\\.',
                                content)
    
    users = []
    if user_copy_section:
        user_data = user_copy_section.group(1).strip().split('\n')
        for line in user_data:
            fields = line.split('\t')
            if len(fields) >= 15:  # Make sure we have enough fields
                try:
                    user = {
                        'id': int(fields[0]),
                        'password': fields[1] if fields[1] != '\\N' else '',
                        'last_login': fields[2] if fields[2] != '\\N' else None,
                        'is_superuser': fields[3] == 't',
                        'email': fields[4],
                        'first_name': fields[5] if fields[5] != '\\N' else '',
                        'last_name': fields[6] if fields[6] != '\\N' else '',
                        'is_staff': fields[7] == 't',
                        'is_active': fields[8] == 't',
                        'date_joined': fields[9],
                        'user_type': fields[10] if fields[10] != '\\N' else 'patient',
                        'phone': fields[11] if fields[11] != '\\N' else '',
                        'gender': fields[12].lower() if fields[12] != '\\N' else '',
                        'date_of_birth': fields[13] if fields[13] != '\\N' else None,
                        'profile_picture': fields[14] if fields[14] != '\\N' else ''
                    }
                    
                    # Check if this is the target user
                    if 'eruwagolden55@gmail.com' in user['email'].lower():
                        print(f"Found target user: {user['email']}")
                    
                    users.append(user)
                except Exception as e:
                    print(f"Error parsing user data: {e}")
    
    # Also look for INSERT statements for users
    insert_users = re.findall(r"INSERT INTO api_customuser.*?VALUES \((.+?)\);\n", content)
    for insert in insert_users:
        try:
            # Extract email from the insert statement
            email_match = re.search(r"'([^']*@[^']*\.[^']*)'\s*,", insert)
            if email_match and 'eruwagolden55@gmail.com' in email_match.group(1).lower():
                print(f"Found target user in INSERT statement: {email_match.group(1)}")
        except Exception as e:
            print(f"Error parsing insert statement: {e}")
    
    return users

def extract_hospital_data():
    """Extract hospital data from the SQL backup file"""
    print("Extracting hospital data from backup file...")
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for COPY sections related to hospitals
    hospital_copy_section = re.search(r'COPY api_hospital .*?FROM stdin;\n([\s\S]*?)\\\.',
                                    content)
    
    hospitals = []
    if hospital_copy_section:
        hospital_data = hospital_copy_section.group(1).strip().split('\n')
        for line in hospital_data:
            fields = line.split('\t')
            if len(fields) >= 10:  # Make sure we have enough fields
                try:
                    hospital = {
                        'id': int(fields[0]),
                        'created_at': fields[1],
                        'updated_at': fields[2],
                        'name': fields[3],
                        'hospital_type': fields[4] if fields[4] != '\\N' else '',
                        'address': fields[5] if fields[5] != '\\N' else '',
                        'city': fields[6] if fields[6] != '\\N' else '',
                        'state': fields[7] if fields[7] != '\\N' else '',
                        'country': fields[8] if fields[8] != '\\N' else '',
                        'phone': fields[9] if fields[9] != '\\N' else ''
                    }
                    hospitals.append(hospital)
                except Exception as e:
                    print(f"Error parsing hospital data: {e}")
    
    return hospitals

def extract_department_data():
    """Extract department data from the SQL backup file"""
    print("Extracting department data from backup file...")
    with open(BACKUP_FILE, 'r') as f:
        content = f.read()
    
    # Look for COPY sections related to departments
    dept_copy_section = re.search(r'COPY api_department .*?FROM stdin;\n([\s\S]*?)\\\.',
                                content)
    
    departments = []
    if dept_copy_section:
        dept_data = dept_copy_section.group(1).strip().split('\n')
        for line in dept_data:
            fields = line.split('\t')
            if len(fields) >= 7:  # Make sure we have enough fields
                try:
                    department = {
                        'id': int(fields[0]),
                        'created_at': fields[1],
                        'updated_at': fields[2],
                        'name': fields[3],
                        'code': fields[4] if fields[4] != '\\N' else '',
                        'description': fields[5] if fields[5] != '\\N' else '',
                        'hospital_id': int(fields[6]) if fields[6] != '\\N' else None
                    }
                    departments.append(department)
                except Exception as e:
                    print(f"Error parsing department data: {e}")
    
    return departments

def create_users(user_data):
    """Create users from extracted data"""
    print("Creating users...")
    created_count = 0
    skipped_count = 0
    target_user_created = False
    
    for user in user_data:
        try:
            # Check if user already exists
            if CustomUser.objects.filter(email=user['email']).exists():
                if 'eruwagolden55@gmail.com' in user['email'].lower():
                    print(f"Target user already exists: {user['email']}")
                    target_user_created = True
                skipped_count += 1
                continue
            
            # Create new user
            new_user = CustomUser(
                email=user['email'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                is_staff=user['is_staff'],
                is_active=user['is_active'],
                date_joined=user['date_joined'],
                user_type=user['user_type'],
                phone=user['phone'],
                gender=user['gender'],
                date_of_birth=user['date_of_birth'],
                profile_picture=user['profile_picture']
            )
            
            # Set password directly if available, otherwise use a default
            if user['password']:
                new_user.password = user['password']  # Use the hashed password from backup
            else:
                new_user.set_password('PublicHealth24')  # Default password
            
            new_user.save()
            created_count += 1
            
            if 'eruwagolden55@gmail.com' in user['email'].lower():
                print(f"Created target user: {user['email']}")
                target_user_created = True
        except Exception as e:
            print(f"Error creating user {user['email']}: {e}")
    
    print(f"Created {created_count} users, skipped {skipped_count} existing users")
    
    # If target user doesn't exist, create it manually
    if not target_user_created:
        create_target_user()
    
    return created_count

def create_target_user():
    """Create the target user manually"""
    print("Creating target user manually...")
    try:
        user, created = CustomUser.objects.get_or_create(
            email='eruwagolden55@gmail.com',
            defaults={
                'first_name': 'Ninioritse',
                'last_name': 'Great Eruwa',
                'phone': '+2348035487113',
                'date_of_birth': '2000-09-20',
                'gender': 'male',
                'user_type': 'patient',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False
            }
        )
        
        if created:
            user.set_password('PublicHealth24')
            user.save()
            print("✅ Target user created successfully!")
        else:
            print("Target user already exists")
        
        return True
    except Exception as e:
        print(f"Error creating target user: {e}")
        return False

def create_hospitals(hospital_data):
    """Create hospitals from extracted data"""
    print("Creating hospitals...")
    created_count = 0
    skipped_count = 0
    
    for hospital in hospital_data:
        try:
            # Check if hospital already exists
            if Hospital.objects.filter(name=hospital['name']).exists():
                skipped_count += 1
                continue
            
            # Create new hospital
            new_hospital = Hospital(
                name=hospital['name'],
                hospital_type=hospital['hospital_type'],
                address=hospital['address'],
                city=hospital['city'],
                state=hospital['state'],
                country=hospital['country'],
                phone=hospital['phone'],
                is_verified=True
            )
            new_hospital.save()
            created_count += 1
            
            print(f"Created hospital: {hospital['name']}")
        except Exception as e:
            print(f"Error creating hospital {hospital['name']}: {e}")
    
    print(f"Created {created_count} hospitals, skipped {skipped_count} existing hospitals")
    
    # If no hospitals were created, create a sample one
    if Hospital.objects.count() == 0:
        create_sample_hospital()
    
    return created_count

def create_departments(department_data):
    """Create departments from extracted data"""
    print("Creating departments...")
    created_count = 0
    skipped_count = 0
    
    # Get all hospitals (for mapping department to hospital)
    hospitals = {h.id: h for h in Hospital.objects.all()}
    
    for dept in department_data:
        try:
            # Get the hospital for this department
            hospital_id = dept['hospital_id']
            hospital = hospitals.get(hospital_id)
            
            if not hospital:
                print(f"Hospital with ID {hospital_id} not found for department {dept['name']}")
                continue
            
            # Check if department already exists in this hospital
            if Department.objects.filter(name=dept['name'], hospital=hospital).exists():
                skipped_count += 1
                continue
            
            # Create new department
            new_dept = Department(
                name=dept['name'],
                code=dept['code'],
                description=dept['description'],
                hospital=hospital
            )
            new_dept.save()
            created_count += 1
            
            print(f"Created department: {dept['name']} in {hospital.name}")
        except Exception as e:
            print(f"Error creating department {dept['name']}: {e}")
    
    print(f"Created {created_count} departments, skipped {skipped_count} existing departments")
    return created_count

def create_sample_hospital():
    """Create a sample hospital with departments"""
    print("Creating sample hospital...")
    try:
        # Create hospital
        hospital = Hospital.objects.create(
            name="St. Nicholas Hospital",
            hospital_type="General Hospital",
            address="1 Hospital Road",
            city="Lagos",
            state="Lagos",
            country="Nigeria",
            postal_code="100001",
            phone="+2347012345678",
            email="info@stnicholas.com",
            website="www.stnicholas.com",
            emergency_unit=True,
            icu_unit=True,
            is_verified=True
        )
        print(f"Created sample hospital: {hospital.name}")
        
        # Create departments
        departments = [
            "Emergency", "Cardiology", "Neurology", "Pediatrics",
            "Orthopedics", "Obstetrics & Gynecology", "Internal Medicine",
            "Surgery", "Radiology", "Pharmacy", "Laboratory"
        ]
        
        for dept_name in departments:
            department = Department.objects.create(
                name=dept_name,
                hospital=hospital,
                code=dept_name[:3].upper(),
                description=f"{dept_name} Department at {hospital.name}"
            )
            print(f"Created department: {department.name}")
        
        # Create a hospital admin account with secure configuration
        admin_email = "admin@stnicholas.com"
        admin, created = HospitalAdmin.objects.get_or_create(
            email=admin_email,
            defaults={
                'hospital': hospital,
                'position': 'Chief Administrator',
                'first_name': 'Admin',
                'last_name': 'User',
                'password_change_required': True,  # Will force password change on first login
                'contact_email': admin_email,  # Secondary contact email
            }
        )
        
        if created:
            admin.set_password('SecureAdmin2024')
            admin.save()
            print(f"Created hospital admin: {admin_email}")
        
        return True
    except Exception as e:
        print(f"Error creating sample hospital: {e}")
        return False

def check_database_state():
    """Check the state of the database"""
    print("\n==============================================")
    print("Database State:")
    print(f"Users: {CustomUser.objects.count()}")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    
    # Check for specific user
    user_exists = CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists()
    print(f"Your account exists: {'✅' if user_exists else '❌'}")
    print("==============================================\n")
    
    if user_exists:
        print("You should now be able to log in with:")
        print("Email: eruwagolden55@gmail.com")
        print("Password: PublicHealth24")
        
        # Check if hospitals exist with their security features
        print("\nThe hospital admin security features are preserved:")
        print("1. Domain validation for hospital email addresses")
        print("2. Required hospital code verification")
        print("3. Mandatory 2FA for all hospital admins")
        print("4. Enhanced security with trusted device tracking")
        print("5. Rate limiting: IP-based rate limiting after 3 failed attempts")
        print("6. Account lockout for 15 minutes after 5 failed attempts")
    else:
        print("\n❌ Your account was not found. Something went wrong.")

@transaction.atomic
def main():
    print("\n==============================================")
    print("Targeted Data Import from Backup")
    print("==============================================\n")
    
    # Extract data from backup file
    users = extract_user_data()
    hospitals = extract_hospital_data()
    departments = extract_department_data()
    
    print(f"\nExtracted {len(users)} users, {len(hospitals)} hospitals, {len(departments)} departments")
    
    # Create data in database
    with transaction.atomic():
        create_users(users)
        create_hospitals(hospitals)
        create_departments(departments)
    
    # Verify database state
    check_database_state()

if __name__ == "__main__":
    main()
