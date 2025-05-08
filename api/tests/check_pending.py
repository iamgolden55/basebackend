import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import HospitalRegistration
from django.db.models import Count

# Get total count
total_pending = HospitalRegistration.objects.filter(status='pending').count()
print(f"\nTotal pending registrations: {total_pending}")

# Get counts by hospital
print("\nCounts by hospital:")
counts_by_hospital = HospitalRegistration.objects.filter(
    status='pending'
).values('hospital__name').annotate(
    count=Count('id')
).order_by('-count')

for result in counts_by_hospital:
    hospital_name = result['hospital__name']
    count = result['count']
    print(f"- {hospital_name}: {count} pending")

# Get patient details
print("\nPending patients by hospital:")
hospitals = {}

for registration in HospitalRegistration.objects.filter(status='pending').select_related('hospital', 'user'):
    hospital_name = registration.hospital.name
    if hospital_name not in hospitals:
        hospitals[hospital_name] = []
    
    hospitals[hospital_name].append({
        'id': registration.id,
        'email': registration.user.email,
        'name': f"{registration.user.first_name} {registration.user.last_name}",
        'registration_date': registration.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

for hospital_name, patients in hospitals.items():
    print(f"\n{hospital_name} ({len(patients)} pending):")
    for patient in patients:
        print(f"  - {patient['name']} ({patient['email']}), registered on {patient['registration_date']}")

print("\n") 