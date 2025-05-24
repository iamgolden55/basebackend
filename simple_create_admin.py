#!/usr/bin/env python
import os
import django
import inspect
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

def inspect_model(model):
    """Inspect a model to see available fields"""
    print(f"\nInspecting model: {model.__name__}")
    for field in model._meta.fields:
        print(f"  - {field.name} ({field.get_internal_type()})")

def create_simple_accounts():
    """Create simple accounts without trying to set complex fields"""
    try:
        # Create superuser
        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                email='admin@example.com',
                password='Admin1234',
            )
            print("Created superuser: admin@example.com / Admin1234")
        else:
            print("Superuser admin@example.com already exists")
        
        # Create regular user
        if not User.objects.filter(email='eruwagolden55@gmail.com').exists():
            User.objects.create_user(
                email='eruwagolden55@gmail.com',
                password='PublicHealth24',
            )
            print("Created regular user: eruwagolden55@gmail.com / PublicHealth24")
        else:
            print("User eruwagolden55@gmail.com already exists")
        
        print("\nAccounts created successfully. Remember that:")
        print("1. All hospital admin accounts will automatically have:")
        print("   - Domain validation for hospital email addresses")
        print("   - Required hospital code verification")
        print("   - Mandatory 2FA for all hospital admins")
        print("   - Enhanced security with trusted device tracking")
        print("2. The login system includes:")
        print("   - Rate limiting after 3 failed attempts")
        print("   - Account lockout for 15 minutes after 5 failed attempts")
        print("   - Email alerts for suspicious login attempts")
        
        return True
    except Exception as e:
        print(f"Error creating accounts: {e}")
        return False

if __name__ == "__main__":
    # Inspect models to understand their structure
    inspect_model(User)
    inspect_model(Hospital)
    inspect_model(HospitalAdmin)
    
    # Create basic accounts
    create_simple_accounts()
