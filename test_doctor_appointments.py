#!/usr/bin/env python3
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

def test_doctor_appointments_endpoint():
    """Test if the doctor-appointments endpoint exists and returns data in expected format"""
    # Get the user (assuming a doctor account)
    User = get_user_model()
    try:
        # Replace this with a known doctor account email
        user = User.objects.get(email='eruwagolden@gmail.com')
        print(f"Found user: {user.get_full_name()} ({user.email})")
    except User.DoesNotExist:
        print("User not found. Please check the email.")
        return
    
    # Create API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test the doctor-appointments endpoint
    endpoint = '/api/doctor-appointments/'
    print(f"Testing endpoint: {endpoint}")
    
    try:
        response = client.get(endpoint)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Endpoint exists and returned success")
            if response.data:
                # Check if the response has the expected format for the frontend
                sample_appointment = response.data[0] if response.data else None
                if sample_appointment:
                    print("\nSample appointment fields:")
                    for key, value in sample_appointment.items():
                        print(f"  - {key}")
                    
                    # Check if all required fields for the frontend are present
                    required_fields = [
                        'appointment_id',
                        'patient_name',
                        'appointment_date',
                        'formatted_date',
                        'status',
                        'priority'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in sample_appointment]
                    if missing_fields:
                        print(f"\nMissing required fields: {missing_fields}")
                    else:
                        print("\nAll required fields are present!")
                    
                    # Print a sample of the data
                    print("\nSample appointment data:")
                    print(json.dumps(sample_appointment, indent=2))
                else:
                    print("No appointments found for this doctor")
            else:
                print("No appointments data returned")
        else:
            print(f"Endpoint returned error: {response.data}")
            print("Endpoint might not exist or requires different authentication")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_doctor_appointments_endpoint() 