# Script to fix Abuja hospital admin credentials
import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import transaction
from api.models import Hospital, HospitalAdmin
from api.models.user.custom_user import CustomUser

def fix_abuja_admin_credentials():
    """Fix Abuja hospital admin credentials to ensure login works"""
    with transaction.atomic():
        try:
            # Get the Abuja hospital
            hospital = Hospital.objects.filter(name="Abuja General Hospital").first()
            if not hospital:
                print("u274c Abuja General Hospital not found!")
                return False
                
            print(f"Found hospital: {hospital.name}")
            
            # Check if hospital has registration number
            if not hospital.registration_number or not hospital.registration_number.startswith('H-'):
                # Update with the registration number from the test output
                hospital.registration_number = 'H-643B7090'
                hospital.save()
                print(f"u2705 Updated hospital registration number: {hospital.registration_number}")
            else:
                print(f"Current hospital registration number: {hospital.registration_number}")
            
            # Define the correct emails
            admin_email = "admin.abujageneralhospital@example.com"  # This is the login email
            contact_email = "benemapp@gmail.com"  # This is the contact email
            
            # First, check if we have a hospital admin record
            admin = HospitalAdmin.objects.filter(hospital=hospital).first()
            
            if admin:
                print(f"Found hospital admin record with email: {admin.email}")
                
                # Update the admin record's email
                admin.email = admin_email
                admin.contact_email = contact_email
                admin.save(update_fields=['email', 'contact_email'])
                print(f"u2705 Updated hospital admin email and contact email")
                
                # Get the associated user
                admin_user = admin.user
                if admin_user:
                    print(f"Found associated user: {admin_user.email}")
                    
                    # Update the user's email if needed
                    if admin_user.email != admin_email:
                        admin_user.email = admin_email
                        admin_user.save(update_fields=['email'])
                        print(f"u2705 Updated user email to: {admin_email}")
                    
                    # Update password
                    admin_user.set_password('AbujaAdmin2025')
                    admin_user.save()
                    print(f"u2705 Updated password for user")
                else:
                    print("u274c Hospital admin has no associated user!")
                    return False
            else:
                print("u274c No hospital admin record found for this hospital!")
                return False
            
            print("\n" + "=" * 50)
            print("UPDATED ABUJA HOSPITAL ADMIN CREDENTIALS:")
            print("=" * 50)
            print(f"Hospital: {hospital.name}")
            print(f"Hospital Code: {hospital.registration_number}")
            print(f"Login Email: {admin_email}")
            print(f"Contact Email: {contact_email}")
            print(f"Password: AbujaAdmin2025")
            print("=" * 50)
            print("\nIMPORTANT: Use these credentials with the endpoint:")
            print("/api/hospitals/admin/login/")
            print("=" * 50)
            
            return True
        except Exception as e:
            print(f"u274c Error fixing admin credentials: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    print("Fixing Abuja hospital admin credentials...\n")
    
    if fix_abuja_admin_credentials():
        print("\nu2705 Successfully fixed Abuja hospital admin credentials!")
    else:
        print("\nu274c Failed to fix Abuja hospital admin credentials")

if __name__ == "__main__":
    main()
