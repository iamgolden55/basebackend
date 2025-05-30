#!/usr/bin/env python
"""
Check the number of patients currently admitted at St. Nicholas Hospital
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models.medical.patient_admission import PatientAdmission
from api.models import Hospital

def check_admitted_patients():
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("Error: St. Nicholas Hospital not found!")
        return
    
    # Count admitted patients
    admitted_count = PatientAdmission.objects.filter(hospital=hospital, status='admitted').count()
    print(f'\nSt. Nicholas Hospital currently has {admitted_count} admitted patients.')
    
    # Show details of admitted patients
    print('\nDetails of admitted patients:')
    admitted_patients = PatientAdmission.objects.filter(hospital=hospital, status='admitted')
    
    if admitted_patients.exists():
        for admission in admitted_patients:
            # Get patient name (either from user account or temp details)
            if admission.patient:
                patient_name = admission.patient.get_full_name()
            else:
                first_name = admission.temp_patient_details.get('first_name', 'Unknown')
                last_name = admission.temp_patient_details.get('last_name', '')
                patient_name = f"{first_name} {last_name}"
            
            # Get department name
            department = admission.department.name if admission.department else 'Unknown'
            
            # Print details
            print(f'- {patient_name} in {department}, Admission ID: {admission.admission_id}')
    else:
        print("No patients are currently admitted.")
    
    # Show total beds in hospital
    total_beds = sum(dept.total_beds for dept in hospital.departments.all())
    occupied_beds = sum(dept.occupied_beds for dept in hospital.departments.all())
    available_beds = total_beds - occupied_beds
    
    print(f"\nHospital Capacity: {occupied_beds}/{total_beds} beds occupied ({available_beds} available)")
    
    # Show beds by department
    print("\nBeds by Department:")
    for dept in hospital.departments.all():
        if dept.total_beds > 0:  # Only show departments with beds
            print(f"- {dept.name}: {dept.occupied_beds}/{dept.total_beds} beds occupied")

if __name__ == "__main__":
    check_admitted_patients()
