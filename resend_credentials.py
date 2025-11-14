#!/usr/bin/env python
"""
Resend hospital admin credentials email
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

def resend_credentials():
    """Resend credentials email"""
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

        # Use the current password (already set)
        password = "Password123!"  # The password we set

        print(f"📧 Resending credentials email...")
        print(f"   To: {hospital_admin.contact_email}")
        print(f"   Username: {hospital_admin.email}")
        print(f"   Password: {password}")
        print()

        # Send credentials email
        email_sent = send_hospital_admin_credentials(hospital, hospital_admin.email, password)

        if email_sent:
            print(f"✅ Credentials email sent successfully to {hospital_admin.contact_email}!")
        else:
            print(f"❌ Failed to send credentials email")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    resend_credentials()
