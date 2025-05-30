import os
import django
import sys

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalRegistration, CustomUser

# Find the problematic view logic and test the fix
try:
    admin_email = "admin.stnicholas65@example.com"
    
    # Get the admin user
    admin_user = CustomUser.objects.get(email=admin_email)
    print(f"✅ Admin user: {admin_user.email}")
    print(f"   Role: {admin_user.role}")
    print(f"   Has hospital attribute: {hasattr(admin_user, 'hospital')}")
    
    # The WRONG way (current code):
    try:
        wrong_hospital = admin_user.hospital
        print(f"❌ user.hospital exists: {wrong_hospital}")
    except AttributeError:
        print("❌ user.hospital does NOT exist (AttributeError)")
    
    # The RIGHT way (what we need):
    admin_hospital = Hospital.objects.filter(user=admin_user).first()
    if admin_hospital:
        print(f"✅ Correct approach - admin's hospital: {admin_hospital.name} (ID: {admin_hospital.id})")
        
        # Test the corrected queryset
        registrations = HospitalRegistration.objects.filter(
            hospital=admin_hospital
        ).select_related('user', 'hospital')
        
        print(f"✅ Registrations found: {registrations.count()}")
        for reg in registrations:
            print(f"   - {reg.user.email} ({reg.status})")
    else:
        print("❌ No hospital found for this admin")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
