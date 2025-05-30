# Script to update Abuja hospital with registration number
import os
import django
import secrets

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital
from api.models.medical.hospital_auth import HospitalAdmin

def update_abuja_hospital():
    # Get the Abuja hospital
    hospital = Hospital.objects.filter(name="Abuja General Hospital").first()
    
    if not hospital:
        print("❌ Abuja General Hospital not found!")
        return False
    
    # Ensure hospital has a registration number for code verification
    if not hospital.registration_number:
        hospital.registration_number = f"ABUJA-{secrets.token_hex(4).upper()}"
        hospital.save()
        print(f"✅ Generated registration number: {hospital.registration_number}")
    else:
        print(f"ℹ️ Hospital already has registration number: {hospital.registration_number}")
    
    # Get admin info
    admin = HospitalAdmin.objects.filter(hospital=hospital).first()
    
    if admin:
        print(f"\nAdmin credentials for {hospital.name}:")
        print(f"Admin name: {admin.name}")
        print(f"Admin email: {admin.email}")
        print(f"Hospital code (for verification): {hospital.registration_number}")
        print("Password: AbujaAdmin2025")
    else:
        print(f"❌ No admin found for {hospital.name}")
    
    return True

if __name__ == "__main__":
    print("Updating Abuja hospital with registration number...")
    update_abuja_hospital()
    print("\nDone!")
