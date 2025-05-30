import os
import django
import sys

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalRegistration, CustomUser

# Test what the API should be returning
try:
    admin_email = "admin.stnicholas65@example.com"
    
    # Get the admin user
    admin_user = CustomUser.objects.get(email=admin_email)
    print(f"✅ Admin user: {admin_user.email} (ID: {admin_user.id})")
    
    # Get admin's hospital
    try:
        hospital = Hospital.objects.get(user=admin_user)
        print(f"✅ Admin's hospital: {hospital.name} (ID: {hospital.id})")
        
        # Get registrations for this hospital
        pending_regs = HospitalRegistration.objects.filter(hospital=hospital, status='pending')
        approved_regs = HospitalRegistration.objects.filter(hospital=hospital, status='approved')
        
        print(f"\n📊 Registration counts for {hospital.name}:")
        print(f"   Pending: {pending_regs.count()}")
        print(f"   Approved: {approved_regs.count()}")
        
        if approved_regs.exists():
            print(f"\n👥 Approved users:")
            for reg in approved_regs:
                print(f"   - {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
                print(f"     Status: {reg.status}")
                print(f"     Approved: {reg.approved_date}")
        else:
            print("❌ No approved registrations found")
            
        if pending_regs.exists():
            print(f"\n⏳ Pending users:")
            for reg in pending_regs:
                print(f"   - {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
        else:
            print("✅ No pending registrations")
            
    except Hospital.DoesNotExist:
        print(f"❌ No hospital found for admin {admin_email}")
        print("Let me check the hospital link again...")
        hospitals = Hospital.objects.filter(user=admin_user)
        print(f"Hospitals linked to {admin_email}: {hospitals.count()}")
        for h in hospitals:
            print(f"   - {h.name} (ID: {h.id})")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
