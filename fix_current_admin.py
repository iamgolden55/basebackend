#!/usr/bin/env python3
"""
🔧 Fix Hospital Admin Primary Hospital Assignment for CURRENT USER
"""

import os
import django
import sys

# Setup Django environment
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import CustomUser, Hospital, HospitalRegistration

def fix_current_hospital_admin():
    """Fix hospital admin primary hospital assignment for user ID 11"""
    
    try:
        # Get the CURRENT logged in admin (ID 11)
        admin_user = CustomUser.objects.get(id=11)
        print(f"👤 Found current admin user: {admin_user.email}")
        
        # Get St. Nicholas Hospital
        hospital = Hospital.objects.filter(name__icontains="St. Nicholas").first()
        print(f"🏥 Found hospital: {hospital.name} (ID: {hospital.id})")
        
        # Check if registration exists
        existing_registration = HospitalRegistration.objects.filter(
            user=admin_user, 
            hospital=hospital
        ).first()
        
        if existing_registration:
            print(f"✅ Registration exists with status: {existing_registration.status}")
            if existing_registration.status != 'approved':
                existing_registration.status = 'approved'
                existing_registration.save()
                print("✅ Approved existing registration")
        else:
            # Create new registration
            registration = HospitalRegistration.objects.create(
                user=admin_user,
                hospital=hospital,
                status='approved',
                is_primary=True
            )
            print("✅ Created new approved registration")
        
        # Set as primary hospital
        admin_user.hospital = hospital
        admin_user.save()
        print(f"✅ Set {hospital.name} as primary hospital for {admin_user.email}")
        
        # Test the fix
        print(f"\n🧪 Testing fix:")
        print(f"   User hospital: {admin_user.hospital.name if admin_user.hospital else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_current_hospital_admin():
        print("\n🎉 Current hospital admin assignment fixed!")
        print("🔄 Refresh your dashboard to see real data!")
    else:
        print("\n💥 Failed to fix current hospital admin assignment")
