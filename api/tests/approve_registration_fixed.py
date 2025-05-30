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

# Hospital name to check for pending registrations
hospital_name = "Abuja General Hospital"

try:
    # Find all pending registrations for the specified hospital
    pending_registrations = HospitalRegistration.objects.filter(
        status='pending',
        hospital__name=hospital_name
    ).select_related('user', 'hospital')
    
    if not pending_registrations:
        print(f"No pending registrations found for {hospital_name}.")
        sys.exit(0)
    
    print(f"\nFound {pending_registrations.count()} pending registration(s) for {hospital_name}:")
    
    # Get the first pending registration
    registration = pending_registrations.first()
    
    # Display registration details before approval
    print(f"\nProcessing registration for {registration.user.first_name} {registration.user.last_name}")
    print(f"ID: {registration.id}")
    print(f"Email: {registration.user.email}")
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
    
    # Verify the API endpoint that would be used for this approval
    print(f"\nAPI Endpoint for this approval would be:")
    print(f"POST /api/hospitals/registrations/{registration.id}/approve/")
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
