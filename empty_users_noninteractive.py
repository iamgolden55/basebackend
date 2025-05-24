#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def empty_user_table():
    """Empty the user table and reset the sequence"""
    try:
        # Count existing users
        initial_count = User.objects.count()
        print(f"\nFound {initial_count} users in the database")
        
        # Get a list of user emails before deletion (for reporting)
        user_emails = list(User.objects.values_list('email', flat=True))
        print("\nUsers to be deleted:")
        for email in user_emails:
            print(f"  - {email}")
        
        # Delete all users
        print("\nDeleting all users...")
        User.objects.all().delete()
        
        # Reset the sequence
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('api_customuser_id_seq', 1, false)")
        
        # Verify deletion
        remaining_count = User.objects.count()
        print(f"\n\u2705 Successfully deleted all users. {remaining_count} users remaining.")
        print("\nYou can now create new users manually through the admin interface.")
        print("Remember that when you create a hospital admin user, the system will:")
        print("1. Automatically set up appropriate permissions")
        print("2. Configure the enhanced security features for hospital admins:")
        print("   - Domain validation for hospital email addresses")
        print("   - Required hospital code verification")
        print("   - Mandatory 2FA for all hospital admins")
        print("   - Enhanced security with trusted device tracking")
        print("3. Configure general login security features:")
        print("   - Rate limiting after 3 failed attempts")
        print("   - Account lockout for 15 minutes after 5 failed attempts")
        print("   - Email alerts for suspicious login attempts")
        
        return True
    except Exception as e:
        print(f"\n\u274c Error emptying user table: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    print("EMPTY USER TABLE - NON-INTERACTIVE")
    print("=" * 50)
    print("\nWARNING: This will delete ALL users from the database.")
    
    empty_user_table()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
