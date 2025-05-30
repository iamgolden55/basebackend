#!/usr/bin/env python
"""
Script to check the total number of beds in St. Nicholas Hospital.
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models import Hospital
from api.models.medical.department import Department

def check_hospital_beds():
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("St. Nicholas Hospital not found!")
        return
    
    print(f"Hospital: {hospital.name}\n")
    
    # Get all departments in the hospital
    departments = Department.objects.filter(hospital=hospital)
    
    # Calculate bed totals
    total_regular_beds = sum(dept.total_beds for dept in departments)
    total_icu_beds = sum(dept.icu_beds for dept in departments)
    occupied_regular_beds = sum(dept.occupied_beds for dept in departments)
    occupied_icu_beds = sum(dept.occupied_icu_beds for dept in departments)
    
    # Calculate available beds
    available_regular_beds = total_regular_beds - occupied_regular_beds
    available_icu_beds = total_icu_beds - occupied_icu_beds
    
    # Print summary
    print(f"Total Bed Capacity: {total_regular_beds + total_icu_beds}")
    print(f"  - Regular Beds: {total_regular_beds} (Available: {available_regular_beds})")
    print(f"  - ICU Beds: {total_icu_beds} (Available: {available_icu_beds})")
    
    print("\nDepartment Breakdown:")
    for dept in departments:
        print(f"  {dept.name}: {dept.total_beds} regular beds, {dept.icu_beds} ICU beds")
        print(f"    - Occupied: {dept.occupied_beds} regular, {dept.occupied_icu_beds} ICU")

if __name__ == "__main__":
    check_hospital_beds()
