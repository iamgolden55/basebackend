#!/usr/bin/env python3
import os
import sys
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Now import Django models
from api.models import CustomUser, Doctor, Hospital, Department

def update_doctor_profile(email, hospital_name, department_name):
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
        
        # Find the hospital (case insensitive)
        hospital = Hospital.objects.filter(name__icontains=hospital_name).first()
        if not hospital:
            return {"error": f"Hospital with name containing '{hospital_name}' not found"}
        
        # Find the department (case insensitive) in the specified hospital
        department = Department.objects.filter(
            name__icontains=department_name,
            hospital=hospital
        ).first()
        
        # If department not found in this hospital, try to find any department matching the name
        if not department:
            department = Department.objects.filter(name__icontains=department_name).first()
            if not department:
                return {"error": f"Department with name containing '{department_name}' not found"}
        
        # Update doctor profile
        old_hospital = doctor.hospital.name if doctor.hospital else "None"
        old_department = doctor.department.name if doctor.department else "None"
        
        doctor.hospital = hospital
        doctor.department = department
        doctor.save()
        
        return {
            "message": "Doctor profile updated successfully",
            "doctor": {
                "id": doctor.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "old_hospital": old_hospital,
                "new_hospital": hospital.name,
                "old_department": old_department,
                "new_department": department.name
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Default values
    email = 'eruwagolden@gmail.com'
    hospital_name = 'St. Nicholas Hospital Lagos'
    department_name = 'Cardiology'
    
    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        hospital_name = sys.argv[2]
    if len(sys.argv) > 3:
        department_name = sys.argv[3]
    
    # Update doctor profile
    result = update_doctor_profile(email, hospital_name, department_name)
    
    # Print as JSON
    print(json.dumps(result, indent=2))
    
    # If successful, also print the updated doctor profile
    if "message" in result:
        from get_doctor_profile import get_doctor_profile
        profile = get_doctor_profile(email)
        print("\nUpdated Doctor Profile:")
        print(json.dumps(profile, indent=2)) 