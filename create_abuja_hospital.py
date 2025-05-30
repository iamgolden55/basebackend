# Script to create Abuja hospital data
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
    """Create Abuja hospital, departments, admin, and medication data"""
    with transaction.atomic():
        try:
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
                "Orthopedics", "Obstetrics & Gynecology", "Internal Medicine",
                "Surgery", "Radiology", "Pharmacy", "Laboratory", "Tropical Medicine"
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
            admin_email = "admin@abujageneralhospital.com"
            admin, created = HospitalAdmin.objects.get_or_create(
                email=admin_email,
                defaults={
                    'hospital': hospital,
                    'position': 'Chief Administrator',
                    'name': 'Abuja Admin',
                    'password_change_required': True,  # Will force password change on first login
                    'contact_email': admin_email,  # Secondary contact email
                }
            )
            
            if created:
                admin.set_password('AbujaAdmin2025')
                admin.save()
                print(f"Created hospital admin: {admin_email}")
            
            # Add some medication catalog entries specific to the region
            medications = [
                {
                    'generic_name': 'Artemether/Lumefantrine',
                    'brand_names': ['Coartem', 'Riamet'],
                    'drug_class': 'Antimalarial',
                    'available_forms': ['tablet'],
                    'indications': 'Treatment of uncomplicated malaria',
                    'contraindications': 'First trimester of pregnancy',
                    'side_effects': 'Headache, dizziness, loss of appetite'
                },
                {
                    'generic_name': 'Amodiaquine',
                    'brand_names': ['Camoquin', 'Flavoquine'],
                    'drug_class': 'Antimalarial',
                    'available_forms': ['tablet', 'suspension'],
                    'indications': 'Treatment of malaria',
                    'contraindications': 'Hepatic disorders',
                    'side_effects': 'Nausea, vomiting, abdominal pain'
                },
                {
                    'generic_name': 'Albendazole',
                    'brand_names': ['Zentel', 'Albenza'],
                    'drug_class': 'Anthelmintic',
                    'available_forms': ['tablet', 'suspension'],
                    'indications': 'Treatment of intestinal parasites',
                    'contraindications': 'Pregnancy',
                    'side_effects': 'Abdominal pain, dizziness, headache'
                }
            ]
            
            for med_data in medications:
                # Check if medication already exists
                existing = MedicationCatalog.objects.filter(generic_name=med_data['generic_name']).first()
                if not existing:
                    med = MedicationCatalog.objects.create(**med_data)
                    print(f"Created medication catalog entry: {med.generic_name}")
                else:
                    print(f"Medication already exists: {med_data['generic_name']}")
            
            return True
        except Exception as e:
            print(f"Error creating Abuja hospital: {e}")
            return False

def check_database_state():
    """Check the state of the database"""
    print("\nDatabase State:")
    print(f"Hospitals: {Hospital.objects.count()}")
    print(f"Departments: {Department.objects.count()}")
    print(f"Hospital Admins: {HospitalAdmin.objects.count()}")
    print(f"Medication Catalog: {MedicationCatalog.objects.count()}")

def main():
    print("Creating Abuja hospital data for testing...")
    
    # First check current state
    print("Current database state:")
    check_database_state()
    
    # Create hospital data
    if create_abuja_hospital():
        print("\n✅ Successfully created Abuja hospital data!")
    else:
        print("\n❌ Failed to create Abuja hospital data")
    
    # Check final state
    print("\nFinal database state:")
    check_database_state()
    
    print("\n" + "=" * 50)
    print("Abuja hospital admin account created:")
    print("Email: admin@abujageneralhospital.com")
    print("Password: AbujaAdmin2025")
    print("")
    print("This account uses the special hospital admin secure login flow with:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA")
    print("4. Enhanced security with trusted device tracking")
    print("=" * 50)

if __name__ == "__main__":
    main()
