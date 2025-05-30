import os
import django
import sys

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, CustomUser

# Link admin user to Hospital ID: 2
try:
    admin_email = "admin.stnicholas65@example.com"
    
    # Get the admin user
    admin_user = CustomUser.objects.get(email=admin_email)
    print(f"✅ Found admin user: {admin_user.email} (ID: {admin_user.id})")
    
    # Get Hospital ID: 2 (the one with registrations)
    hospital = Hospital.objects.get(id=2)
    print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
    
    # Link them
    hospital.user = admin_user
    hospital.save()
    
    print(f"🎉 SUCCESS! Linked {admin_user.email} to {hospital.name}")
    print(f"   Hospital {hospital.name} (ID: {hospital.id}) now belongs to {admin_user.email}")
    
    # Verify the link
    verification = Hospital.objects.get(id=2)
    if verification.user and verification.user.email == admin_email:
        print("✅ Verification: Link successful!")
    else:
        print("❌ Verification: Link failed!")
        
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
