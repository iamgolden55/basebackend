import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration, CustomUser

# Find Nkem Gladys Eruwa's registration details
user_email = "eruwagolden@gmail.com"

try:
    # Find the user
    user = CustomUser.objects.get(email=user_email)
    print(f"\nUser: {user.first_name} {user.last_name} ({user.email})")
    
    # Get all their hospital registrations
    registrations = HospitalRegistration.objects.filter(
        user=user
    ).select_related('hospital')
    
    if not registrations:
        print("No hospital registrations found for this user")
    else:
        print(f"\nHospital Registrations ({registrations.count()}):")
        
        for reg in registrations:
            print(f"\n- Hospital: {reg.hospital.name}")
            print(f"  Status: {reg.status}")
            print(f"  Registration Date: {reg.created_at}")
            print(f"  Approval Date: {reg.approved_date or 'Not yet approved'}")
            print(f"  Primary Hospital: {'Yes' if reg.is_primary else 'No'}")
    
except CustomUser.DoesNotExist:
    print(f"User with email {user_email} not found")
except Exception as e:
    print(f"Error: {str(e)}") 