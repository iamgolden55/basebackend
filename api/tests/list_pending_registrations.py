import os
import django
import sys
from django.utils import timezone

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration

# List all pending registrations
try:
    # Find all pending registrations
    pending_registrations = HospitalRegistration.objects.filter(
        status='pending'
    ).select_related('user', 'hospital')
    
    if not pending_registrations:
        print("No pending registrations found in the system.")
        sys.exit(0)
    
    print(f"\nFound {pending_registrations.count()} pending registration(s):")
    
    for reg in pending_registrations:
        print(f"\nUser: {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
        print(f"Hospital: {reg.hospital.name}")
        print(f"Status: {reg.status}")
        print(f"Registration date: {reg.created_at}")
        print("-" * 50)
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
