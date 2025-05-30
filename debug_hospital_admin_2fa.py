# Script to debug hospital admin 2FA and provide a bypass for testing
import os
import django
import sys
import json
import pyotp
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.core.cache import cache
from django.utils import timezone
from api.models import Hospital, HospitalAdmin
from api.models.user.custom_user import CustomUser
from django.conf import settings

def check_email_settings():
    """Check the email settings in the Django configuration"""
    print("\n" + "=" * 50)
    print("EMAIL CONFIGURATION SETTINGS:")
    print("=" * 50)
    
    # Check if email backend is configured
    email_backend = getattr(settings, 'EMAIL_BACKEND', None)
    print(f"EMAIL_BACKEND: {email_backend}")
    
    # Check if email host is configured
    email_host = getattr(settings, 'EMAIL_HOST', None)
    print(f"EMAIL_HOST: {email_host}")
    
    # Check if email port is configured
    email_port = getattr(settings, 'EMAIL_PORT', None)
    print(f"EMAIL_PORT: {email_port}")
    
    # Check if email host user is configured
    email_host_user = getattr(settings, 'EMAIL_HOST_USER', None)
    print(f"EMAIL_HOST_USER: {email_host_user}")
    
    # Check if email host password is configured (don't print the actual password)
    email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    if email_host_password:
        print("EMAIL_HOST_PASSWORD: [CONFIGURED]")
    else:
        print("EMAIL_HOST_PASSWORD: [NOT CONFIGURED]")
    
    # Check if default from email is configured
    default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    print(f"DEFAULT_FROM_EMAIL: {default_from_email}")
    
    # Check if console email backend is being used (common in development)
    if email_backend == 'django.core.mail.backends.console.EmailBackend':
        print("\nNOTE: Using console email backend - emails are printed to console, not sent!")
        print("Check your terminal where the Django server is running to see the 2FA code.")
    
    # Check if file email backend is being used
    elif email_backend == 'django.core.mail.backends.filebased.EmailBackend':
        email_file_path = getattr(settings, 'EMAIL_FILE_PATH', None)
        print(f"\nNOTE: Using file email backend - emails are saved to: {email_file_path}")
        print(f"Check that directory for email files containing your 2FA code.")

def generate_2fa_bypass(email):
    """Generate a 2FA bypass by creating a valid cache entry"""
    # Get the Abuja hospital admin
    admin_email = "admin.abujageneralhospital@example.com"
    admin = HospitalAdmin.objects.filter(email=admin_email).first()
    
    if not admin:
        print(f"\n❌ Hospital admin with email {admin_email} not found!")
        return False
    
    print(f"\nGenerating 2FA bypass for: {admin_email}")
    
    # Generate a new TOTP secret and code
    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)
    verification_code = totp.now()
    
    # Store the code in cache with 10-minute expiry
    cache_key = f"hospital_admin_2fa_{admin_email}"
    cache_data = {
        'code': verification_code,
        'secret': totp_secret,
        'timestamp': timezone.now().timestamp(),
        'attempts': 0
    }
    
    cache.set(cache_key, cache_data, timeout=600)  # 10 minutes
    
    print("\n" + "=" * 50)
    print("2FA BYPASS INFORMATION:")
    print("=" * 50)
    print(f"Email: {admin_email}")
    print(f"2FA Code: {verification_code}")
    print(f"Valid for: 10 minutes")
    print("=" * 50)
    
    return True

def check_cache_for_2fa_codes():
    """Check if there are any 2FA codes in the cache"""
    print("\n" + "=" * 50)
    print("CHECKING CACHE FOR 2FA CODES:")
    print("=" * 50)
    
    # Get all keys in cache that match the pattern
    from django.core.cache.backends.locmem import LocMemCache
    
    # This is a bit of a hack to access the cache keys
    if isinstance(cache, LocMemCache):
        # For LocMemCache, we can access _cache directly
        all_keys = list(cache._cache.keys())
        
        # Filter for 2FA keys
        twofa_keys = [k for k in all_keys if 'hospital_admin_2fa_' in str(k)]
        
        if twofa_keys:
            print(f"Found {len(twofa_keys)} 2FA codes in cache:")
            for key in twofa_keys:
                data = cache.get(key)
                if data:
                    email = key.replace('hospital_admin_2fa_', '')
                    code = data.get('code', 'unknown')
                    timestamp = data.get('timestamp', 0)
                    if timestamp:
                        try:
                            time = datetime.fromtimestamp(timestamp)
                            time_str = time.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            time_str = 'unknown'
                    else:
                        time_str = 'unknown'
                    
                    print(f"Email: {email}")
                    print(f"Code: {code}")
                    print(f"Generated: {time_str}")
                    print("-" * 30)
        else:
            print("No 2FA codes found in cache.")
    else:
        print("Cannot access cache keys directly with this cache backend.")

def main():
    print("Hospital Admin 2FA Debug Tool\n")
    
    # Check email settings
    check_email_settings()
    
    # Check for existing 2FA codes
    check_cache_for_2fa_codes()
    
    # Generate a new 2FA bypass
    generate_2fa_bypass("admin.abujageneralhospital@example.com")
    
    print("\nIMPORTANT: When logging in at /api/hospitals/admin/login/")
    print("1. Use the credentials we fixed earlier")
    print("2. After successful login, you'll be prompted for 2FA")
    print("3. Use the 2FA code generated above")
    print("4. If you still don't receive the code, check the console where your Django server is running")

if __name__ == "__main__":
    main()
