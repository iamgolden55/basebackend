#!/usr/bin/env python
import os
import sys
import django

# Add the project root directory to the Python path
sys.path.insert(0, '/Users/new/Newphb/basebackend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# Setup Django
django.setup()

from api.models import HospitalRegistration, CustomUser

# Debug user registration
print("🔍 DEBUGGING USER HOSPITAL REGISTRATION...")

# Get user ID 11 (from your token)
try:
    user = CustomUser.objects.get(id=11)
    print(f"✅ Found user: {user.email}")
    
    # Check all registrations for this user
    all_registrations = HospitalRegistration.objects.filter(user=user)
    print(f"📊 Total registrations for user: {all_registrations.count()}")
    
    for reg in all_registrations:
        print(f"  - Hospital: {reg.hospital.name} (ID: {reg.hospital.id})")
        print(f"    Status: {reg.status}")
        print(f"    Is Primary: {reg.is_primary}")
        print(f"    Created: {reg.created_at}")
        print(f"    Approved: {reg.approved_date}")
        print()
    
    # Check for primary registration
    primary_reg = HospitalRegistration.objects.filter(
        user=user,
        is_primary=True,
        status='approved'
    ).first()
    
    if primary_reg:
        print(f"✅ Found primary registration: {primary_reg.hospital.name}")
        
        # Check if hospital has departments
        departments = primary_reg.hospital.departments.all()
        print(f"🏥 Departments in {primary_reg.hospital.name}: {departments.count()}")
        
        for dept in departments:
            print(f"  - {dept.name} ({dept.code})")
            print(f"    Beds: {dept.total_beds} total, {dept.available_beds} available")
    else:
        print("❌ NO PRIMARY REGISTRATION FOUND!")
        print("🔍 Checking reasons...")
        
        # Check each registration individually
        for reg in all_registrations:
            issues = []
            if not reg.is_primary:
                issues.append("not marked as primary")
            if reg.status != 'approved':
                issues.append(f"status is '{reg.status}' instead of 'approved'")
            
            if issues:
                print(f"  ❌ {reg.hospital.name}: {', '.join(issues)}")
            else:
                print(f"  ✅ {reg.hospital.name}: should work as primary!")

except CustomUser.DoesNotExist:
    print("❌ User with ID 11 not found!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
