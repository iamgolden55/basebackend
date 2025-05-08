#!/usr/bin/env python3
import os
import django
import json
import requests

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

def test_complete_appointment_with_summary():
    """Test completing an appointment with a medical summary"""
    # Find a pending or confirmed appointment
    appointment = Appointment.objects.filter(
        status__in=['pending', 'confirmed']
    ).first()
    
    if not appointment:
        print("No suitable appointment found for testing")
        return
    
    print(f"Testing appointment: {appointment.appointment_id}")
    print(f"Current status: {appointment.status}")
    print(f"Patient: {appointment.patient.get_full_name()}")
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
    print(f"Updated status to: {appointment.status}")
    
    # Get the doctor's user account
    doctor_user = appointment.doctor.user
    
    # Create an API client
    client = APIClient()
    client.force_authenticate(user=doctor_user)
    
    # First try updating without medical summary (should fail)
    print("\nTesting without medical summary...")
    response = client.patch(
        f'/api/doctor-appointments/{appointment.appointment_id}/status/',
        {'status': 'completed'},
        format='json'
    )
    
    print(f"Response status code: {response.status_code}")
    print(f"Response data: {response.data}")
    
    # Now try with medical summary (should succeed)
    print("\nTesting with medical summary...")
    
    # Create a comprehensive medical summary with treatment recommendations
    medical_summary = """
    Patient presented with symptoms of seasonal allergies including nasal congestion and itchy eyes.
    
    Examination:
    - Clear lungs on auscultation
    - No signs of infection
    - Mild nasal inflammation
    
    Diagnosis:
    - Seasonal allergic rhinitis
    
    Treatment:
    - Prescribed Loratadine 10mg once daily for 30 days
    - Saline nasal spray as needed
    - Recommended to avoid known allergens and keep windows closed during high pollen count days
    
    Follow-up:
    - Return in 4 weeks if symptoms persist
    - Contact office if symptoms worsen
    """
    
    response = client.patch(
        f'/api/doctor-appointments/{appointment.appointment_id}/status/',
        {
            'status': 'completed',
            'medical_summary': medical_summary
        },
        format='json'
    )
    
    print(f"Response status code: {response.status_code}")
    print(f"Response data: {response.data}")
    
    # Verify the appointment was updated
    updated_appointment = Appointment.objects.get(id=appointment.id)
    print(f"\nVerification:")
    print(f"Updated status: {updated_appointment.status}")
    print(f"Medical summary: {updated_appointment.medical_summary}")
    print(f"Completed at: {updated_appointment.completed_at}")
    
    # Verify that a medical record was created or updated for the patient
    print("\nChecking patient's medical record...")
    patient = appointment.patient
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
            print(f"Doctor notes: {latest_interaction.doctor_notes[:100]}...")
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
            print("Medical record summary data:")
            print(f"Patient name: {data['data']['patient_name']}")
            print(f"HPN: {data['data']['hpn']}")
            
            if 'interactions' in data['data'] and data['data']['interactions']:
                print(f"\nFound {len(data['data']['interactions'])} interactions")
                latest = data['data']['interactions'][0]
                print(f"Latest interaction: {latest['formatted_date']}")
                print(f"Doctor: {latest['doctor_name']}")
                print(f"Summary: {latest['doctor_notes'][:100]}...")
            else:
                print("No interactions found in API response")
        else:
            print(f"API error: {response.data}")
        
    except Exception as e:
        print(f"Error checking medical record: {str(e)}")
    
    # Serialize the appointment to check all fields
    serializer = AppointmentSerializer(updated_appointment)
    print("\nSerialized appointment data:")
    print(json.dumps(serializer.data, indent=2, default=str))

if __name__ == "__main__":
    test_complete_appointment_with_summary() 