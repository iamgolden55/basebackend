#!/usr/bin/env python3
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import sys

def test_doctor_interactions_endpoint():
    """Test if the doctor-interactions endpoint exists and what it returns"""
    # Get the user
    User = get_user_model()
    try:
        user = User.objects.get(email='eruwagolden@gmail.com')
        print(f"Found user: {user.get_full_name()} ({user.email})")
    except User.DoesNotExist:
        print("User not found. Please check the email.")
        return
    
    # Create API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # List of endpoints to test
    endpoints = [
        '/api/patient/medical-record/',
        '/api/patient/medical-record/summary/',
        '/api/patient/medical-record/doctor-interactions/',
    ]
    
    print("\nTesting endpoints...")
    
    for endpoint in endpoints:
        print(f"\nAttempting to access: {endpoint}")
        try:
            response = client.get(endpoint)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Response data structure:")
                print(json.dumps(response.data, indent=2)[:500] + "..." if len(json.dumps(response.data)) > 500 else json.dumps(response.data, indent=2))
            else:
                print(f"Error response: {response.data}")
        except Exception as e:
            print(f"Error accessing endpoint: {str(e)}")
    
    # Test OTP flow
    print("\nTesting OTP flow for full medical record access:")
    try:
        # Request OTP
        print("Step 1: Requesting OTP...")
        otp_response = client.post('/api/patient/medical-record/request-otp/')
        print(f"OTP request status: {otp_response.status_code}")
        
        if otp_response.status_code == 200:
            print("OTP request successful - check user's email for OTP code")
            print("Manual step required: Enter the OTP from the email")
            otp = input("Enter the OTP you received: ")
            
            # Verify OTP
            print("\nStep 2: Verifying OTP...")
            verify_response = client.post(
                '/api/patient/medical-record/verify-otp/',
                {'otp': otp}
            )
            print(f"OTP verification status: {verify_response.status_code}")
            
            if verify_response.status_code == 200:
                print("OTP verification successful")
                med_access_token = verify_response.data.get('med_access_token')
                
                if med_access_token:
                    # Access medical record with token
                    print("\nStep 3: Accessing medical record with med_access_token...")
                    
                    # Add the med_access_token to headers
                    client.credentials(
                        HTTP_AUTHORIZATION=f"Bearer {client.credentials.get('HTTP_AUTHORIZATION', '').split(' ')[1]}",
                        HTTP_X_MED_ACCESS_TOKEN=med_access_token
                    )
                    
                    med_response = client.get('/api/patient/medical-record/')
                    print(f"Medical record access status: {med_response.status_code}")
                    
                    if med_response.status_code == 200:
                        print("Successfully accessed medical record with OTP verification")
                        print("\nMedical record data structure:")
                        print(json.dumps(med_response.data, indent=2)[:500] + "..." if len(json.dumps(med_response.data)) > 500 else json.dumps(med_response.data, indent=2))
                    else:
                        print(f"Error accessing medical record: {med_response.data}")
                else:
                    print("No med_access_token received after OTP verification")
            else:
                print(f"OTP verification failed: {verify_response.data}")
        else:
            print(f"Error requesting OTP: {otp_response.data}")
            
    except Exception as e:
        print(f"Error testing OTP flow: {str(e)}")

if __name__ == "__main__":
    test_doctor_interactions_endpoint() 