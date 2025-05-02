import os
import django
import sys
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration, CustomUser

hospital_name = "Abuja Central Hospital"

try:
    # Get all doctor registrations for the hospital (both pending and approved)
    doctor_registrations = HospitalRegistration.objects.filter(
        hospital__name=hospital_name,
        user__role='doctor'
    ).select_related('user', 'hospital')
    
    # Count total doctors by status
    total_doctors = doctor_registrations.count()
    status_counts = doctor_registrations.values('status').annotate(count=Count('id'))
    
    print(f"\nDoctor Registrations at {hospital_name}:")
    print(f"Total registrations: {total_doctors}")
    print("\nBreakdown by status:")
    for status in status_counts:
        print(f"- {status['status'].title()}: {status['count']}")
    
    print("\nDoctor Details:")
    print("-" * 50)
    
    for reg in doctor_registrations:
        doctor = reg.user
        print(f"Name: Dr. {doctor.first_name} {doctor.last_name}")
        print(f"Email: {doctor.email}")
        print(f"Status: {reg.status.title()}")
        print(f"Registration Date: {reg.created_at}")
        if reg.status == 'approved':
            print(f"Approval Date: {reg.approved_date}")
        print("-" * 50)

except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1) 