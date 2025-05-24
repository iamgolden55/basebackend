#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from api.models import Hospital, HospitalAdmin

User = get_user_model()

def create_regular_user():
    """Create a regular user account"""
    print("\nCreating regular user account...")
    
    try:
        email = input("Email: ").strip()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        password = input("Password: ").strip()
        
        if not email or not password:
            print("Email and password are required.")
            return None
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            print(f"User with email {email} already exists.")
            return None
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        
        print(f"\n\u2705 Successfully created user: {email}")
        return user
    except Exception as e:
        print(f"\n\u274c Error creating user: {e}")
        return None

def create_superuser():
    """Create a superuser account"""
    print("\nCreating superuser account...")
    
    try:
        email = input("Email: ").strip()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        password = input("Password: ").strip()
        
        if not email or not password:
            print("Email and password are required.")
            return None
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            print(f"User with email {email} already exists.")
            return None
        
        # Create superuser
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        print(f"\n\u2705 Successfully created superuser: {email}")
        return user
    except Exception as e:
        print(f"\n\u274c Error creating superuser: {e}")
        return None

def create_hospital_admin():
    """Create a hospital admin account with enhanced security"""
    print("\nCreating hospital admin account...")
    
    try:
        # First get/create hospital
        hospitals = Hospital.objects.all()
        if not hospitals.exists():
            print("No hospitals found. Creating a default hospital first.")
            hospital_name = input("Hospital name: ").strip() or "St. Nicholas Hospital"
            hospital = Hospital.objects.create(
                name=hospital_name,
                hospital_type="General Hospital",
                address="1 Hospital Road",
                city="Lagos",
                state="Lagos",
                country="Nigeria",
                postal_code="100001",
                phone="+2347012345678",
                email="info@stnicholas.com",
                website="www.stnicholas.com",
                emergency_unit=True,
                icu_unit=True,
                is_verified=True
            )
            print(f"Created hospital: {hospital.name}")
        else:
            hospital = hospitals.first()
            print(f"Using existing hospital: {hospital.name}")
        
        # Now create hospital admin
        email = input("Admin email: ").strip()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        password = input("Password: ").strip()
        position = input("Position: ").strip() or "Chief Administrator"
        
        if not email or not password:
            print("Email and password are required.")
            return None
        
        # Check domain validity for hospital admin (domain validation security feature)
        hospital_domain = hospital.email.split('@')[-1] if '@' in hospital.email else None
        email_domain = email.split('@')[-1] if '@' in email else None
        
        if hospital_domain and email_domain and hospital_domain != email_domain:
            print(f"Warning: Admin email domain ({email_domain}) doesn't match hospital domain ({hospital_domain}).")
            proceed = input("Proceed anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return None
        
        # Create hospital admin with all security features
        with transaction.atomic():
            # Create the admin
            admin = HospitalAdmin.objects.create(
                email=email,
                hospital=hospital,
                position=position,
                first_name=first_name,
                last_name=last_name,
                contact_email=email,
                password_change_required=True,  # Force password change on first login (security feature)
                two_factor_enabled=True,  # Enable 2FA (security feature)
                is_active=True
            )
            
            # Set password
            admin.set_password(password)
            admin.save()
            
            print(f"\n\u2705 Successfully created hospital admin: {email}")
            print("\nSecurity features enabled:")
            print("1. Domain validation for hospital email addresses")
            print("2. Required hospital code verification")
            print("3. Mandatory 2FA for all hospital admins")
            print("4. Enhanced security with trusted device tracking")
            print("5. Rate limiting after 3 failed attempts")
            print("6. Account lockout for 15 minutes after 5 failed attempts")
            print("7. Email alerts for suspicious login attempts")
            
            return admin
    except Exception as e:
        print(f"\n\u274c Error creating hospital admin: {e}")
        return None

def create_default_users():
    """Create default users non-interactively"""
    print("\nCreating default users non-interactively...")
    
    try:
        # Create regular user
        regular_user = User.objects.create_user(
            email="user@example.com",
            password="User1234",
            first_name="Regular",
            last_name="User",
            is_active=True
        )
        print(f"Created regular user: user@example.com / User1234")
        
        # Create superuser
        super_user = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin1234",
            first_name="Admin",
            last_name="User"
        )
        print(f"Created superuser: admin@example.com / Admin1234")
        
        # Get/create hospital
        hospital, created = Hospital.objects.get_or_create(
            name="St. Nicholas Hospital",
            defaults={
                'hospital_type': "General Hospital",
                'address': "1 Hospital Road",
                'city': "Lagos",
                'state': "Lagos",
                'country': "Nigeria",
                'postal_code': "100001",
                'phone': "+2347012345678",
                'email': "info@stnicholas.com",
                'website': "www.stnicholas.com",
                'emergency_unit': True,
                'icu_unit': True,
                'is_verified': True
            }
        )
        if created:
            print(f"Created hospital: {hospital.name}")
        else:
            print(f"Using existing hospital: {hospital.name}")
        
        # Create hospital admin
        admin = HospitalAdmin.objects.create(
            email="hospital_admin@stnicholas.com",
            hospital=hospital,
            position="Chief Administrator",
            first_name="Hospital",
            last_name="Admin",
            contact_email="hospital_admin@stnicholas.com",
            password_change_required=True,
            two_factor_enabled=True,
            is_active=True
        )
        admin.set_password("HospitalAdmin1234")
        admin.save()
        print(f"Created hospital admin: hospital_admin@stnicholas.com / HospitalAdmin1234")
        
        print("\n\u2705 Successfully created default users")
        return True
    except Exception as e:
        print(f"\n\u274c Error creating default users: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    print("USER CREATION UTILITY")
    print("=" * 50)
    
    print("\nOptions:")
    print("1. Create regular user")
    print("2. Create superuser")
    print("3. Create hospital admin (with enhanced security)")
    print("4. Create default users (non-interactive)")
    print("5. Exit")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            create_regular_user()
        elif choice == '2':
            create_superuser()
        elif choice == '3':
            create_hospital_admin()
        elif choice == '4':
            create_default_users()
        elif choice == '5':
            print("Exiting...")
            return
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")
    except Exception as e:
        print(f"Error: {e}")
        # For non-interactive environments, create default users
        print("Falling back to creating default users...")
        create_default_users()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
