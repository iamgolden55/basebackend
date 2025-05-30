# Script to create Abuja hospital data with required staff
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
from api.models.user.custom_user import CustomUser
from django.utils import timezone
import traceback

def create_abuja_hospital_with_staff():
    """Create Abuja hospital, departments, admin, staff, and medication data"""
    with transaction.atomic():
        try:
            # Check if the hospital already exists
            existing_hospital = Hospital.objects.filter(name="Abuja General Hospital").first()
            if existing_hospital:
                hospital = existing_hospital
                print(f"Using existing hospital: {hospital.name}")
            else:
                # Create Abuja hospital
                hospital = Hospital.objects.create(
                    name="Abuja General Hospital",
                    hospital_type="General Hospital",
                    address="123 Federal Capital Territory",
                    city="Abuja",
                    state="FCT",
                    country="Nigeria",
                    postal_code="900001",
                    phone="+2348012345678",
                    email="info@abujageneralhospital.com",
                    website="www.abujageneralhospital.com",
                    emergency_unit=True,
                    icu_unit=True,
                    is_verified=True
                )
                print(f"Created hospital: {hospital.name}")
            
            # Create departments for the hospital
            departments = [
                "Emergency", "Cardiology", "Neurology", "Pediatrics",
                "Orthopedics", "Surgery"
            ]
            
            created_departments = []
            for dept_name in departments:
                dept, created = Department.objects.get_or_create(
                    name=dept_name,
                    hospital=hospital,
                    defaults={
                        'code': dept_name[:3].upper(),
                        'description': f"{dept_name} Department at {hospital.name}"
                    }
                )
                if created:
                    created_departments.append(dept)
                    print(f"Created department: {dept.name}")
            
            # Create a hospital admin account
            admin_email = "admin@abujageneralhospital.com"
            admin, created = HospitalAdmin.objects.get_or_create(
                email=admin_email,
                defaults={
                    'hospital': hospital,
                    'position': 'Chief Administrator',
                    'name': 'Abuja Admin',
                    'password_change_required': True,
                    'contact_email': admin_email,
                }
            )
            
            if created:
                admin.set_password('AbujaAdmin2025')
                admin.save()
                print(f"Created hospital admin: {admin_email}")
            
            # Create staff members (doctors)
            for i in range(1, 4):
                email = f"doctor{i}@abujageneralhospital.com"
                # Check if user already exists
                user = CustomUser.objects.filter(email=email).first()
                if not user:
                    # Create user
                    user = CustomUser.objects.create(
                        email=email,
                        first_name=f"Doctor{i}",
                        last_name="Abuja",
                        role='doctor',
                        is_staff=True,
                        is_email_verified=True,
                        primary_hospital=hospital
                    )
                    user.set_password('Doctor2025')
                    user.save()
                    print(f"Created doctor user: {email}")
                
                # Associate doctor with hospital
                user.primary_hospital = hospital
                user.save()
                print(f"Associated doctor {email} with hospital")
            
            # Add basic medication catalog entries
            med = MedicationCatalog.objects.create(
                generic_name='Artemether/Lumefantrine',
                brand_names=['Coartem'],
                drug_class='Antimalarial',
                available_forms=['tablet']
            )
            print(f"Created medication catalog entry: {med.generic_name}")
            
            print("\nSuccessfully created or updated Abuja hospital with staff!")
            return True
        except Exception as e:
            print(f"Error creating Abuja hospital with staff: {e}")
            print(traceback.format_exc())
            return False

def check_database_state():
    """Check the state of the database"""
    print("\nDatabase State:")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    print(f"Custom Users: {CustomUser.objects.count()}")
    print(f"Medication Catalog: {MedicationCatalog.objects.count()}")

def main():
    print("Creating Abuja hospital data with staff for testing...")
    
    # First check current state
    print("Current database state:")
    check_database_state()
    
    # Create hospital data
    if create_abuja_hospital_with_staff():
        print("\nu2705 Successfully created or updated Abuja hospital data with staff!")
    else:
        print("\nu274c Failed to create Abuja hospital data with staff")
    
    # Check final state
    print("\nFinal database state:")
    check_database_state()
    
    print("\n" + "=" * 50)
    print("Abuja hospital credentials created:")
    print("\nAdmin account:")
    print("Email: admin@abujageneralhospital.com")
    print("Password: AbujaAdmin2025")
    print("\nDoctor accounts (password for all: Doctor2025):")
    print("- doctor1@abujageneralhospital.com")
    print("- doctor2@abujageneralhospital.com")
    print("- doctor3@abujageneralhospital.com")
    print("=" * 50)

if __name__ == "__main__":
    main()
