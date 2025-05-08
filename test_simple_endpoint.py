#!/usr/bin/env python3
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

def test_endpoint():
    """Test if the doctor-interactions endpoint exists"""
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
    
    # Test the endpoint
    endpoint = '/api/patient/medical-record/doctor-interactions/'
    print(f"Testing endpoint: {endpoint}")
    
    try:
        response = client.get(endpoint)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Endpoint exists and returned success")
            print("Response data:")
            print(json.dumps(response.data, indent=2))
        else:
            print(f"Endpoint returned error: {response.data}")
            print("Endpoint might not exist or requires different authentication")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_endpoint() 