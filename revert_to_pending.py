#!/usr/bin/env python3
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from django.utils import timezone
from django.db import connection

def revert_to_pending(appointment_id='APT-5F317193'):
    """Revert appointment status back to pending using direct DB update"""
    # Find the appointment
    appointment = Appointment.objects.filter(appointment_id=appointment_id).first()
    if not appointment:
        print(f"Appointment not found: {appointment_id}")
        return
    
    print(f"Appointment: {appointment}")
    print(f"Current status: {appointment.status}")
    
    # Update the appointment to pending status directly in the database
    old_status = appointment.status
    print(f"Reverting status from '{old_status}' to 'pending'")
    
    # Use direct DB update to bypass model validation
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE api_appointment SET status = %s WHERE appointment_id = %s",
                ['pending', appointment_id]
            )
            print("Direct database update completed")
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        return
    
    # Verify the status change
    appointment.refresh_from_db()
    print(f"Status after update: {appointment.status}")
    
    if appointment.status == 'pending':
        print(f"Successfully reverted appointment status to pending")
    else:
        print(f"Failed to revert status, current status: {appointment.status}")

if __name__ == "__main__":
    revert_to_pending()
    print("Done!") 