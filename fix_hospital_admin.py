#!/usr/bin/env python3
"""
🔧 Fix Hospital Admin Primary Hospital Assignment
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

def fix_hospital_admin_assignment():
    """Fix hospital admin primary hospital assignment"""
    
    try:
        # Get the hospital admin who is currently logged in (info@stnicholas.com)
        admin_user = CustomUser.objects.get(email='info@stnicholas.com')
        print(f"👤 Found admin user: {admin_user.email}")
        
        # Get St. Nicholas Hospital (there are duplicates, let's use ID 2 or 3)
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
    if fix_hospital_admin_assignment():
        print("\n🎉 Hospital admin assignment fixed!")
        print("🔄 The dashboard should now show real data!")
    else:
        print("\n💥 Failed to fix hospital admin assignment")
