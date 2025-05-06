#!/usr/bin/env python
import os
import django
import sys
import json
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Appointment, CustomUser
from rest_framework.test import APIClient
from django.urls import reverse

def test_update_status():
    """Test various ways to update an appointment status"""
    
    # Get the appointment
    appointment_id = 'APT-GOLDEN02'
    try:
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        print(f"Found appointment: {appointment_id}")
        print(f"Current status: {appointment.status}")
    except Appointment.DoesNotExist:
        print(f"Appointment {appointment_id} not found")
        return
    
    # Get the doctor
    try:
        doctor = CustomUser.objects.get(email='eruwagolden@gmail.com')
        print(f"Doctor: {doctor.first_name} {doctor.last_name}")
    except CustomUser.DoesNotExist:
        print("Doctor not found")
        return
    
    print("\n--- Testing different update methods ---")
    
    # Method 1: Using the REST API
    client = APIClient()
    client.force_authenticate(user=doctor)
    
    # First reset the status to pending (using direct SQL to bypass validation)
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    print(f"\nReset appointment status to 'pending' (rows updated: {cursor.rowcount})")
    
    # Test method 1: Regular PATCH update
    print("\n1. Using PATCH with /api/appointments/{id}/")
    response = client.patch(
        f'/api/appointments/{appointment.id}/',
        {'status': 'confirmed'},
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 2: Using the appointment_id instead of numeric ID
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    
    print("\n2. Using PATCH with /api/appointments/APT-GOLDEN02/")
    response = client.patch(
        f'/api/appointments/{appointment_id}/',
        {'status': 'confirmed'},
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 3: Try using doctor-appointments endpoint 
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    
    print("\n3. Using PATCH with /api/doctor-appointments/APT-GOLDEN02/")
    response = client.patch(
        f'/api/doctor-appointments/{appointment_id}/',
        {'status': 'confirmed'},
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 4: Check if there's a .../status/ endpoint
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    
    print("\n4. Using PATCH with /api/appointments/APT-GOLDEN02/status/")
    response = client.patch(
        f'/api/appointments/{appointment_id}/status/',
        {'status': 'confirmed'},
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 5: Look for an 'approve' action endpoint
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    
    print("\n5. Using POST with /api/appointments/APT-GOLDEN02/approve/")
    response = client.post(
        f'/api/appointments/{appointment_id}/approve/',
        {'approval_notes': 'Approved by test script'},
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 6: Try using doctor-appointments status endpoint with redirect following
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['pending', appointment_id])
    
    print("\n6. Using PATCH with /api/doctor-appointments/APT-GOLDEN02/status/ (follow_redirects=True)")
    
    # Get the redirect URL first
    redirect_response = client.patch(
        f'/api/doctor-appointments/{appointment_id}/status/',
        {'status': 'confirmed'},
        format='json',
        follow=False
    )
    print(f"Redirect status code: {redirect_response.status_code}")
    if redirect_response.status_code == 301:
        redirect_url = redirect_response.url
        print(f"Following redirect to: {redirect_url}")
        response = client.patch(
            redirect_url,
            {'status': 'confirmed'},
            format='json'
        )
        print(f"Status code after redirect: {response.status_code}")
        print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    
    # Method 7: Test cancellation
    # Reset first
    cursor.execute('UPDATE api_appointment SET status = %s WHERE appointment_id = %s', 
                   ['confirmed', appointment_id])
    
    print("\n7. Testing cancellation with /api/appointments/APT-GOLDEN02/status/")
    response = client.patch(
        f'/api/appointments/{appointment_id}/status/',
        {
            'status': 'cancelled',
            'cancellation_reason': 'Patient requested cancellation'
        },
        format='json'
    )
    print(f"Status code: {response.status_code}")
    print(f"Response data: {json.dumps(response.data, indent=2) if hasattr(response, 'data') else 'No data'}")
    
    # Check if update worked
    appointment.refresh_from_db()
    print(f"New status: {appointment.status}")
    print(f"Cancellation reason: {appointment.cancellation_reason}")
    
    print("\n--- Test completed ---")

if __name__ == "__main__":
    test_update_status() 