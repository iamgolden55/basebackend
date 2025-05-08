import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical_staff.doctor import Doctor
from django.db.models import Count

# Get all doctors
doctors = Doctor.objects.all()

# Get total count of doctors
total_doctors = doctors.count()
print(f"\nTotal doctors in the system: {total_doctors}")

# Count verified doctors
verified_doctors = doctors.filter(is_verified=True).count()
print(f"Total verified doctors: {verified_doctors}")
print(f"Verification percentage: {(verified_doctors / total_doctors * 100) if total_doctors > 0 else 0:.2f}%")

# Count by hospital
print("\nVerified doctors by hospital:")
hospital_counts = doctors.filter(is_verified=True).values('hospital__name').annotate(count=Count('id'))
for hospital in hospital_counts:
    hospital_name = hospital['hospital__name'] or 'No Hospital'
    print(f"- {hospital_name}: {hospital['count']}")

# Count by department
print("\nVerified doctors by department:")
dept_counts = doctors.filter(is_verified=True).values('department__name').annotate(count=Count('id'))
for dept in dept_counts:
    dept_name = dept['department__name'] or 'No Department'
    print(f"- {dept_name}: {dept['count']}")

# Count by status
print("\nVerified doctors by status:")
status_counts = doctors.filter(is_verified=True).values('status').annotate(count=Count('id'))
for status in status_counts:
    print(f"- {status['status']}: {status['count']}")