#!/usr/bin/env python3
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.models.medical.medical_record import MedicalRecord, DoctorInteraction
from api.serializers import AppointmentSerializer, PatientMedicalRecordSummarySerializer
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.db import connection

def test_goldin_appointment_summary():
    """Test completing an appointment with a medical summary for Goldin Eruwa"""
    # Find Goldin Eruwa by email
    User = get_user_model()
    patient = User.objects.filter(email='eruwagolden@gmail.com').first()
    
    if not patient:
        print("User Goldin Eruwa not found in database")
        return
        
    print(f"Testing for patient: {patient.get_full_name()} ({patient.email})")
    
    # Find a pending or confirmed appointment for this patient
    appointment = Appointment.objects.filter(
        patient=patient,
        status__in=['pending', 'confirmed']
    ).first()
    
    if not appointment:
        # If no appointment exists, let's create one
        print("No existing appointment found, creating a new one")
        
        # Get a doctor
        from api.models.medical_staff.doctor import Doctor
        doctor = Doctor.objects.filter(is_active=True, is_verified=True).first()
        
        if not doctor:
            print("No active doctor found in database")
            return
            
        # Get a hospital and department
        from api.models.medical.hospital import Hospital
        from api.models.medical.department import Department
        
        hospital = Hospital.objects.first()
        department = Department.objects.filter(hospital=hospital).first()
        
        if not hospital or not department:
            print("No hospital or department found")
            return
            
        # Create a new appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            department=department,
            appointment_date=timezone.now() + timezone.timedelta(days=7),
            duration=30,
            appointment_type='consultation',
            priority='normal',
            status='confirmed',
            chief_complaint='Routine checkup',
            appointment_id=Appointment.generate_appointment_id()
        )
        print(f"Created new appointment: {appointment.appointment_id}")
    else:
        print(f"Found existing appointment: {appointment.appointment_id}")
        
    print(f"Current status: {appointment.status}")
    print(f"Doctor: {appointment.doctor.user.get_full_name()}")
    
    # Temporarily update the appointment date to be in the past and status to 'confirmed'
    # This is needed to bypass the validation that appointments can't be in the past
    with connection.cursor() as cursor:
        # Update appointment date to yesterday
        yesterday = (timezone.now() - timezone.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "UPDATE api_appointment SET appointment_date = %s, status = 'confirmed' WHERE id = %s",
            [yesterday, appointment.id]
        )
    
    # Refresh the appointment from DB
    appointment = Appointment.objects.get(id=appointment.id)
    print(f"Updated appointment date to: {appointment.appointment_date}")
    
    # Get the doctor's user account
    doctor_user = appointment.doctor.user
    
    # Create an API client
    client = APIClient()
    client.force_authenticate(user=doctor_user)
    
    # Create a comprehensive medical summary with treatment recommendations
    medical_summary = """
    Patient: Goldin Eruwa
    
    Presenting Complaint:
    Patient presented with headache, fatigue, and mild fever for the past 3 days.
    
    Examination:
    - Temperature: 37.5°C
    - Blood Pressure: 130/85 mmHg
    - Heart Rate: 82 bpm
    - Respiratory Rate: 18/min
    - Throat: Slightly inflamed
    - Lungs: Clear on auscultation
    
    Diagnosis:
    - Viral upper respiratory infection
    
    Treatment:
    - Paracetamol 500mg, 1 tablet every 6 hours as needed for fever and headache
    - Increase fluid intake to at least 2-3 liters per day
    - Rest for 48 hours
    - Vitamin C 1000mg daily for 7 days
    
    Follow-up:
    - Return in 7 days if symptoms persist
    - Contact immediately if fever exceeds 38.5°C or if severe symptoms develop
    
    Additional Recommendations:
    - Avoid strenuous activity until symptoms resolve
    - Isolate from family members when possible to prevent spread
    """
    
    # Complete the appointment with medical summary
    print("\nCompleting appointment with medical summary...")
    response = client.patch(
        f'/api/doctor-appointments/{appointment.appointment_id}/status/',
        {
            'status': 'completed',
            'medical_summary': medical_summary
        },
        format='json'
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        print("Appointment completed successfully")
    else:
        print(f"Response data: {response.data}")
        print("Failed to complete appointment")
        return
    
    # Verify the appointment was updated
    updated_appointment = Appointment.objects.get(id=appointment.id)
    print(f"\nVerification:")
    print(f"Updated status: {updated_appointment.status}")
    print(f"Completed at: {updated_appointment.completed_at}")
    
    # Verify that a medical record was created or updated for the patient
    print("\nChecking patient's medical record...")
    try:
        if hasattr(patient, 'medical_record') and patient.medical_record:
            print(f"Patient has medical record with HPN: {patient.medical_record.hpn}")
            medical_record = patient.medical_record
        else:
            print("Patient has no medical record - this shouldn't happen after completing appointment")
            return
        
        # Check if a doctor interaction was created
        interactions = DoctorInteraction.objects.filter(
            medical_record=medical_record,
            doctor=appointment.doctor
        ).order_by('-interaction_date')
        
        if interactions.exists():
            latest_interaction = interactions.first()
            print(f"\nFound doctor interaction from {latest_interaction.interaction_date}")
            print(f"Interaction type: {latest_interaction.interaction_type}")
            print(f"Doctor notes summary: {latest_interaction.doctor_notes[:150]}...")
        else:
            print("No doctor interaction found - this suggests an issue with the _create_medical_record_entry method")
        
        # Test the API endpoint to retrieve medical record summary
        print("\nTesting medical record summary API endpoint...")
        patient_client = APIClient()
        patient_client.force_authenticate(user=patient)
        
        response = patient_client.get('/api/patient/medical-record/summary/')
        print(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print("Medical record summary data retrieved successfully")
            print(f"Patient name: {data['data']['patient_name']}")
            print(f"HPN: {data['data']['hpn']}")
            
            if 'interactions' in data['data'] and data['data']['interactions']:
                print(f"\nFound {len(data['data']['interactions'])} interactions")
                latest = data['data']['interactions'][0]
                print(f"Latest interaction: {latest['formatted_date']}")
                print(f"Doctor: {latest['doctor_name']}")
                print(f"Department: {latest['department_name']}")
                print(f"Hospital: {latest['hospital_name']}")
                print(f"Doctor notes: {latest['doctor_notes'][:150]}...")
                
                print("\nMEDICAL RECORD ACCESS INFORMATION:")
                print(f"To view this in your browser, login as {patient.email} and go to:")
                print(f"  Dashboard -> Medical Records")
                print(f"Or directly access the API endpoint:")
                print(f"  GET /api/patient/medical-record/summary/")
                print("\nThis appointment summary has been successfully added to Goldin's medical record.")
            else:
                print("No interactions found in API response")
        else:
            print(f"API error: {response.data}")
        
    except Exception as e:
        print(f"Error checking medical record: {str(e)}")

if __name__ == "__main__":
    test_goldin_appointment_summary() 