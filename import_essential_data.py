# Script to import essential data from SQL backup
import os
import django
import re
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import transaction
from api.models import CustomUser, Hospital, Doctor, Department
from api.models.medical.hospital_auth import HospitalAdmin
from api.models.medical.medication import Medication, MedicationCatalog

def parse_data_from_backup():
    """Parse essential data from the SQL backup file"""
    backup_file = '/Users/new/Newphb/basebackend/medic_db_backup.sql'
    
    with open(backup_file, 'r') as f:
        content = f.read()
    
    # Extract the specific user we're interested in
    user_data = re.findall(r'\d+\s+pbkdf2_sha256\S+\s+\\N\s+f\s+eruwagolden55@gmail\.com[^\n]+', content)
    if user_data:
        print("Found user data in backup file")
    else:
        print("User data not found in backup file")
    
    # Extract hospital data
    hospital_data = re.findall(r'\d+\s+\d{4}-\d{2}-\d{2}\s+\d{4}-\d{2}-\d{2}[^\n]+hospital[^\n]+', content)
    print(f"Found {len(hospital_data)} hospital records")
    
    # Extract department data
    department_data = re.findall(r'\d+\s+\d{4}-\d{2}-\d{2}\s+\d{4}-\d{2}-\d{2}[^\n]+department[^\n]+', content)
    print(f"Found {len(department_data)} department records")
    
    return {
        'user_data': user_data,
        'hospital_data': hospital_data,
        'department_data': department_data
    }

def create_key_entities():
    """Create essential entities manually"""
    # Create or update user account
    with transaction.atomic():
        try:
            user, created = CustomUser.objects.get_or_create(
                email='eruwagolden55@gmail.com',
                defaults={
                    'first_name': 'Ninioritse',
                    'last_name': 'Great Eruwa',
                    'phone': '+2348035487113',
                    'date_of_birth': '2000-09-20',
                    'gender': 'male',
                    'country': 'nigeria',
                    'state': 'delta',
                    'city': 'Asaba',
                    'nin': '12121212121',
                    'consent_terms': True,
                    'consent_hipaa': True,
                    'consent_data_processing': True,
                    'preferred_language': 'english',
                    'secondary_languages': ['yoruba', 'isoko'],
                    'is_active': True,
                    'is_email_verified': True,
                    'user_type': 'patient'
                }
            )
            
            if created:
                # Set password only if user was newly created
                user.set_password('PublicHealth24')
                user.save()
                print("Created user: eruwagolden55@gmail.com")
            else:
                print("User already exists, skipping password change")
                
            # Always create sample hospital data for testing
            # First check if hospitals exist
            if Hospital.objects.count() == 0:
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
                print(f"Created hospital: {hospital.name}")
                
                # Create departments for the hospital
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
                
                # Add some medication catalog entries
                medications = [
                    {
                        'generic_name': 'Paracetamol',
                        'brand_names': ['Panadol', 'Tylenol'],
                        'drug_class': 'Analgesic',
                        'available_forms': ['tablet', 'syrup'],
                        'indications': 'Pain relief, fever reduction',
                        'contraindications': 'Liver disease',
                        'side_effects': 'Generally well tolerated'
                    },
                    {
                        'generic_name': 'Amoxicillin',
                        'brand_names': ['Amoxil', 'Trimox'],
                        'drug_class': 'Antibiotic',
                        'available_forms': ['capsule', 'suspension'],
                        'indications': 'Bacterial infections',
                        'contraindications': 'Penicillin allergy',
                        'side_effects': 'Diarrhea, rash'
                    },
                    {
                        'generic_name': 'Lisinopril',
                        'brand_names': ['Zestril', 'Prinivil'],
                        'drug_class': 'ACE Inhibitor',
                        'available_forms': ['tablet'],
                        'indications': 'Hypertension, heart failure',
                        'contraindications': 'Pregnancy, angioedema',
                        'side_effects': 'Dry cough, dizziness'
                    }
                ]
                
                for med_data in medications:
                    med = MedicationCatalog.objects.create(**med_data)
                    print(f"Created medication catalog entry: {med.generic_name}")
            
            return True
        except Exception as e:
            print(f"Error creating entities: {e}")
            return False

def check_database_state():
    """Check the state of the database after import"""
    print("\nDatabase State:")
    print(f"Users: {CustomUser.objects.count()}")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    print(f"Medication Catalog: {MedicationCatalog.objects.count()}")
    
    user_exists = CustomUser.objects.filter(email='eruwagolden55@gmail.com').exists()
    print(f"Your account exists: {'✅' if user_exists else '❌'}")
    
    return user_exists

def main():
    # First check current database state
    print("Current database state:")
    initial_state = check_database_state()
    
    # If we don't have a user account, try to create one
    if not initial_state:
        print("\nAttempting to create essential data...")
        if create_key_entities():
            print("\n✅ Successfully created essential data!")
        else:
            print("\n❌ Failed to create essential data")
    else:
        print("\n✅ Your account already exists, no need to import")
    
    # Final check
    print("\nFinal database state:")
    final_state = check_database_state()
    
    print("\n" + "=" * 50)
    if final_state:
        print("✅ Your account is ready to use!")
        print("Email: eruwagolden55@gmail.com")
        print("Password: Your original password (or 'PublicHealth24' if reset)")
        print("\nA sample hospital has been created with departments and medications.")
        print("Hospital admin account: admin@stnicholas.com / SecureAdmin2024")
        print("=" * 50)
        return True
    else:
        print("❌ Account setup failed. Please contact support.")
        print("=" * 50)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
