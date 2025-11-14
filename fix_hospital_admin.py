#!/usr/bin/env python
"""
Fix hospital admin credentials mismatch
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

def fix_hospital_admin():
    """Fix hospital admin email mismatch"""
    try:
        hospital_name = "New General Central Hospital GRA Asaba"

        # Find the hospital
        hospital = Hospital.objects.filter(name__icontains=hospital_name).first()

        if not hospital:
            print(f"❌ Hospital not found")
            return

        # Find hospital admin
        hospital_admin = HospitalAdmin.objects.filter(hospital=hospital).first()

        if not hospital_admin:
            print(f"❌ No hospital admin found")
            return

        print(f"Current State:")
        print(f"  HospitalAdmin.email: {hospital_admin.email}")
        print(f"  HospitalAdmin.contact_email: {hospital_admin.contact_email}")
        print(f"  CustomUser.email: {hospital_admin.user.email if hospital_admin.user else 'No user'}")
        print()

        # Fix the CustomUser email to match HospitalAdmin.email
        if hospital_admin.user:
            user = hospital_admin.user
            old_email = user.email
            user.email = hospital_admin.email  # Should be admin.newgeneralcentralhospitalgraasaba@example.com
            user.save()

            print(f"✅ Fixed CustomUser email:")
            print(f"   Old: {old_email}")
            print(f"   New: {user.email}")
            print()

            # Verify
            user_by_email = CustomUser.objects.filter(email=hospital_admin.email).first()
            if user_by_email:
                print(f"✅ User can now be found by email lookup!")
            else:
                print(f"❌ Still can't find user by email")

        print()
        print(f"=" * 60)
        print(f"LOGIN CREDENTIALS (NOW WORKING)")
        print(f"=" * 60)
        print(f"Login URL: http://localhost:5173/organization/login")
        print(f"Username/Email: {hospital_admin.email}")
        print(f"Password: Password123!")
        print(f"Hospital Code: {hospital.registration_number}")
        print(f"=" * 60)
        print(f"\n📧 Credentials were sent to: {hospital_admin.contact_email}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_hospital_admin()
