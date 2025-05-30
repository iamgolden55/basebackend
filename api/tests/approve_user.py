import os
import django
import sys
from django.utils import timezone

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration, CustomUser

# Get user email from command line argument or use default
if len(sys.argv) > 1:
    user_email = sys.argv[1]
else:
    # List available pending registrations
    pending_registrations = HospitalRegistration.objects.filter(
        status='pending'
    ).select_related('user', 'hospital')
    
    if not pending_registrations:
        print("No pending registrations found in the system.")
        sys.exit(0)
    
    print(f"\nFound {pending_registrations.count()} pending registration(s):")
    
    for i, reg in enumerate(pending_registrations, 1):
        print(f"{i}. User: {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
        print(f"   Hospital: {reg.hospital.name}")
        print(f"   Registration date: {reg.created_at}")
    
    print("\nPlease run the script again with the user email as an argument:")
    print("Example: python approve_user.py eruwagolden@gmail.com")
    sys.exit(0)

try:
    # Find the registration
    registration = HospitalRegistration.objects.filter(
        user__email=user_email,
        status='pending'
    ).select_related('user', 'hospital').first()
    
    if not registration:
        print(f"No pending registration found for {user_email}")
        sys.exit(1)
    
    # Display registration details before approval
    print(f"\nFound registration for {registration.user.first_name} {registration.user.last_name}")
    print(f"Hospital: {registration.hospital.name}")
    print(f"Status: {registration.status}")
    print(f"Registration date: {registration.created_at}")
    
    # Approve the registration
    registration.status = 'approved'
    registration.approved_date = timezone.now()
    registration.save()
    
    print(f"\nRegistration APPROVED successfully!")
    print(f"New status: {registration.status}")
    print(f"Approval date: {registration.approved_date}")
    
    # Check if this is the user's only approved registration
    other_approved = HospitalRegistration.objects.filter(
        user=registration.user,
        status='approved'
    ).exclude(id=registration.id).exists()
    
    # Set as primary if it's the only approved registration
    if not other_approved and not registration.is_primary:
        registration.is_primary = True
        registration.save()
        print("\nThis is now set as the user's primary hospital")
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
