import os
import django
import sys

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalRegistration

# List all St. Nicholas hospitals and their registrations
try:
    st_nicholas_hospitals = Hospital.objects.filter(name__icontains="St. Nicholas")
    
    print(f"Found {st_nicholas_hospitals.count()} St. Nicholas hospitals:")
    print("=" * 60)
    
    for hospital in st_nicholas_hospitals:
        print(f"\n🏥 Hospital: {hospital.name}")
        print(f"   ID: {hospital.id}")
        
        # Check what fields are available
        available_fields = [field.name for field in hospital._meta.fields]
        print(f"   Available fields: {available_fields}")
        
        # Get registrations for this hospital
        registrations = HospitalRegistration.objects.filter(hospital=hospital)
        pending = registrations.filter(status='pending')
        approved = registrations.filter(status='approved')
        
        print(f"   📊 Registrations: {registrations.count()} total")
        print(f"      - Pending: {pending.count()}")
        print(f"      - Approved: {approved.count()}")
        
        if approved.exists():
            print(f"   👥 Approved Users:")
            for reg in approved:
                print(f"      - {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
        
        print("-" * 60)
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
