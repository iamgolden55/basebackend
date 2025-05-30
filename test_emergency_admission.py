#!/usr/bin/env python
"""
Test script for emergency patient admission and registration flow.
This script demonstrates how to create an emergency admission for an unregistered patient
and then convert them to a registered user with an HPN number.
"""

import os
import django
import sys
import json
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from django.utils import timezone
from api.models import Hospital, CustomUser, HospitalRegistration
from api.models.medical.department import Department
from api.models.medical_staff.doctor import Doctor
from api.models.medical.patient_admission import PatientAdmission
from api.utils.id_generators import generate_admission_id, generate_temp_patient_id, generate_hpn_number

def test_emergency_admission():
    """
    Test the emergency admission flow for an unregistered patient,
    followed by registration to create a full patient account
    """
    print("\n===== EMERGENCY ADMISSION AND REGISTRATION TEST =====\n")
    
    # Step 1: Find hospital, department, and doctor
    print("Step 1: Finding hospital, department, and doctor...")
    
    # Find a hospital
    hospital = Hospital.objects.filter(name__icontains='St. Nicholas').first()
    if not hospital:
        print("Error: Hospital not found!")
        return
        
    print(f"Hospital: {hospital.name}")
    
    # Find an emergency department
    departments = Department.objects.filter(hospital=hospital, name__icontains='Emergency')
    if not departments.exists():
        # If no emergency department, get any department with beds
        departments = Department.objects.filter(hospital=hospital, total_beds__gt=0)
    
    if not departments.exists():
        print("Error: No suitable department found!")
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
    
    # Step 2: Create an emergency admission for an unregistered patient
    print("\nStep 2: Creating emergency admission for unregistered patient...")
    
    # Generate temporary patient ID
    temp_patient_id = generate_temp_patient_id()
    
    # Create comprehensive temporary patient details with all required fields
    temp_patient_details = {
        # Required personal information
        "first_name": "John",
        "last_name": "Doe",
        "gender": "male",
        "age": 35,  # Either age or date_of_birth is required
        "date_of_birth": "1990-05-15",  # Including both for completeness
        "phone_number": "+1234567890",
        "city": "Lagos",  # Important for HPN generation
        "address": "123 Main St, Lagos, Nigeria",
        "emergency_contact": "+1987654321",
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_relationship": "Spouse",
        
        # Required medical information
        "chief_complaint": "Chest pain and shortness of breath",
        "allergies": ["Penicillin"],
        
        # Additional helpful information
        "current_medications": ["None"],
        "brief_history": "No known cardiac history. Started experiencing pain 2 hours ago.",
        "vitals": {
            "blood_pressure": "140/90",
            "heart_rate": 92,
            "temperature": 37.8,
            "respiratory_rate": 20,
            "oxygen_saturation": 95
        },
        "insurance_provider": "National Health Insurance",
        "insurance_id": "NHI1234567890",
        "occupation": "Software Engineer",
        "preferred_language": "English"
    }
    
    # Create admission
    admission = PatientAdmission.objects.create(
        admission_id=generate_admission_id(),
        hospital=hospital,
        department=department,
        status='pending',
        admission_type='emergency',
        priority='urgent',
        reason_for_admission="Chest pain and shortness of breath",
        is_icu_bed=False,
        attending_doctor=doctor,
        expected_discharge_date=timezone.now() + timedelta(days=2),
        diagnosis="Suspected acute coronary syndrome",
        acuity_level=2,
        is_registered_patient=False,
        temp_patient_id=temp_patient_id,
        temp_patient_details=temp_patient_details,
        registration_status='pending'
    )
    
    print(f"Created emergency admission: {admission.admission_id}")
    print(f"Temporary Patient ID: {admission.temp_patient_id}")
    print(f"Patient: {admission.patient_name}")
    print(f"Registration Status: {admission.registration_status}")
    
    # Step 3: Admit the patient
    print("\nStep 3: Admitting emergency patient...")
    try:
        admission.admit_patient()
        print(f"Patient admitted successfully. Status: {admission.status}")
        print(f"Current department bed status: {department.occupied_beds}/{department.total_beds} beds occupied")
    except Exception as e:
        print(f"Error admitting patient: {str(e)}")
    
    # Step 4: Convert temporary patient to registered user
    print("\nStep 4: Converting temporary patient to registered user...")
    
    # Generate a unique email address for each run
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    unique_email = f"john.doe.{unique_id}@example.com"
    
    # Registration data that would come from a form
    registration_data = {
        "email": unique_email,
        "password": "SecurePassword123",
        "date_of_birth": "1990-05-15"
    }
    print(f"Using unique email for registration: {unique_email}")
    
    try:
        # Convert to registered patient
        user = admission.convert_to_registered_patient(registration_data)
        
        print(f"Patient converted to registered user successfully")
        print(f"User: {user.get_full_name()} (ID: {user.id})")
        
        # Get the hospital registration
        registration = HospitalRegistration.objects.filter(user=user, hospital=hospital).first()
        if registration:
            print(f"Hospital Registration created: {registration}")
            print(f"Is Primary Hospital: {registration.is_primary}")
            
        # Check for HPN number from the user object (primary source)
        print(f"HPN Number: {user.hpn}")
        
        # Also check if it was stored in temp_patient_details (backup)
        if admission.temp_patient_details and 'hpn_number' in admission.temp_patient_details:
            print(f"HPN Number in temp details: {admission.temp_patient_details['hpn_number']}")
        else:
            print("HPN Number in temp details: Not found")
        
        # Verify admission status
        print(f"\nUpdated Admission:\nStatus: {admission.status}")
        print(f"Registration Status: {admission.registration_status}")
        print(f"Is Registered Patient: {admission.is_registered_patient}")
        print(f"Patient: {admission.patient.get_full_name() if admission.patient else 'None'}")
        
    except Exception as e:
        print(f"Error converting patient: {str(e)}")
    
    # Step 5: Discharge patient
    print("\nStep 5: Discharging patient...")
    try:
        admission.discharge_patient(
            destination="Home",
            summary="Patient stabilized. Symptoms resolved with treatment.",
            followup="Schedule follow-up with cardiologist within 7 days."
        )
        print(f"Patient discharged successfully. Status: {admission.status}")
        print(f"Discharge summary: {admission.discharge_summary}")
        
        # Check department bed status after discharge
        department = admission.department
        print(f"Current department bed status: {department.occupied_beds}/{department.total_beds} beds occupied")
    except Exception as e:
        print(f"Error discharging patient: {str(e)}")
    
    print("\n===== EMERGENCY ADMISSION AND REGISTRATION TEST COMPLETED =====\n")
    return admission

if __name__ == "__main__":
    test_emergency_admission()
