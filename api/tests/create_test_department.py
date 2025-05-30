import os
import django
import sys
import argparse
from datetime import time

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital
from api.models.medical.department import Department
from django.utils import timezone

# Standard operating hours template
STANDARD_HOURS = {
    "monday": {"open": "08:00", "close": "17:00"},
    "tuesday": {"open": "08:00", "close": "17:00"},
    "wednesday": {"open": "08:00", "close": "17:00"},
    "thursday": {"open": "08:00", "close": "17:00"},
    "friday": {"open": "08:00", "close": "17:00"},
    "saturday": {"open": "09:00", "close": "13:00"},
    "sunday": {"open": "10:00", "close": "14:00"}
}

EMERGENCY_HOURS = {
    "monday": {"open": "00:00", "close": "23:59"},
    "tuesday": {"open": "00:00", "close": "23:59"},
    "wednesday": {"open": "00:00", "close": "23:59"},
    "thursday": {"open": "00:00", "close": "23:59"},
    "friday": {"open": "00:00", "close": "23:59"},
    "saturday": {"open": "00:00", "close": "23:59"},
    "sunday": {"open": "00:00", "close": "23:59"}
}

# Department templates with common configurations
DEPARTMENT_TEMPLATES = {
    "cardiology": {
        "name": "Cardiology",
        "code": "CARD",
        "department_type": "medical",
        "description": "Specializes in diagnosis and treatment of heart conditions",
        "floor_number": "3",
        "wing": "north",
        "is_24_hours": False,
        "total_beds": 25,
        "icu_beds": 8,
        "minimum_staff_required": 5,
        "appointment_duration": 30,
        "requires_referral": True
    },
    "neurology": {
        "name": "Neurology",
        "code": "NEUR",
        "department_type": "medical",
        "description": "Specializes in disorders of the nervous system",
        "floor_number": "4",
        "wing": "east",
        "is_24_hours": False,
        "total_beds": 20,
        "icu_beds": 5,
        "minimum_staff_required": 4,
        "appointment_duration": 45,
        "requires_referral": True
    },
    "orthopedics": {
        "name": "Orthopedics",
        "code": "ORTH",
        "department_type": "surgical",
        "description": "Specializes in musculoskeletal system - bones, joints, ligaments, tendons, muscles",
        "floor_number": "2",
        "wing": "west",
        "is_24_hours": False,
        "total_beds": 30,
        "icu_beds": 0,
        "minimum_staff_required": 6,
        "appointment_duration": 30,
        "requires_referral": False
    },
    "emergency": {
        "name": "Emergency Department",
        "code": "EMER",
        "department_type": "emergency",
        "description": "Provides immediate care for acute illnesses and injuries",
        "floor_number": "1",
        "wing": "central",
        "is_24_hours": True,
        "total_beds": 15,
        "icu_beds": 5,
        "minimum_staff_required": 10,
        "appointment_duration": 0,  # No appointments in emergency
        "requires_referral": False
    },
    "pediatrics": {
        "name": "Pediatrics",
        "code": "PEDI",
        "department_type": "medical",
        "description": "Medical care for infants, children, and adolescents",
        "floor_number": "5",
        "wing": "south",
        "is_24_hours": False,
        "total_beds": 35,
        "icu_beds": 10,
        "minimum_staff_required": 8,
        "appointment_duration": 25,
        "requires_referral": False
    },
    "radiology": {
        "name": "Radiology",
        "code": "RADI",
        "department_type": "radiology",
        "description": "Diagnostic imaging services including X-ray, CT, MRI",
        "floor_number": "2",
        "wing": "east",
        "is_24_hours": False,
        "total_beds": 0,  # No beds in radiology
        "icu_beds": 0,
        "minimum_staff_required": 4,
        "appointment_duration": 20,
        "requires_referral": True
    },
    "laboratory": {
        "name": "Clinical Laboratory",
        "code": "CLAB",
        "department_type": "laboratory",
        "description": "Performs tests on clinical specimens for diagnosis",
        "floor_number": "1",
        "wing": "south",
        "is_24_hours": True,
        "total_beds": 0,  # No beds in laboratory
        "icu_beds": 0,
        "minimum_staff_required": 5,
        "appointment_duration": 15,
        "requires_referral": True
    },
    "pharmacy": {
        "name": "Pharmacy",
        "code": "PHAR",
        "department_type": "pharmacy",
        "description": "Dispenses medications and provides pharmaceutical care",
        "floor_number": "1",
        "wing": "central",
        "is_24_hours": True,
        "total_beds": 0,  # No beds in pharmacy
        "icu_beds": 0,
        "minimum_staff_required": 3,
        "appointment_duration": 10,
        "requires_referral": False
    },
    "obstetrics": {
        "name": "Obstetrics & Gynecology",
        "code": "OBGY",
        "department_type": "medical",
        "description": "Women's health and childbirth",
        "floor_number": "4",
        "wing": "north",
        "is_24_hours": True,
        "total_beds": 25,
        "icu_beds": 5,
        "minimum_staff_required": 7,
        "appointment_duration": 30,
        "requires_referral": False
    },
    "icu": {
        "name": "Intensive Care Unit",
        "code": "ICU",
        "department_type": "critical_care",
        "description": "Specialized care for patients with severe and life-threatening illnesses",
        "floor_number": "3",
        "wing": "central",
        "is_24_hours": True,
        "total_beds": 0,  # All beds are ICU beds
        "icu_beds": 20,
        "minimum_staff_required": 12,
        "appointment_duration": 0,  # No appointments in ICU
        "requires_referral": True
    }
}

