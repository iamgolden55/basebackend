#!/usr/bin/env python
import os
import django
import sys
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model

User = get_user_model()

def create_user_account():
    """Create a user account with the essential fields"""
    try:
        # First check if user already exists
        if User.objects.filter(email='eruwagolden55@gmail.com').exists():
            user = User.objects.get(email='eruwagolden55@gmail.com')
            print(f"\n✅ User account already exists: {user.email}")
            
            # Update the password for testing
            response = input("Do you want to reset the password to 'PublicHealth24'? (y/n): ").strip().lower()
            if response == 'y':
                user.set_password('PublicHealth24')
                user.save()
                print("Password reset successfully!")
            return True
        
        # User doesn't exist, create it
        print("\nCreating user account...")
        
        # Determine what fields the User model has
        user_fields = [f.name for f in User._meta.get_fields()]
        
        # Create a dictionary with all potential fields
        user_data = {
            'email': 'eruwagolden55@gmail.com',
            'first_name': 'Ninioritse',
            'last_name': 'Great Eruwa',
            'is_active': True,
        }
        
        # Additional fields that might be in the model
        optional_fields = {
            'phone': '+2348035487113',
            'gender': 'male',
            'date_of_birth': '2000-09-20',
            'country': 'nigeria',
            'state': 'delta',
            'city': 'Asaba',
            'user_type': 'patient',
            'is_staff': False,
            'is_superuser': False,
        }
        
        # Add optional fields if they exist in the model
        for field, value in optional_fields.items():
            if field in user_fields:
                user_data[field] = value
        
        # Create the user with the appropriate fields
        user = User.objects.create(**user_data)
        
        # Set password
        user.set_password('PublicHealth24')
        user.save()
        
        print(f"\n✅ User account created successfully: {user.email}")
        return True
    except Exception as e:
        print(f"\n❌ Error creating user account: {e}")
        return False

def print_login_instructions():
    """Print login instructions"""
    print("\n" + "=" * 50)
    print("Login Information:")
    print("Email: eruwagolden55@gmail.com")
    print("Password: PublicHealth24")
    print("\nYou can now log in to the system with these credentials.")
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")
    print("=" * 50)

def main():
    print("\n" + "=" * 50)
    print("User Account Setup")
    print("=" * 50)
    
    # Create user account
    if create_user_account():
        print_login_instructions()
        return 0
    else:
        print("\n❌ Failed to create user account. Please contact support.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
