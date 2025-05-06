#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.user.custom_user import CustomUser
from api.models.medical.hospital_registration import HospitalRegistration

# Email to check
email = "eruwagolden@gmail.com"

try:
    # Find the user
    user = CustomUser.objects.get(email=email)
    print(f"User found: {user.email} (ID: {user.id})")
    
    # Check if the user has hospital registrations
    registrations = HospitalRegistration.objects.filter(user=user)
    
    if registrations.exists():
        print(f"Found {registrations.count()} hospital registration(s):")
        for reg in registrations:
            print(f"- Hospital: {reg.hospital.name}")
            print(f"  Status: {reg.status}")
            print(f"  Is Primary: {reg.is_primary}")
            print(f"  Created: {reg.created_at}")
            print(f"  Approved: {reg.approved_date}")
    else:
        print("No hospital registrations found for this user.")
    
    # Check user's primary hospital
    if hasattr(user, 'hospital') and user.hospital:
        print(f"\nUser's primary hospital is set to: {user.hospital.name}")
    else:
        print("\nUser does not have a primary hospital set.")
    
except CustomUser.DoesNotExist:
    print(f"User with email {email} not found.")
except Exception as e:
    print(f"Error: {e}")
