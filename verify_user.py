#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def verify_user(email):
    """Verify a user account by setting is_email_verified to True"""
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            print(f"\n\u274c User with email {email} not found.")
            return False
        
        # Set verification flags
        user.is_email_verified = True
        user.is_verified = True
        user.save()
        
        print(f"\n\u2705 User account {email} has been verified successfully!")
        return True
    except Exception as e:
        print(f"\n\u274c Error verifying user: {e}")
        return False

if __name__ == "__main__":
    email = "eruwagolden55@gmail.com"
    verify_user(email)
