#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Doctor

User = get_user_model()

def check_user_role(email):
    """Check user role and doctor status"""
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            print(f"\n❌ User with email {email} not found.")
            return False
        
        print(f"\n=== User Details for {email} ===")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role if hasattr(user, 'role') else 'No role field'}")
        print(f"User Type: {user.user_type if hasattr(user, 'user_type') else 'No user_type field'}")
        print(f"Is Staff: {user.is_staff}")
        print(f"Is Active: {user.is_active}")
        
        # Check if user has HPN (Health Professional Number)
        if hasattr(user, 'hpn'):
            print(f"HPN: {user.hpn}")
        
        # Check if doctor profile exists
        doctor = Doctor.objects.filter(user=user).first()
        if doctor:
            print(f"\n=== Doctor Profile ===")
            print(f"Department: {doctor.department.name}")
            print(f"Hospital: {doctor.hospital.name}")
            print(f"Status: {doctor.status}")
            print(f"Medical License: {doctor.medical_license_number}")
            print(f"Is Verified: {doctor.is_verified}")
        else:
            print(f"\n❌ No doctor profile found for this user")
        
        return True
    except Exception as e:
        print(f"\n❌ Error checking user: {e}")
        return False

if __name__ == "__main__":
    email = "eruwagolden55@gmail.com"
    check_user_role(email)
