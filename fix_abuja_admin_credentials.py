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
                print("❌ Abuja General Hospital not found!")
                return False
                
            print(f"Found hospital: {hospital.name}")
            
            # Check if hospital has registration number
            if not hospital.registration_number or not hospital.registration_number.startswith('H-'):
                # Update with the registration number from the test output
                hospital.registration_number = 'H-643B7090'
                hospital.save()
                print(f"✅ Updated hospital registration number: {hospital.registration_number}")
            else:
                print(f"Current hospital registration number: {hospital.registration_number}")
            
            # Get the admin user
            admin_email = "admin.abujageneralhospital@example.com"  # This is the login email
            contact_email = "benemapp@gmail.com"  # This is the contact email
            
            # Find the admin user
            admin_user = CustomUser.objects.filter(email=admin_email).first()
            
            if not admin_user:
                # Try to find by contact email
                possible_user = CustomUser.objects.filter(email=contact_email).first()
                
                if possible_user and possible_user.role == 'hospital_admin':
                    # Update the email to match the login format
                    print(f"Found admin user with contact email: {possible_user.email}")
                    print(f"Updating to standardized login email: {admin_email}")
                    possible_user.email = admin_email
                    possible_user.save()
                    admin_user = possible_user
                else:
                    # Create a new admin user with the correct email
                    print(f"Creating new admin user with email: {admin_email}")
                    admin_user = CustomUser.objects.create(
                        email=admin_email,
                        first_name='Abuja',
                        last_name='Admin',
                        role='hospital_admin',
                        is_staff=True,
                        is_email_verified=True,
                        preferred_language='en',
                        country='Nigeria',
                        state='FCT',
                        city='Abuja',
                        phone='+2348012345678',
                        consent_terms=True,
                        consent_hipaa=True,
                        consent_data_processing=True
                    )
            else:
                print(f"Found admin user: {admin_user.email}")
            
            # Set or update the password
            admin_user.set_password('AbujaAdmin2025')
            admin_user.save()
            print(f"✅ Updated password for admin user: {admin_user.email}")
            
            # Check if HospitalAdmin exists
            admin = HospitalAdmin.objects.filter(hospital=hospital).first()
            
            if admin:
                # Update the admin record
                print(f"Found hospital admin record: {admin.email}")
                
                # Update the email to match the login format
                admin.email = admin_email
                
                # Make sure contact_email is set correctly
                admin.contact_email = contact_email
                
                # Make sure user is linked correctly
                admin.user = admin_user
                
                # Make sure hospital is linked correctly
                admin.hospital = hospital
                
                admin.save()
                print(f"✅ Updated hospital admin record")
            else:
                # Create new HospitalAdmin
                print(f"Creating new hospital admin record")
                admin = HospitalAdmin.objects.create(
                    user=admin_user,
                    hospital=hospital,
                    email=admin_email,
                    contact_email=contact_email,
                    position='Chief Administrator',
                    name='Abuja Admin',
                    password_change_required=False
                )
                print(f"✅ Created hospital admin record")
            
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
            print(f"❌ Error fixing admin credentials: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    print("Fixing Abuja hospital admin credentials...\n")
    
    if fix_abuja_admin_credentials():
        print("\n✅ Successfully fixed Abuja hospital admin credentials!")
    else:
        print("\n❌ Failed to fix Abuja hospital admin credentials")

if __name__ == "__main__":
    main()
