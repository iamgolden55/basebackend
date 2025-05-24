import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital
from api.models.medical.department import Department
from django.utils import timezone

def create_test_department():
    """
    Create a test department in an existing hospital
    """
    # Find the first hospital in the system
    try:
        hospital = Hospital.objects.first()
        if not hospital:
            print("No hospitals found in the system. Creating a test hospital first...")
            hospital = Hospital.objects.create(
                name="Test General Hospital",
                hospital_type="general",
                city="Test City",
                address="123 Test Street",
                is_verified=True,
                verification_date=timezone.now().date(),
                email="test@hospital.com"
            )
            print(f"Created test hospital: {hospital.name}")
        
        # Create a new department using the hospital's create_department method
        department = hospital.create_department(
            name="Cardiology",
            code="CARD-002",
            department_type="medical",
            description="Specializes in diagnosis and treatment of heart conditions",
            floor_number="5",
            wing="north",
            extension_number="3001",
            emergency_contact="3911",
            email="cardiology@testhospital.com",
            is_24_hours=True,
            operating_hours={
                "monday": {"open": "08:00", "close": "20:00"},
                "tuesday": {"open": "08:00", "close": "20:00"},
                "wednesday": {"open": "08:00", "close": "20:00"},
                "thursday": {"open": "08:00", "close": "20:00"},
                "friday": {"open": "08:00", "close": "18:00"},
                "saturday": {"open": "09:00", "close": "15:00"},
                "sunday": {"open": "10:00", "close": "14:00"}
            },
            total_beds=20,
            icu_beds=5,
            bed_capacity=25,
            minimum_staff_required=4,
            current_staff_count=5,  # Ensure we have enough staff for validation
            recommended_staff_ratio=1.5,
            annual_budget=500000.00,
            appointment_duration=30,
            max_daily_appointments=40,
            requires_referral=True
        )
        
        print(f"\nSuccessfully created department:\n")
        print(f"ID: {department.id}")
        print(f"Name: {department.name}")
        print(f"Code: {department.code}")
        print(f"Hospital: {department.hospital.name}")
        print(f"Type: {department.department_type}")
        print(f"Location: {department.wing} Wing, Floor {department.floor_number}")
        print(f"Capacity: {department.total_beds} regular beds, {department.icu_beds} ICU beds")
        print(f"Contact: {department.extension_number} (ext)")
        
        # List all departments in this hospital
        all_departments = Department.objects.filter(hospital=hospital)
        print(f"\nAll departments in {hospital.name}:")
        for i, dept in enumerate(all_departments, 1):
            print(f"{i}. {dept.name} ({dept.code})")
        
    except Exception as e:
        print(f"Error creating department: {str(e)}")

if __name__ == "__main__":
    create_test_department()
