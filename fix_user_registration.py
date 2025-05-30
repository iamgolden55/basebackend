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

from api.models import HospitalRegistration, CustomUser, Hospital
from django.utils import timezone

print("🔧 FIXING USER HOSPITAL REGISTRATION...")

try:
    # Get user ID 11
    user = CustomUser.objects.get(id=11)
    print(f"✅ Found user: {user.email}")
    
    # Get St. Nicholas Hospital
    hospital = Hospital.objects.get(name="St. Nicholas Hospital")
    print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
    
    # Check if registration already exists
    existing_reg = HospitalRegistration.objects.filter(
        user=user,
        hospital=hospital
    ).first()
    
    if existing_reg:
        print(f"⚠️  Registration already exists:")
        print(f"   Status: {existing_reg.status}")
        print(f"   Is Primary: {existing_reg.is_primary}")
        
        # Update it to be approved and primary
        existing_reg.status = 'approved'
        existing_reg.is_primary = True
        existing_reg.approved_date = timezone.now()
        existing_reg.save()
        print("✅ Updated existing registration to approved and primary!")
    else:
        # Create new registration
        registration = HospitalRegistration.objects.create(
            user=user,
            hospital=hospital,
            is_primary=True,
            status='approved',
            approved_date=timezone.now()
        )
        print("✅ Created new approved primary hospital registration!")
        print(f"   Registration ID: {registration.id}")
    
    # Verify the fix
    primary_reg = HospitalRegistration.objects.filter(
        user=user,
        is_primary=True,
        status='approved'
    ).first()
    
    if primary_reg:
        print(f"🎉 SUCCESS! User now has primary registration with {primary_reg.hospital.name}")
        
        # Check departments
        departments = primary_reg.hospital.departments.all()
        print(f"🏥 Available departments: {departments.count()}")
        for dept in departments[:3]:  # Show first 3
            print(f"   - {dept.name}: {dept.available_beds} beds available")
    else:
        print("❌ Fix failed - still no primary registration")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
