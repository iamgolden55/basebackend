#!/usr/bin/env python3
"""
Script to test appointment status change notifications
"""
import os
import django
import logging
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import models after Django setup
from api.models.medical.appointment import Appointment
from api.models.medical.appointment_notification import AppointmentNotification
from api.utils.email import send_appointment_status_update_email
from django.utils import timezone

def test_appointment_status_update(appointment_id='APT-B002EF55'):
    """Test updating an appointment status and sending notifications"""
    
    # Get the appointment
    try:
        appointment = Appointment.objects.get(appointment_id=appointment_id)
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return
    
    # Print current status
    logger.info(f"Appointment current status: {appointment.status}")
    
    # Count current notifications
    notification_count = AppointmentNotification.objects.filter(
        appointment=appointment, 
        event_type='appointment_update'
    ).count()
    logger.info(f"Current notification count: {notification_count}")
    
    # Try to update appointment status
    try:
        # Store old status
        old_status = appointment.status
        
        # Force status to pending first
        if old_status == 'confirmed':
            logger.info("Temporarily setting status to 'pending' for testing")
            Appointment.objects.filter(id=appointment.id).update(status='pending')
            appointment.refresh_from_db()
            
        # Now update to confirmed
        logger.info(f"Updating status from '{appointment.status}' to 'confirmed'")
        appointment.status = 'confirmed'
        appointment.save()
        
        # Check if status was updated
        appointment.refresh_from_db()
        logger.info(f"Status after update: {appointment.status}")
        
        # Check notifications after update
        new_notification_count = AppointmentNotification.objects.filter(
            appointment=appointment, 
            event_type='appointment_update'
        ).count()
        logger.info(f"New notification count: {new_notification_count}")
        logger.info(f"Created {new_notification_count - notification_count} new notification(s)")
        
        # List new notifications
        if new_notification_count > notification_count:
            notifications = AppointmentNotification.objects.filter(
                appointment=appointment, 
                event_type='appointment_update'
            ).order_by('-created_at')[:3]
            
            logger.info("Latest notifications:")
            for n in notifications:
                logger.info(f"  - {n.notification_type} | {n.subject} | {n.created_at}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating appointment status: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting appointment notification test")
    result = test_appointment_status_update()
    logger.info(f"Test completed with result: {result}") 