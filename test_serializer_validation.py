#!/usr/bin/env python
"""
Test script to debug serializer validation
"""
import os
import django
import sys
from datetime import datetime, date

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Appointment, Department
from api.serializers import AppointmentSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.request import Request
from django.test import RequestFactory

User = get_user_model()

def test_serializer_validation():
    """Test the serializer validation logic directly"""
    print("=== TESTING SERIALIZER VALIDATION ===")
    
    # Get a user with existing appointments
    user = User.objects.filter(appointments__isnull=False).first()
    if not user:
        print("No user with appointments found")
        return
    
    print(f"Testing with user: {user.username} (ID: {user.id})")
    
    # Get an existing appointment to replicate
    existing_appointment = Appointment.objects.filter(patient=user).first()
    if not existing_appointment:
        print("No existing appointments found")
        return
    
    print(f"Existing appointment: {existing_appointment.id} on {existing_appointment.appointment_date.date()} in {existing_appointment.department.name}")
    
    # Create request context
    factory = RequestFactory()
    request = factory.post('/api/appointments/')
    request.user = user
    
    # Test data that should trigger duplicate validation
    test_data = {
        'hospital': existing_appointment.hospital.id,
        'department': existing_appointment.department.id,
        'appointment_date': existing_appointment.appointment_date,
        'appointment_type': 'consultation',
        'priority': 'normal',
        'chief_complaint': 'Test complaint'
    }
    
    print(f"Test data: {test_data}")
    
    # Create serializer with context
    serializer = AppointmentSerializer(data=test_data, context={'request': request})
    
    print("Checking serializer validation...")
    try:
        if serializer.is_valid():
            print("❌ VALIDATION PASSED - This should have failed!")
            print(f"Validated data: {serializer.validated_data}")
        else:
            print("✅ VALIDATION FAILED - As expected")
            print(f"Errors: {serializer.errors}")
    except Exception as e:
        print(f"❌ VALIDATION EXCEPTION: {e}")

if __name__ == "__main__":
    test_serializer_validation()