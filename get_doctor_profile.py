#!/usr/bin/env python3
import os
import sys
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Now import Django models
from api.models import CustomUser, Doctor

def get_doctor_profile(email):
    try:
        # Get the user
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return {"error": f"User with email {email} not found"}
        
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return {"error": f"User {email} does not have a doctor profile"}
        
        # Get the doctor profile
        doctor = user.doctor_profile
        
        # Create a data dictionary
        data = {
            'id': doctor.id,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}"
            },
            'specialization': doctor.specialization,
            'medical_license_number': doctor.medical_license_number,
            'license_expiry_date': str(doctor.license_expiry_date) if doctor.license_expiry_date else None,
            'years_of_experience': doctor.years_of_experience,
            'department': {
                'id': doctor.department.id if doctor.department else None,
                'name': doctor.department.name if doctor.department else None,
                'code': doctor.department.code if doctor.department else None
            },
            'hospital': {
                'id': doctor.hospital.id if doctor.hospital else None,
                'name': doctor.hospital.name if doctor.hospital else None
            },
            'consultation_days': doctor.consultation_days,
            'consultation_hours_start': str(doctor.consultation_hours_start) if doctor.consultation_hours_start else None,
            'consultation_hours_end': str(doctor.consultation_hours_end) if doctor.consultation_hours_end else None,
            'appointment_duration': doctor.appointment_duration,
            'is_active': doctor.is_active,
            'is_verified': doctor.is_verified
        }
        
        return data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Get email from command line argument or use default
    email = sys.argv[1] if len(sys.argv) > 1 else 'eruwagolden@gmail.com'
    
    # Get doctor profile
    profile = get_doctor_profile(email)
    
    # Print as JSON
    print(json.dumps(profile, indent=2)) 