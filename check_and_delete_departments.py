#!/usr/bin/env python
"""
Script to check for doctors in St. Nicholas Hospital departments and delete the departments if needed.
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models import Hospital, Department
from api.models.medical_staff.doctor import Doctor

def main():
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("St. Nicholas Hospital not found!")
        return
    
    print(f"Hospital: {hospital.name} ({hospital.hospital_type})")
    print(f"Total departments: {hospital.departments.count()}")
    
    # Check each department for doctors
    for dept in hospital.departments.all():
        print(f"\nDepartment: {dept.name} (ID: {dept.id})")
        print(f"Department Type: {dept.get_department_type_display()}")
        
        # Check for doctors in this department
        doctors = Doctor.objects.filter(department=dept)
        print(f"Doctors count: {doctors.count()}")
        
        if doctors.count() > 0:
            print("Doctors in this department:")
            for doc in doctors:
                user_email = doc.user.email if doc.user else "No user"
                print(f"- {user_email} ({doc.specialization})")
            print("WARNING: Cannot delete department with associated doctors!")
        else:
            print("No doctors found in this department.")
            print("Department can be safely deleted.")
    
    print("\n=== Summary ===")
    print("To delete departments without doctors, run this script with --delete flag")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        # Find St. Nicholas Hospital
        hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
        if not hospital:
            print("St. Nicholas Hospital not found!")
            exit(1)
        
        # Check each department and delete if no doctors
        for dept in list(hospital.departments.all()):
            doctors = Doctor.objects.filter(department=dept)
            if doctors.count() == 0:
                dept_name = dept.name
                dept_id = dept.id
                dept.delete()
                print(f"Deleted department: {dept_name} (ID: {dept_id})")
            else:
                print(f"Department {dept.name} (ID: {dept.id}) has {doctors.count()} doctors - NOT deleted")
    else:
        main()
