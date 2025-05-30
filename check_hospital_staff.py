#!/usr/bin/env python
"""
Script to check the number of staff members on duty at St. Nicholas Hospital.
"""

import os
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models import Hospital, CustomUser
from api.models.medical.department import Department
from api.models.medical_staff.doctor import Doctor
from django.utils import timezone

def check_hospital_staff():
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("St. Nicholas Hospital not found!")
        return
    
    print(f"Hospital: {hospital.name}\n")
    
    # Get all departments in the hospital
    departments = Department.objects.filter(hospital=hospital)
    
    # Get current day and time
    now = timezone.now()
    current_day = now.strftime('%A').lower()
    current_time = now.strftime('%H:%M')
    
    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M')} ({current_day})\n")
    
    # Check total staff count from departments
    total_staff_count = sum(dept.current_staff_count for dept in departments)
    total_min_required = sum(dept.minimum_staff_required for dept in departments)
    
    # Try to get actual staff members
    try:
        doctors = Doctor.objects.filter(hospital=hospital)
        doctor_count = doctors.count()
    except:
        doctor_count = "Unknown (Doctor model not accessible)"
    
    # Since we don't have a staff schedule model, we'll use department counts
    on_duty_staff = "Unknown (No staff schedule system available)"
    # In a real system, this would check which staff are currently on shift
    
    # Print summary
    print(f"Total Staff Count: {total_staff_count}")
    print(f"Minimum Staff Required: {total_min_required}")
    print(f"Registered Doctors: {doctor_count}")
    print(f"Staff Currently On Duty: {on_duty_staff}")
    
    print("\nDepartment Staff Breakdown:")
    for dept in departments:
        print(f"  {dept.name}: {dept.current_staff_count} staff (min required: {dept.minimum_staff_required})")
        
        # Try to get doctors in this department
        try:
            dept_doctors = Doctor.objects.filter(hospital=hospital, department=dept).count()
            print(f"    - Doctors: {dept_doctors}")
        except:
            pass

if __name__ == "__main__":
    check_hospital_staff()
