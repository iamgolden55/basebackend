import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, Doctor
from django.db.models import Count, Q

# Set the hospital name
hospital_name = "General Hospital"

try:
    # Find the hospital
    hospital = Hospital.objects.get(name=hospital_name)
    print(f"\nHospital: {hospital.name}")
    print(f"ID: {hospital.id}")
    print(f"Address: {hospital.address}, {hospital.city}, {hospital.country}")
    
    # Get all doctors assigned to this hospital
    doctors = Doctor.objects.filter(hospital=hospital).select_related('user', 'department')
    
    # Get total count
    total_doctors = doctors.count()
    print(f"\nTotal doctors: {total_doctors}")
    
    # Count by status
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
    
    # Get model fields dynamically
    doctor_fields = [field.name for field in Doctor._meta.fields]
    
    # List all doctors
    print("\nDoctor Details:")
    for doctor in doctors:
        print(f"\n- Name: Dr. {doctor.user.first_name} {doctor.user.last_name}")
        
        # Check if specialty exists before accessing it
        if 'specialty' in doctor_fields:
            print(f"  Specialty: {doctor.specialty or 'Not specified'}")
        
        print(f"  Department: {doctor.department.name if doctor.department else 'Not assigned'}")
        print(f"  Status: {doctor.status}")
        
        # Check if available_for_appointments exists before accessing it
        if 'available_for_appointments' in doctor_fields:
            print(f"  Available for appointments: {'Yes' if doctor.available_for_appointments else 'No'}")
    
except Hospital.DoesNotExist:
    print(f"Hospital '{hospital_name}' not found")
except Exception as e:
    print(f"Error: {str(e)}") 