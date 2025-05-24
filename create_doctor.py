#!/usr/bin/env python
import os
import django
import sys
from django.utils import timezone

# Adjust the Python path to include the parent directory
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Doctor, Hospital, Department, CustomUser

def create_doctor_from_user(email, department_name, hospital_name):
    """Create a doctor profile for an existing user"""
    try:
        # Find the user
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            print(f"\n\u274c User with email {email} not found.")
            return False
        
        # Find the hospital
        hospital = Hospital.objects.filter(name__icontains=hospital_name).first()
        if not hospital:
            print(f"\n\u274c Hospital with name containing '{hospital_name}' not found.")
            return False
        
        # Find the department
        department = Department.objects.filter(
            name__icontains=department_name,
            hospital=hospital
        ).first()
        if not department:
            print(f"\n\u274c Department with name containing '{department_name}' in hospital '{hospital.name}' not found.")
            return False
        
        # Check if doctor already exists for this user
        existing_doctor = Doctor.objects.filter(user=user).first()
        if existing_doctor:
            print(f"\n\u274c Doctor profile already exists for {email}")
            return False
        
        # Print the current Doctor model fields for debugging
        print("\nDoctor model fields:")
        for field in Doctor._meta.fields:
            print(f"  - {field.name} ({field.get_internal_type()})")
        
        # Create the doctor with all required fields
        doctor = Doctor.objects.create(
            user=user,
            hospital=hospital,
            department=department,
            status="active",
            years_of_experience=5,
            languages_spoken="English",
            is_active=True,
            is_verified=True,
            chronic_care_experience=True,
            available_for_appointments=True,
            specialization="Cardiology",
            medical_license_number="MED-" + email.split('@')[0][:5].upper(),
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365*5),  # 5 years from now
            qualifications=["MD", "MBBS", "PhD"],
            board_certifications="Board Certified in Cardiology",
            consultation_hours_start=timezone.datetime.strptime('09:00', '%H:%M').time(),
            consultation_hours_end=timezone.datetime.strptime('17:00', '%H:%M').time(),
            consultation_days="Monday,Tuesday,Wednesday,Thursday,Friday",
            max_daily_appointments=20,
            appointment_duration=30,
            medical_school="Lagos Medical School",
            graduation_year=2015,
            office_phone="+2347012345678",
            office_location="2nd Floor, Cardiology Wing",
            emergency_contact="+2347012345678",
            expertise_codes=[],
            primary_expertise_codes=[],
            complex_case_rating=4.5,
            continuity_of_care_rating=4.8
        )
        
        # Update user role if needed
        if user.role != 'doctor':
            user.role = 'doctor'
            user.save()
        
        print(f"\n\u2705 Successfully created doctor profile for {user.first_name} {user.last_name} ({email})")
        print(f"Department: {department.name}")
        print(f"Hospital: {hospital.name}")
        print(f"Role: {user.role}")
        return True
    except Exception as e:
        print(f"\n\u274c Error creating doctor: {e}")
        return False

if __name__ == "__main__":
    email = "eruwagolden55@gmail.com"
    department = "Cardiology"
    hospital = "St. Nicholas"
    create_doctor_from_user(email, department, hospital)
