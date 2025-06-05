#!/usr/bin/env python
"""
Test script for the patient admission system.
This script demonstrates how to create, admit, transfer, and discharge patients.
"""

import os
import django
import sys
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from django.utils import timezone
from api.models import Hospital, CustomUser
from api.models.medical.department import Department
from api.models.medical_staff.doctor import Doctor
from api.models.medical.patient_admission import PatientAdmission
from api.models.medical.patient_transfer import PatientTransfer
from api.utils.id_generators import generate_admission_id

def create_test_admission():
    """
    Create a test patient admission in the system
    """
    print("\n===== PATIENT ADMISSION SYSTEM TEST =====\n")
    
    # Step 1: Find hospital, department, doctor and patient
    print("Step 1: Finding hospital, department, doctor and patient...")
    
    # Find St. Nicholas Hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("Error: St. Nicholas Hospital not found!")
        return
        
    print(f"Hospital: {hospital.name}")
    
    # Find a department with beds
    departments = Department.objects.filter(hospital=hospital, total_beds__gt=0)
    if not departments.exists():
        print("Error: No departments with beds found!")
        return
        
    department = departments.first()
    print(f"Department: {department.name} (Available beds: {department.total_beds - department.occupied_beds})")
    
    # Find a doctor
    doctors = Doctor.objects.filter(hospital=hospital)
    if not doctors.exists():
        print("Error: No doctors found!")
        return
        
    doctor = doctors.first()
    print(f"Doctor: {doctor.user.get_full_name()} (Specialization: {doctor.specialization})")
    
    # Find a patient (any user who isn't a doctor or admin)
    patients = CustomUser.objects.exclude(id__in=Doctor.objects.values_list('user_id', flat=True))
    if not patients.exists():
        print("Error: No patients found!")
        return
        
    patient = patients.first()
    print(f"Patient: {patient.get_full_name()} (ID: {patient.id})")
    
    # Step 2: Create a new admission
    print("\nStep 2: Creating new patient admission...")
    
    # Check if patient already has an active admission
    existing_admission = PatientAdmission.objects.filter(
        patient=patient, 
        status__in=['pending', 'admitted']
    ).first()
    
    if existing_admission:
        print(f"Patient already has an active admission: {existing_admission.admission_id} ({existing_admission.status})")
        admission = existing_admission
    else:
        # Create a new admission
        # Create admission using the model fields as expected by serializer
        admission = PatientAdmission.objects.create(
            admission_id=generate_admission_id(),
            patient=patient,
            hospital=hospital,  # serializer maps hospital_id to this
            department=department,  # serializer maps department_id to this
            status='pending',
            admission_type='inpatient',
            priority='elective',  # must be one of: emergency, urgent, elective
            reason_for_admission="Abdominal pain and fever",
            is_icu_bed=False,
            bed_identifier=f"Room {department.floor_number}01-A",
            attending_doctor=doctor,
            expected_discharge_date=timezone.now() + timedelta(days=3),
            diagnosis="Suspected appendicitis",
            acuity_level=3,
            is_registered_patient=True,
            registration_status='complete'
        )
        print(f"Created new admission: {admission.admission_id} (Status: {admission.status})")
    
    # Step 3: Admit the patient
    if admission.status == 'pending':
        print("\nStep 3: Admitting patient...")
        try:
            admission.admit_patient()
            print(f"Patient admitted successfully. Bed assigned in {department.name}.")
            print(f"Current department bed status: {department.occupied_beds}/{department.total_beds} beds occupied")
        except Exception as e:
            print(f"Error admitting patient: {str(e)}")
    elif admission.status == 'admitted':
        print("\nStep 3: Patient is already admitted")
    else:
        print(f"\nStep 3: Cannot admit patient with status '{admission.status}'")
        return
    
    # Step 4: Transfer patient to another department (if possible)
    print("\nStep 4: Transferring patient to another department...")
    
    # Find another department with beds
    other_department = Department.objects.filter(
        hospital=hospital, 
        total_beds__gt=0
    ).exclude(id=department.id).first()
    
    if other_department:
        print(f"Found transfer department: {other_department.name}")
        try:
            admission.transfer_patient(
                new_department=other_department,
                reason="Patient requires specialized care"
            )
            print(f"Patient transferred successfully to {other_department.name}")
            print(f"Source department: {department.occupied_beds}/{department.total_beds} beds occupied")
            print(f"Target department: {other_department.occupied_beds}/{other_department.total_beds} beds occupied")
            
            # Show transfer record
            transfer = PatientTransfer.objects.filter(admission=admission).latest('transfer_date')
            print(f"Transfer record: {transfer} (Reason: {transfer.reason})")
        except Exception as e:
            print(f"Error transferring patient: {str(e)}")
    else:
        print("No other departments with beds available for transfer")
    
    # Step 5: Discharge patient
    print("\nStep 5: Discharging patient...")
    try:
        admission.discharge_patient(
            destination="Home",
            summary="Patient's condition improved. No complications during stay.",
            followup="Follow up with primary care physician in 7 days."
        )
        print(f"Patient discharged successfully. Status: {admission.status}")
        print(f"Length of stay: {admission.length_of_stay_days} days")
        print(f"Discharge summary: {admission.discharge_summary}")
        
        # Check department bed status after discharge
        department = admission.department
        print(f"Current department bed status: {department.occupied_beds}/{department.total_beds} beds occupied")
    except Exception as e:
        print(f"Error discharging patient: {str(e)}")
    
    print("\n===== PATIENT ADMISSION SYSTEM TEST COMPLETED =====\n")
    return admission

if __name__ == "__main__":
    create_test_admission()
