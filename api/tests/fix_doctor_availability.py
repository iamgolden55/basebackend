#!/usr/bin/env python
import os
import django
import datetime
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.hospital import Hospital
from api.models.medical.department import Department
from api.models.medical_staff.doctor import Doctor
from api.models.medical.appointment import Appointment

def fix_doctor_availability():
    print("Fixing doctor availability...")
    
    # 1. Update all doctors in Cardiology department
    cardio_dept = Department.objects.get(name='Cardiology')
    hospital = Hospital.objects.get(name='General Hospital')
    
    # Get all cardiology doctors
    cardio_doctors = Doctor.objects.filter(
        department=cardio_dept,
        hospital=hospital
    )
    
    print(f"Found {cardio_doctors.count()} doctors in Cardiology department")
    
    # 2. Update each doctor
    for doctor in cardio_doctors:
        # Set license to be valid for next 2 years
        doctor.license_expiry_date = timezone.now().date() + datetime.timedelta(days=730)
        
        # Set consultation days to all weekdays
        doctor.consultation_days = 'Mon,Tue,Wed,Thu,Fri'
        
        # Set consultation hours (9 AM to 5 PM)
        doctor.consultation_hours_start = datetime.time(9, 0)
        doctor.consultation_hours_end = datetime.time(17, 0)
        
        # Set other required fields
        doctor.is_active = True
        doctor.is_verified = True
        doctor.status = 'active'
        doctor.available_for_appointments = True
        doctor.max_daily_appointments = 20
        doctor.appointment_duration = 30
        
        doctor.save()
        print(f"Updated doctor: {doctor.user.get_full_name()}")
        print(f"- License valid until: {doctor.license_expiry_date}")
        print(f"- Consultation days: {doctor.consultation_days}")
        print(f"- Hours: {doctor.consultation_hours_start} - {doctor.consultation_hours_end}")
        print(f"- Can practice: {doctor.can_practice}")
        print("---")

    # 3. Clear any existing appointments to avoid conflicts
    Appointment.objects.filter(
        doctor__in=cardio_doctors,
        appointment_date__gte=timezone.now()
    ).delete()
    
    print("\nAll doctors updated successfully!")
    print("\nNext steps:")
    print("1. Run 'python manage.py create_appointment_availability' to create new appointment slots")
    print("2. Clear your browser cache")
    print("3. Restart your frontend application")
    print("4. Try booking an appointment again")

if __name__ == '__main__':
    fix_doctor_availability() 