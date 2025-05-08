#!/usr/bin/env python3
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.models.medical.appointment_notification import AppointmentNotification

def check_notification_status(appointment_id='APT-5F317193'):
    """Check notification status for the appointment"""
    # Find the appointment
    appointment = Appointment.objects.filter(appointment_id=appointment_id).first()
    if not appointment:
        print(f"Appointment not found: {appointment_id}")
        return
    
    print(f"Appointment: {appointment}")
    print(f"Current status: {appointment.status}")
    print(f"Patient: {appointment.patient.get_full_name()} ({appointment.patient.email})")
    
    # Get all notifications for this appointment
    notifications = AppointmentNotification.objects.filter(appointment=appointment).order_by('-created_at')
    print(f"Total notifications: {notifications.count()}")
    
    # Count by status
    pending_count = notifications.filter(status='pending').count()
    sent_count = notifications.filter(status='sent').count()
    failed_count = notifications.filter(status='failed').count()
    
    print(f"Status summary:")
    print(f" - Pending: {pending_count}")
    print(f" - Sent: {sent_count}")
    print(f" - Failed: {failed_count}")
    
    # Print notification details
    print("\nNotification details:")
    for i, n in enumerate(notifications[:10], 1):  # Show the most recent 10
        print(f"{i}. {n.notification_type} | {n.event_type} | {n.subject} | Status: {n.status}")
        if n.sent_time:
            print(f"   Sent: {n.sent_time}")

if __name__ == "__main__":
    check_notification_status()
    print("\nDone!") 