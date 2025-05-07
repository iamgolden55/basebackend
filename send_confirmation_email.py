#!/usr/bin/env python3
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.utils.email import send_appointment_status_update_email
from django.utils import timezone

def send_confirmation_email(appointment_id='APT-5F317193'):
    """Send status update email for the appointment"""
    # Find the appointment
    appointment = Appointment.objects.filter(appointment_id=appointment_id).first()
    if not appointment:
        print(f"Appointment not found: {appointment_id}")
        return
    
    print(f"Appointment: {appointment}")
    print(f"Current status: {appointment.status}")
    print(f"Patient: {appointment.patient.get_full_name()} ({appointment.patient.email})")
    
    # Update the appointment to confirmed status if it's pending
    if appointment.status == 'pending':
        old_status = appointment.status
        print(f"Updating status from '{old_status}' to 'confirmed'")
        appointment.status = 'confirmed'
        appointment.save()
        print(f"Status updated to: {appointment.status}")
    
    # Send a status update email directly
    print("Sending appointment status update email...")
    result = send_appointment_status_update_email(appointment)
    
    if result:
        print(f"✓ Status update email sent successfully to {appointment.patient.email}")
    else:
        print(f"✗ Failed to send status update email")

if __name__ == "__main__":
    send_confirmation_email()
    print("Done!") 