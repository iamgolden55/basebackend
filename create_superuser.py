#!/usr/bin/env python
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Create a Django superuser account"""
    try:
        # Check if a superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("\n\u26A0 A superuser already exists. These are the current superusers:")
            for user in User.objects.filter(is_superuser=True):
                print(f"  - {user.email}")
            
            create_new = input("\nDo you want to create another superuser? (y/n): ").strip().lower()
            if create_new != 'y':
                return False
        
        # Get user input for superuser details
        print("\n" + "=" * 50)
        print("Django Superuser Creation")
        print("=" * 50)
        
        email = input("\nEmail address: ").strip()
        
        # Validate email
        if not email or '@' not in email:
            print("\n\u274C Invalid email address!")
            return False
        
        # Check if user with this email already exists
        if User.objects.filter(email=email).exists():
            existing_user = User.objects.get(email=email)
            print(f"\n\u26A0 User with email {email} already exists.")
            
            if existing_user.is_superuser:
                print("This user is already a superuser.")
                return True
            
            # Make existing user a superuser
            make_super = input("Do you want to make this user a superuser? (y/n): ").strip().lower()
            if make_super == 'y':
                existing_user.is_superuser = True
                existing_user.is_staff = True
                
                # Set password
                password = input("New password: ")
                if password:
                    existing_user.set_password(password)
                
                existing_user.save()
                print(f"\n\u2705 User {email} is now a superuser!")
                return True
            else:
                return False
        
        # Get remaining details for new user
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        password = input("Password: ").strip()
        
        if not password:
            print("\n\u274C Password cannot be empty!")
            return False
        
        # Create the superuser
        superuser = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        print(f"\n\u2705 Superuser {email} created successfully!")
        print("You can now use this account to access the Django admin interface.")
        return True
    
    except Exception as e:
        print(f"\n\u274C Error creating superuser: {e}")
        return False

def main():
    if create_superuser():
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
