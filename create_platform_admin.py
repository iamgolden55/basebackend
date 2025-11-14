#!/usr/bin/env python
"""
Create a Platform Admin user for the admin dashboard.
Run with: python create_platform_admin.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.user.custom_user import CustomUser
from api.models.user.role import Role

def create_platform_admin():
    """Create a Platform Admin user."""

    # Check if Platform Admin role exists
    try:
        platform_admin_role = Role.objects.get(name='Platform Admin')
        print(f"✅ Found Platform Admin role: {platform_admin_role.name}")
    except Role.DoesNotExist:
        print("❌ Platform Admin role not found!")
        print("Please run migrations first:")
        print("  python manage.py migrate")
        return

    # Check if user already exists
    email = 'platformadmin@phb.com'
    if CustomUser.objects.filter(email=email).exists():
        print(f"⚠️  User with email {email} already exists!")
        print(f"📝 Updating existing user to Platform Admin role...")
        user = CustomUser.objects.get(email=email)
        user.registry_role = platform_admin_role
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"✅ Updated existing user: {user.email}")
        print(f"   Registry Role: {user.registry_role.name}")
        print(f"   Permissions: {user.registry_role.permissions}")
        print(f"\n🔐 Use these credentials to login to the admin dashboard:")
        print(f"   http://localhost:3000")
        print(f"   Email: {user.email}")
        print(f"   Password: Admin123! (if unchanged)")
        return

    # Create new Platform Admin user
    print(f"\n📝 Creating Platform Admin user...")
    admin_user = CustomUser.objects.create_user(
        email=email,
        password='Admin123!',
        first_name='Platform',
        last_name='Admin',
        is_staff=True,
        is_superuser=True
    )

    # Assign Platform Admin role (use registry_role, not role)
    admin_user.registry_role = platform_admin_role
    admin_user.role = 'admin'  # Set the old role field to 'admin'
    admin_user.save()

    print(f"\n✅ Successfully created Platform Admin user!")
    print(f"   Email: {admin_user.email}")
    print(f"   Password: Admin123!")
    print(f"   Registry Role: {admin_user.registry_role.name}")
    print(f"   Permissions: {admin_user.registry_role.permissions}")
    print(f"\n🔐 Use these credentials to login to the admin dashboard:")
    print(f"   http://localhost:3000")
    print(f"   Email: {admin_user.email}")
    print(f"   Password: Admin123!")
    print(f"\n⚠️  IMPORTANT: Change the password after first login!")

if __name__ == '__main__':
    create_platform_admin()
