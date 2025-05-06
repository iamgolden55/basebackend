import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.hospital import Hospital
from api.models.medical_staff.doctor import Doctor
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

User = get_user_model()

# Set the hospital name
hospital_name = "General Hospital"

try:
    # Find the hospital
    hospital = Hospital.objects.get(name=hospital_name)
    print(f"\nHospital: {hospital.name}")
    
    # Get all doctors assigned to this hospital
    doctors = Doctor.objects.filter(hospital=hospital).select_related('user', 'department')
    
    # Get total count of doctors
    total_doctors = doctors.count()
    print(f"\nTotal doctors at {hospital.name}: {total_doctors}")
    
    # Count active doctors (staff members)
    active_doctors = doctors.filter(user__is_staff=True).count()
    print(f"Total doctors who are staff members: {active_doctors}")
    
    # Count by status if status field exists
    if hasattr(Doctor, 'status'):
        status_counts = doctors.values('status').annotate(count=Count('id'))
        print("\nDoctors by status:")
        for status in status_counts:
            print(f"- {status['status']}: {status['count']}")
    
    # Count by department
    dept_counts = doctors.values('department__name').annotate(count=Count('id'))
    print("\nDoctors by department:")
    for dept in dept_counts:
        dept_name = dept['department__name'] or 'No Department'
        print(f"- {dept_name}: {dept['count']}")
    
    # Count staff doctors by department
    staff_dept_counts = doctors.filter(user__is_staff=True).values('department__name').annotate(count=Count('id'))
    print("\nStaff doctors by department:")
    for dept in staff_dept_counts:
        dept_name = dept['department__name'] or 'No Department'
        print(f"- {dept_name}: {dept['count']}")
    
except Hospital.DoesNotExist:
    print(f"Hospital '{hospital_name}' not found")
except Exception as e:
    print(f"Error: {str(e)}")