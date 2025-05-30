import os
import django
import sys

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalRegistration, CustomUser

# Find the admin user and their hospital
try:
    admin_email = "admin.stnicholas65@example.com"
    
    # Find the admin user
    try:
        admin_user = CustomUser.objects.get(email=admin_email)
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print(f"   User ID: {admin_user.id}")
    except CustomUser.DoesNotExist:
        print(f"❌ Admin user {admin_email} not found")
        print("Let me check what admin users exist:")
        admins = CustomUser.objects.filter(role='hospital_admin')
        for admin in admins:
            print(f"   - {admin.email} (ID: {admin.id})")
        sys.exit()
    
    # Find which hospital this admin is associated with
    hospitals = Hospital.objects.filter(user=admin_user)
    print(f"\n🏥 Hospitals associated with {admin_email}:")
    
    if not hospitals.exists():
        print("❌ No hospitals found for this admin")
        print("Let me check all hospitals and their associated users:")
        all_hospitals = Hospital.objects.all()
        for h in all_hospitals:
            print(f"   - {h.name} (ID: {h.id}) -> User: {h.user.email if h.user else 'None'}")
    else:
        for hospital in hospitals:
            print(f"   - {hospital.name} (ID: {hospital.id})")
            
            # Check registrations for this hospital
            registrations = HospitalRegistration.objects.filter(hospital=hospital)
            print(f"     Registrations: {registrations.count()}")
            
            for reg in registrations:
                print(f"       - {reg.user.email} ({reg.status})")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
