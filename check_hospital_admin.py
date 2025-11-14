#!/usr/bin/env python
"""
Check hospital admin credentials
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.hospital import Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from api.models.user.custom_user import CustomUser

def check_hospital_admin():
    """Check hospital admin account details"""
    try:
        hospital_name = "New General Central Hospital GRA Asaba"

        # Find the hospital
        hospital = Hospital.objects.filter(name__icontains=hospital_name).first()

        if not hospital:
            print(f"❌ Hospital not found")
            return

        print(f"✅ Hospital: {hospital.name} (ID: {hospital.id})")
        print(f"   Registration Number: {hospital.registration_number}")
        print(f"   Email: {hospital.email}")
        print(f"   Is Verified: {hospital.is_verified}")
        print()

        # Find hospital admin
        hospital_admin = HospitalAdmin.objects.filter(hospital=hospital).first()

        if not hospital_admin:
            print(f"❌ No hospital admin found for this hospital")
            return

        print(f"✅ Hospital Admin:")
        print(f"   Admin Email (Login Username): {hospital_admin.email}")
        print(f"   Contact Email (Real Email): {hospital_admin.contact_email}")
        print(f"   Name: {hospital_admin.name}")
        print(f"   Position: {hospital_admin.position}")
        print()

        # Check if user account exists
        if hospital_admin.user:
            user = hospital_admin.user
            print(f"✅ User Account:")
            print(f"   User ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   First Name: {user.first_name}")
            print(f"   Last Name: {user.last_name}")
            print(f"   Role: {user.role}")
            print(f"   Is Staff: {user.is_staff}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Email Verified: {user.is_email_verified}")
            print(f"   Has Password: {user.password != ''}")
            print()

            # Try to find user by email
            user_by_email = CustomUser.objects.filter(email=hospital_admin.email).first()
            if user_by_email:
                print(f"✅ User can be found by email lookup")
                print(f"   Password hash starts with: {user_by_email.password[:20]}...")
            else:
                print(f"❌ User CANNOT be found by email lookup - THIS IS THE PROBLEM!")
        else:
            print(f"❌ No user account linked to hospital admin - THIS IS THE PROBLEM!")

        print()
        print(f"=" * 60)
        print(f"LOGIN CREDENTIALS")
        print(f"=" * 60)
        print(f"Login URL: http://localhost:5173/organization/login")
        print(f"Username/Email: {hospital_admin.email}")
        print(f"Password: [Check email at {hospital_admin.contact_email}]")
        print(f"Hospital Code: {hospital.registration_number}")
        print(f"=" * 60)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_hospital_admin()
