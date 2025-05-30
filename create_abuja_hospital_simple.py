# Script to create Abuja hospital data with required staff counts
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

def create_abuja_hospital():
    """Create Abuja hospital and departments with proper staff counts"""
    with transaction.atomic():
        try:
            # Create Abuja hospital or use existing one
            hospital, created = Hospital.objects.get_or_create(
                name="Abuja General Hospital",
                defaults={
                    'hospital_type': "General Hospital",
                    'address': "123 Federal Capital Territory",
                    'city': "Abuja",
                    'state': "FCT",
                    'country': "Nigeria",
                    'postal_code': "900001",
                    'phone': "+2348012345678",
                    'email': "info@abujageneralhospital.com",
                    'website': "www.abujageneralhospital.com",
                    'emergency_unit': True,
                    'icu_unit': True,
                    'is_verified': True
                }
            )
            
            if created:
                print(f"Created hospital: {hospital.name}")
            else:
                print(f"Using existing hospital: {hospital.name}")
            
            # Create departments with proper staff counts
            departments = [
                {
                    'name': "Emergency",
                    'code': "EMG-ABJ",
                    'description': "Emergency Department at Abuja General Hospital",
                    'current_staff_count': 5,  # Setting staff count above minimum
                    'minimum_staff_required': 3
                },
                {
                    'name': "Cardiology",
                    'code': "CAR-ABJ",
                    'description': "Cardiology Department at Abuja General Hospital",
                    'current_staff_count': 4,
                    'minimum_staff_required': 2
                },
                {
                    'name': "Neurology",
                    'code': "NEU-ABJ",
                    'description': "Neurology Department at Abuja General Hospital",
                    'current_staff_count': 3,
                    'minimum_staff_required': 2
                },
                {
                    'name': "Pediatrics",
                    'code': "PED-ABJ",
                    'description': "Pediatrics Department at Abuja General Hospital",
                    'current_staff_count': 4,
                    'minimum_staff_required': 3
                }
            ]
            
            for dept_data in departments:
                # Check if department already exists
                existing_dept = Department.objects.filter(
                    name=dept_data['name'], 
                    hospital=hospital
                ).first()
                
                if existing_dept:
                    print(f"Department already exists: {dept_data['name']}")
                    # Update staff counts if needed
                    if existing_dept.current_staff_count < dept_data['current_staff_count']:
                        existing_dept.current_staff_count = dept_data['current_staff_count']
                        existing_dept.save()
                        print(f"Updated staff count for: {dept_data['name']}")
                else:
                    # Create new department with proper staff counts
                    department = Department.objects.create(
                        hospital=hospital,
                        **dept_data
                    )
                    print(f"Created department: {department.name} with {department.current_staff_count} staff")
            
            # Create a hospital admin account if needed
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
            else:
                print(f"Admin already exists: {admin_email}")
            
            return True
        except Exception as e:
            print(f"Error creating Abuja hospital: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_database_state():
    """Check the state of the database"""
    print("\nDatabase State:")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    print(f"Medication Catalog: {MedicationCatalog.objects.count()}")

def main():
    print("Creating Abuja hospital data...")
    
    # First check current state
    print("Current database state:")
    check_database_state()
    
    # Create hospital data
    if create_abuja_hospital():
        print("\nu2705 Successfully created Abuja hospital data!")
    else:
        print("\nu274c Failed to create Abuja hospital data")
    
    # Check final state
    print("\nFinal database state:")
    check_database_state()
    
    print("\n" + "=" * 50)
    print("Abuja hospital admin account:")
    print("Email: admin@abujageneralhospital.com")
    print("Password: AbujaAdmin2025")
    print("=" * 50)

if __name__ == "__main__":
    main()
