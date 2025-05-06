import os
import django
import sys
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, Department, CustomUser, HospitalRegistration, Doctor
from django.db import transaction

# Hospital name
HOSPITAL_NAME = "Abuja Central Hospital"

# Define common departments and their doctors
DEPARTMENTS = [
    {
        "name": "Cardiology",
        "code": "CARD",
        "department_type": "medical",
        "description": "Heart and cardiovascular system specialists",
        "minimum_staff": 2,
        "doctors": [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@abujahospital.com",
                "specialization": "Interventional Cardiology",
                "license_number": "CARD001",
                "years_experience": 10
            },
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@abujahospital.com",
                "specialization": "Cardiac Electrophysiology",
                "license_number": "CARD002",
                "years_experience": 8
            }
        ]
    },
    {
        "name": "Pediatrics",
        "code": "PED",
        "department_type": "medical",
        "description": "Child healthcare specialists",
        "minimum_staff": 1,
        "doctors": [
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "email": "michael.brown@abujahospital.com",
                "specialization": "General Pediatrics",
                "license_number": "PED001",
                "years_experience": 12
            }
        ]
    },
    {
        "name": "Orthopedics",
        "code": "ORTH",
        "department_type": "surgical",
        "description": "Bone and joint specialists",
        "minimum_staff": 1,
        "doctors": [
            {
                "first_name": "David",
                "last_name": "Wilson",
                "email": "david.wilson@abujahospital.com",
                "specialization": "Joint Replacement",
                "license_number": "ORTH001",
                "years_experience": 15
            }
        ]
    },
    {
        "name": "Neurology",
        "code": "NEUR",
        "department_type": "medical",
        "description": "Brain and nervous system specialists",
        "minimum_staff": 1,
        "doctors": [
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "email": "emily.davis@abujahospital.com",
                "specialization": "Clinical Neurology",
                "license_number": "NEUR001",
                "years_experience": 9
            }
        ]
    }
]

try:
    with transaction.atomic():
        # Get or create the hospital
        hospital, created = Hospital.objects.get_or_create(
            name=HOSPITAL_NAME,
            defaults={
                'address': '123 Hospital Road',
                'city': 'Abuja',
                'country': 'Nigeria',
                'phone': '+234123456789',
                'email': 'info@abujacentralhospital.com'
            }
        )
        
        if created:
            print(f"\nCreated new hospital: {hospital.name}")
        else:
            print(f"\nUsing existing hospital: {hospital.name}")

        # Create departments and doctors
        created_departments = []
        created_doctors = []
        
        for dept_data in DEPARTMENTS:
            # First create the department
            dept = Department.objects.create(
                hospital=hospital,
                name=dept_data['name'],
                code=dept_data['code'],
                department_type=dept_data['department_type'],
                description=dept_data['description'],
                minimum_staff_required=dept_data['minimum_staff'],
                current_staff_count=len(dept_data['doctors']),
                floor_number='1',
                wing='north',
                extension_number='123',
                emergency_contact='911',
                email=f"{dept_data['code'].lower()}@abujacentralhospital.com",
                is_24_hours=False,
                operating_hours={
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'}
                },
                total_beds=20,
                icu_beds=5,
                appointment_duration=30,
                max_daily_appointments=50,
                requires_referral=False,
                recommended_staff_ratio=1.0
            )
            created_departments.append(dept)
            print(f"\nCreated department: {dept.name}")
            
            # Create doctors for this department
            department_doctors = []
            for doctor_data in dept_data['doctors']:
                # Create user account for doctor
                doctor_user, created = CustomUser.objects.get_or_create(
                    email=doctor_data['email'],
                    defaults={
                        'first_name': doctor_data['first_name'],
                        'last_name': doctor_data['last_name'],
                        'role': 'doctor',
                        'is_email_verified': True
                    }
                )
                
                if created:
                    doctor_user.set_password('Doctor@123')
                    doctor_user.save()
                    print(f"Created doctor user: Dr. {doctor_user.first_name} {doctor_user.last_name}")
                
                # Create hospital registration for doctor
                registration, created = HospitalRegistration.objects.get_or_create(
                    user=doctor_user,
                    hospital=hospital,
                    defaults={
                        'status': 'approved',
                        'approved_date': timezone.now(),
                        'is_primary': True
                    }
                )
                
                if created:
                    # Create doctor profile with required fields
                    doctor = Doctor.objects.create(
                        user=doctor_user,
                        hospital=hospital,
                        department=dept,
                        specialization=doctor_data['specialization'],
                        medical_license_number=doctor_data['license_number'],
                        license_expiry_date=date.today() + timedelta(days=365),  # Valid for 1 year
                        years_of_experience=doctor_data['years_experience'],
                        is_verified=True,
                        status='active',
                        consultation_days='Mon,Tue,Wed,Thu,Fri',
                        consultation_hours_start=timezone.datetime.strptime('09:00', '%H:%M').time(),
                        consultation_hours_end=timezone.datetime.strptime('17:00', '%H:%M').time(),
                        languages_spoken='English',
                        qualifications=["MBBS", "MD"],
                        available_for_appointments=True
                    )
                    created_doctors.append(doctor)
                    department_doctors.append(doctor_user)
                    print(f"Created doctor profile for Dr. {doctor_user.first_name} {doctor_user.last_name}")
                    print(f"Specialization: {doctor_data['specialization']}")
                    print(f"Department: {dept.name}")

            # Update department's current staff count
            dept.current_staff_count = len(department_doctors)
            dept.save()

        print("\nSetup completed successfully!")
        print(f"Total departments created: {len(created_departments)}")
        print(f"Total doctors registered: {len(created_doctors)}")
        print("\nDoctor Credentials:")
        print("------------------")
        print("Email format: firstname.lastname@abujahospital.com")
        print("Default password for all doctors: Doctor@123")

except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1) 