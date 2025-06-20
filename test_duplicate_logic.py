#!/usr/bin/env python
"""
Test script to debug duplicate appointment validation logic
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
from django.contrib.auth import get_user_model

User = get_user_model()
from django.utils import timezone

def test_duplicate_logic():
    """Test the duplicate appointment logic"""
    print("=== TESTING DUPLICATE APPOINTMENT LOGIC ===")
    
    # Try to find a user who has appointments
    users_with_appointments = User.objects.filter(appointments__isnull=False).distinct()
    
    if not users_with_appointments.exists():
        print("No users with appointments found")
        return
    
    user = users_with_appointments.first()
    print(f"Testing with user: {user.username} (ID: {user.id})")
    
    # Get their appointments
    user_appointments = Appointment.objects.filter(patient=user).order_by('-appointment_date')
    print(f"User has {user_appointments.count()} appointments")
    
    for apt in user_appointments[:5]:  # Show first 5
        print(f"  - ID={apt.id}, Date={apt.appointment_date}, Dept={apt.department.name}, Status={apt.status}")
    
    # Check for appointments on a specific date
    if user_appointments.exists():
        test_appointment = user_appointments.first()
        test_date = test_appointment.appointment_date.date()
        test_department = test_appointment.department
        
        print(f"\nTesting duplicate logic for date {test_date} in {test_department.name}")
        
        # Run the same query as in serializer validation
        duplicate_check = Appointment.objects.filter(
            patient=user,
            appointment_date__date=test_date,
            department=test_department,
            status__in=['pending', 'confirmed', 'in_progress', 'scheduled']
        ).exclude(
            status__in=['cancelled', 'completed', 'no_show']
        )
        
        print(f"Query: {duplicate_check.query}")
        print(f"Count: {duplicate_check.count()}")
        print(f"Appointments found:")
        for apt in duplicate_check:
            print(f"  - ID={apt.id}, Date={apt.appointment_date}, Status={apt.status}")

if __name__ == "__main__":
    test_duplicate_logic()