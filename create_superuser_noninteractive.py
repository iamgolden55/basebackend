#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Predefined superuser details
SUPER_EMAIL = "admin@example.com"  # Change this if needed
SUPER_PASSWORD = "AdminPassword123"  # Strong default password
SUPER_FIRST_NAME = "Admin"
SUPER_LAST_NAME = "User"

def create_superuser_noninteractive():
    """Create a Django superuser account without interaction"""
    try:
        # Check if a superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("\n\u26A0 A superuser already exists. These are the current superusers:")
            for user in User.objects.filter(is_superuser=True):
                print(f"  - {user.email}")
            return True
        
        # Check if user with this email already exists
        if User.objects.filter(email=SUPER_EMAIL).exists():
            existing_user = User.objects.get(email=SUPER_EMAIL)
            print(f"\n\u26A0 User with email {SUPER_EMAIL} already exists.")
            
            if existing_user.is_superuser:
                print("This user is already a superuser.")
                return True
            
            # Make existing user a superuser
            existing_user.is_superuser = True
            existing_user.is_staff = True
            existing_user.set_password(SUPER_PASSWORD)
            existing_user.save()
            print(f"\n\u2705 User {SUPER_EMAIL} is now a superuser!")
            return True
        
        # Create the superuser
        superuser = User.objects.create_superuser(
            email=SUPER_EMAIL,
            password=SUPER_PASSWORD,
            first_name=SUPER_FIRST_NAME,
            last_name=SUPER_LAST_NAME
        )
        
        print(f"\n\u2705 Superuser {SUPER_EMAIL} created successfully!")
        print("\nSuperuser credentials:")
        print(f"Email: {SUPER_EMAIL}")
        print(f"Password: {SUPER_PASSWORD}")
        print("\nYou can now use this account to access the Django admin interface.")
        return True
    
    except Exception as e:
        print(f"\n\u274C Error creating superuser: {e}")
        return False

def main():
    if create_superuser_noninteractive():
        print("\n" + "=" * 50)
        print("Django Admin Access Information")
        print("=" * 50)
        print("\nYou can access the Django admin interface at:")
        print("http://127.0.0.1:8000/admin/")
        print("\nLog in with your superuser credentials.")
        print("=" * 50)
        return 0
    else:
        print("\n\u274C Failed to create superuser.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
