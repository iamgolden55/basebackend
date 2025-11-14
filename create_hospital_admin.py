#!/usr/bin/env python
"""
Create hospital admin account for existing hospital
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
from api.utils.email import send_hospital_admin_credentials
import secrets
import string
import re

def create_hospital_admin_for_hospital(hospital_name):
    """Create hospital admin account for existing hospital"""
    try:
        # Find the hospital
        hospital = Hospital.objects.filter(name__icontains=hospital_name).first()

        if not hospital:
            print(f"❌ Hospital not found: {hospital_name}")
            return False

        print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
        print(f"   Email: {hospital.email}")
        print(f"   Registration Number: {hospital.registration_number}")

        # Check if admin already exists
        existing_admin = HospitalAdmin.objects.filter(hospital=hospital).first()
        if existing_admin:
            print(f"⚠️  Hospital admin already exists: {existing_admin.email}")
            return False

        # Generate admin email from hospital name
        hospital_name_clean = re.sub(r'[^a-zA-Z0-9\s]', '', hospital.name.lower())
        hospital_slug = hospital_name_clean.replace(' ', '')[:50]
        admin_email = f"admin.{hospital_slug}@example.com"

        # Generate secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        password = password[:9] + 'A1!'  # Ensure it has uppercase, digit, and special char

        print(f"\n🔐 Creating admin account...")
        print(f"   Admin Email: {admin_email}")
        print(f"   Password: {password}")

        # Create hospital admin
        hospital_admin = HospitalAdmin.objects.create(
            hospital=hospital,
            name=f"{hospital.name} Administrator",
            position="Hospital Administrator",
            email=admin_email,
            contact_email=hospital.email,  # Real email for notifications
            password=password  # Will be hashed by HospitalAdmin.save()
        )

        print(f"✅ Hospital admin account created successfully!")
        print(f"   User ID: {hospital_admin.user.id if hospital_admin.user else 'N/A'}")

        # Send credentials email
        print(f"\n📧 Sending credentials email to {hospital.email}...")
        email_sent = send_hospital_admin_credentials(hospital, admin_email, password)

        if email_sent:
            print(f"✅ Credentials email sent successfully!")
        else:
            print(f"⚠️  Failed to send credentials email, but account was created")

        print(f"\n" + "="*60)
        print(f"HOSPITAL ADMIN CREDENTIALS")
        print(f"="*60)
        print(f"Hospital: {hospital.name}")
        print(f"Hospital Code: {hospital.registration_number}")
        print(f"Login Email: {admin_email}")
        print(f"Password: {password}")
        print(f"Real Contact Email: {hospital.email}")
        print(f"="*60)

        return True

    except Exception as e:
        print(f"❌ Error creating hospital admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    hospital_name = "New General Central Hospital GRA Asaba"
    print(f"Creating hospital admin for: {hospital_name}")
    print(f"=" * 60)
    create_hospital_admin_for_hospital(hospital_name)