def create_departments(hospital_name=None, department_types=None):
    """
    Create departments in a specified hospital or the first available hospital
    
    Args:
        hospital_name (str): Name of the hospital to add departments to
        department_types (list): List of department types to create
    """
    try:
        # Find the specified hospital or use the first one
        if hospital_name:
            hospital = Hospital.objects.filter(name__icontains=hospital_name).first()
            if not hospital:
                print(f"Hospital with name containing '{hospital_name}' not found.")
                return
        else:
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
        
        print(f"\nCreating departments for hospital: {hospital.name}\n")
        
        # If no specific departments are requested, use all templates
        if not department_types:
            department_types = list(DEPARTMENT_TEMPLATES.keys())
        
        created_departments = []
        existing_departments = Department.objects.filter(hospital=hospital).values_list('name', flat=True)
        
        # Create each requested department
        for dept_type in department_types:
            if dept_type not in DEPARTMENT_TEMPLATES:
                print(f"Warning: Unknown department type '{dept_type}'. Skipping.")
                continue
                
            template = DEPARTMENT_TEMPLATES[dept_type]
            
            # Skip if department with this name already exists
            if template["name"] in existing_departments:
                print(f"Department '{template['name']}' already exists in {hospital.name}. Skipping.")
                continue
                
            # Generate a unique code with hospital-specific suffix
            code_suffix = f"{len(existing_departments) + len(created_departments) + 1:03d}"
            unique_code = f"{template['code']}-{code_suffix}"
            
            # Set appropriate operating hours based on 24-hour status
            if template["is_24_hours"]:
                operating_hours = {
                    "monday": {"start": "00:00", "end": "23:59"},
                    "tuesday": {"start": "00:00", "end": "23:59"},
                    "wednesday": {"start": "00:00", "end": "23:59"},
                    "thursday": {"start": "00:00", "end": "23:59"},
                    "friday": {"start": "00:00", "end": "23:59"},
                    "saturday": {"start": "00:00", "end": "23:59"},
                    "sunday": {"start": "00:00", "end": "23:59"}
                }
            else:
                operating_hours = {
                    "monday": {"start": "08:00", "end": "17:00"},
                    "tuesday": {"start": "08:00", "end": "17:00"},
                    "wednesday": {"start": "08:00", "end": "17:00"},
                    "thursday": {"start": "08:00", "end": "17:00"},
                    "friday": {"start": "08:00", "end": "17:00"},
                    "saturday": {"start": "09:00", "end": "13:00"},
                    "sunday": {"start": "10:00", "end": "14:00"}
                }
            
            # Calculate bed capacity
            bed_capacity = template["total_beds"] + template["icu_beds"]
            
            # Create the department
            department = hospital.create_department(
                name=template["name"],
                code=unique_code,
                department_type=template["department_type"],
                description=template["description"],
                floor_number=template["floor_number"],
                wing=template["wing"],
                extension_number=f"{3000 + len(created_departments)}",
                emergency_contact=f"{9000 + len(created_departments)}",
                email=f"{dept_type.lower()}@{hospital.name.lower().replace(' ', '')}.com",
                is_24_hours=template["is_24_hours"],
                operating_hours=operating_hours,
                total_beds=template["total_beds"],
                icu_beds=template["icu_beds"],
                bed_capacity=bed_capacity,
                minimum_staff_required=template["minimum_staff_required"],
                current_staff_count=template["minimum_staff_required"] + 1,  # Ensure we have enough staff
                recommended_staff_ratio=1.5,
                annual_budget=500000.00,
                appointment_duration=template["appointment_duration"],
                max_daily_appointments=50,
                requires_referral=template["requires_referral"]
            )
            
            created_departments.append(department)
            print(f"Created department: {department.name} ({department.code})")
            print(f"  Type: {department.get_department_type_display()}")
            print(f"  Location: {department.wing} Wing, Floor {department.floor_number}")
            print(f"  Capacity: {department.total_beds} regular beds, {department.icu_beds} ICU beds")
            print(f"  24-Hour Service: {'Yes' if department.is_24_hours else 'No'}")
            print(f"  Minimum Staff: {department.minimum_staff_required}\n")
        
        # Summary of all departments in the hospital
        all_departments = Department.objects.filter(hospital=hospital)
        print(f"\n=== All departments in {hospital.name} ({all_departments.count()} total) ===\n")
        for i, dept in enumerate(all_departments, 1):
            print(f"{i}. {dept.name} ({dept.code}) - {dept.get_department_type_display()}")
            print(f"   Beds: {dept.total_beds} regular, {dept.icu_beds} ICU")
        
        return created_departments
        
    except Exception as e:
        print(f"Error creating departments: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create hospital departments')
    parser.add_argument('--hospital', type=str, help='Name of the hospital (partial match)')
    parser.add_argument('--departments', type=str, nargs='+', 
                        choices=list(DEPARTMENT_TEMPLATES.keys()),
                        help='Department types to create')
    parser.add_argument('--list', action='store_true', help='List available department templates')
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable department templates:\n")
        for key, dept in DEPARTMENT_TEMPLATES.items():
            print(f"{key}: {dept['name']} ({dept['department_type']})")
            print(f"  Description: {dept['description']}")
            print(f"  Beds: {dept['total_beds']} regular, {dept['icu_beds']} ICU\n")
        sys.exit(0)
    
    create_departments(args.hospital, args.departments)
