import os
import django
import sys
from django.utils import timezone

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration, Hospital

# List all approved registrations for St. Nicholas Hospital
try:
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains="St. Nicholas").first()
    
    if not hospital:
        print("St. Nicholas Hospital not found. Let me list all hospitals:")
        hospitals = Hospital.objects.all()
        for h in hospitals:
            print(f"- {h.name}")
        sys.exit(0)
    
    print(f"Found hospital: {hospital.name}")
    
    # Find all registrations for this hospital
    all_registrations = HospitalRegistration.objects.filter(
        hospital=hospital
    ).select_related('user')
    
    if not all_registrations:
        print("No registrations found for this hospital.")
    else:
        print(f"\nTotal registrations for {hospital.name}: {all_registrations.count()}")
        
        pending = all_registrations.filter(status='pending')
        approved = all_registrations.filter(status='approved')
        
        print(f"- Pending: {pending.count()}")
        print(f"- Approved: {approved.count()}")
        
        if approved.exists():
            print(f"\nApproved users:")
            for reg in approved:
                print(f"- {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
                print(f"  Approved on: {reg.approved_date}")
                print(f"  Primary: {'Yes' if reg.is_primary else 'No'}")
        
        if pending.exists():
            print(f"\nPending users:")
            for reg in pending:
                print(f"- {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
                print(f"  Registered on: {reg.created_at}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
