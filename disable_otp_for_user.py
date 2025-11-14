#!/usr/bin/env python
"""
Script to disable OTP requirement for a user account
Useful for test accounts that need quick login without OTP verification
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def disable_otp_for_user(email):
    """Disable OTP requirement for a specific user"""

    try:
        user = User.objects.get(email=email)

        print('='*70)
        print(f'Disabling OTP for: {email}')
        print('='*70)
        print(f'User: {user.first_name} {user.last_name}')
        print(f'Role: {user.role}')
        print(f'Current OTP Required: {user.otp_required_for_login}')
        print()

        # Disable OTP
        user.otp_required_for_login = False
        user.otp = None
        user.otp_created_at = None
        user.save()

        print('✅ OTP requirement disabled!')
        print()
        print('Updated Settings:')
        print(f'  OTP Required: {user.otp_required_for_login}')
        print(f'  OTP Code: {user.otp}')
        print('='*70)

        return True

    except User.DoesNotExist:
        print(f'❌ Error: User with email {email} not found')
        return False
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return False

def enable_otp_for_user(email):
    """Enable OTP requirement for a specific user"""

    try:
        user = User.objects.get(email=email)

        print('='*70)
        print(f'Enabling OTP for: {email}')
        print('='*70)

        # Enable OTP
        user.otp_required_for_login = True
        user.save()

        print('✅ OTP requirement enabled!')
        print(f'  OTP Required: {user.otp_required_for_login}')
        print('='*70)

        return True

    except User.DoesNotExist:
        print(f'❌ Error: User with email {email} not found')
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  Disable OTP: python disable_otp_for_user.py <email>')
        print('  Enable OTP:  python disable_otp_for_user.py <email> --enable')
        print()
        print('Examples:')
        print('  python disable_otp_for_user.py dr.emmanuel.okonkwo@phb-test.com')
        print('  python disable_otp_for_user.py patient@example.com --enable')
        sys.exit(1)

    email = sys.argv[1]
    enable = '--enable' in sys.argv

    if enable:
        enable_otp_for_user(email)
    else:
        disable_otp_for_user(email)
