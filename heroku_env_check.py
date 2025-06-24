#!/usr/bin/env python
"""
Heroku Environment Variables Checker
"""
import os
import sys

# Required environment variables for production
REQUIRED_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',  # Heroku Postgres provides this
    'DJANGO_SETTINGS_MODULE',
    'ALLOWED_HOST',
]

# Optional but recommended variables
OPTIONAL_VARS = [
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD', 
    'PAYSTACK_SECRET_KEY',
    'PAYSTACK_PUBLIC_KEY',
    'FRONTEND_URLS',
    'REDIS_URL',
    'DEBUG'
]

def check_heroku_env():
    print("🔍 Checking Heroku Environment Variables...")
    print("=" * 50)
    
    missing_required = []
    missing_optional = []
    
    print("\n✅ REQUIRED Variables:")
    for var in REQUIRED_VARS:
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}: {'*' * min(len(value), 20)}")
        else:
            print(f"  ❌ {var}: MISSING")
            missing_required.append(var)
    
    print("\n🔧 OPTIONAL Variables:")
    for var in OPTIONAL_VARS:
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}: {'*' * min(len(value), 20)}")
        else:
            print(f"  ⚠️  {var}: Not set")
            missing_optional.append(var)
    
    print("\n" + "=" * 50)
    
    if missing_required:
        print(f"❌ CRITICAL: {len(missing_required)} required variables missing!")
        print("These MUST be set for deployment to work:")
        for var in missing_required:
            print(f"  - {var}")
        return False
    else:
        print("✅ All required variables are set!")
        
    if missing_optional:
        print(f"⚠️  {len(missing_optional)} optional variables not set.")
        print("Consider setting these for full functionality:")
        for var in missing_optional:
            print(f"  - {var}")
    
    return True

if __name__ == "__main__":
    success = check_heroku_env()
    sys.exit(0 if success else 1)
