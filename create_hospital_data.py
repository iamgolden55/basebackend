# Script to create essential hospital data
import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import transaction
from api.models import Hospital, Department
from api.models.medical.hospital_auth import HospitalAdmin
from api.models.medical.medication import MedicationCatalog

def create_hospital_data():
    """Create hospital, departments, admin, and medication data"""
    with transaction.atomic():
        try:
            # Create sample hospital
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
    """Check the state of the database"""
    print("\nDatabase State:")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    print(f"Medication Catalog: {MedicationCatalog.objects.count()}")

def main():
    print("Creating hospital data for testing...")
    
    # First check current state
    print("Current database state:")
    check_database_state()
    
    # Create hospital data
    if create_hospital_data():
        print("\n✅ Successfully created hospital data!")
    else:
        print("\n❌ Failed to create hospital data")
    
    # Check final state
    print("\nFinal database state:")
    check_database_state()
    
    print("\n" + "=" * 50)
    print("Hospital admin account created:")
    print("Email: admin@stnicholas.com")
    print("Password: SecureAdmin2024")
    print("")
    print("This account uses the special hospital admin secure login flow with:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA")
    print("4. Enhanced security with trusted device tracking")
    print("=" * 50)

if __name__ == "__main__":
    main()
