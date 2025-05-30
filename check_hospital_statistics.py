#!/usr/bin/env python
"""
Check statistics for St. Nicholas Hospital including discharged patients and emergency cases
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models.medical.patient_admission import PatientAdmission
from api.models import Hospital

def check_hospital_statistics():
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("Error: St. Nicholas Hospital not found!")
        return
    
    print(f"\n=== STATISTICS FOR {hospital.name} ===")
    
    # Count total admissions
    total_admissions = PatientAdmission.objects.filter(hospital=hospital).count()
    print(f"\nTotal admissions (all time): {total_admissions}")
    
    # Count by status
    statuses = ['pending', 'admitted', 'discharged', 'transferred', 'deceased', 'left_ama']
    print("\nAdmissions by status:")
    for status in statuses:
        count = PatientAdmission.objects.filter(hospital=hospital, status=status).count()
        print(f"- {status.title()}: {count}")
    
    # Count emergency admissions
    emergency_count = PatientAdmission.objects.filter(
        hospital=hospital, 
        admission_type='emergency'
    ).count()
    print(f"\nEmergency admissions: {emergency_count}")
    
    # Count unregistered patients (emergency admissions without accounts)
    unregistered_count = PatientAdmission.objects.filter(
        hospital=hospital, 
        is_registered_patient=False
    ).count()
    print(f"Unregistered patient admissions: {unregistered_count}")
    
    # Count converted patients (formerly unregistered)
    converted_count = PatientAdmission.objects.filter(
        hospital=hospital, 
        temp_patient_details__isnull=False, 
        patient__isnull=False
    ).count()
    print(f"Converted patients (unregistered → registered): {converted_count}")
    
    # List recent discharges
    recent_discharges = PatientAdmission.objects.filter(hospital=hospital, status='discharged').order_by('-actual_discharge_date')[:5]
    if recent_discharges.exists():
        print("\nRecent discharges:")
        for discharge in recent_discharges:
            patient_name = "Unknown"
            if discharge.patient:
                patient_name = discharge.patient.get_full_name()
            elif discharge.temp_patient_details:
                first_name = discharge.temp_patient_details.get('first_name', 'Unknown')
                last_name = discharge.temp_patient_details.get('last_name', '')
                patient_name = f"{first_name} {last_name}"
                
            discharge_date = discharge.actual_discharge_date.strftime('%Y-%m-%d') if discharge.actual_discharge_date else 'Unknown'
            print(f"- {patient_name} (ID: {discharge.admission_id}), discharged on {discharge_date}")
    
    # Show admission types breakdown
    print("\nAdmissions by type:")
    admission_types = PatientAdmission.objects.filter(hospital=hospital).values('admission_type').distinct()
    for admission_type in admission_types:
        type_name = admission_type['admission_type']
        type_count = PatientAdmission.objects.filter(hospital=hospital, admission_type=type_name).count()
        print(f"- {type_name.title()}: {type_count}")

if __name__ == "__main__":
    check_hospital_statistics()
