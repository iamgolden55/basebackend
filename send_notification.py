#!/usr/bin/env python3
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.models.medical.appointment_notification import AppointmentNotification
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils.html import strip_tags

def check_and_send_notifications(appointment_id='APT-5F317193'):
    """Check notification status and send any pending notifications"""
    # Find the appointment
    appointment = Appointment.objects.filter(appointment_id=appointment_id).first()
    if not appointment:
        print(f"Appointment not found: {appointment_id}")
        return
    
    print(f"Appointment: {appointment}")
    print(f"Status: {appointment.status}")
    print(f"Patient Email: {appointment.patient.email}")
    
    # Get all notifications for this appointment
    notifications = AppointmentNotification.objects.filter(appointment=appointment)
    print(f"Total notifications: {notifications.count()}")
    
    # Print pending notifications
    pending = notifications.filter(status='pending')
    print(f"Pending notifications: {pending.count()}")
    for n in pending:
        print(f" - ID: {n.id} | Type: {n.notification_type} | Event: {n.event_type} | Template: {n.template_name}")
    
    # Use direct email sending for the appointment status update
    # This is a workaround for the template path issue
    if pending.count() > 0:
        print("Using direct email sending method...")
        for notification in pending:
            try:
                # Get the context for the template
                context = notification._get_template_context()
                
                # Get the template path - note that the templates are in api/templates/email/
                template_path = f"email/{notification.template_name}.html"
                print(f"Looking for template: {template_path}")
                
                # Render the template
                html_message = render_to_string(template_path, context)
                text_message = strip_tags(html_message)
                
                # Create and send the email
                email = EmailMessage(
                    subject=notification.subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.recipient.email]
                )
                email.content_subtype = "html"
                
                # Try to generate and attach calendar file for appointment
                from api.utils.email import generate_ics_for_appointment
                try:
                    ics_content = generate_ics_for_appointment(appointment)
                    email.attach(
                        f'appointment_{appointment.appointment_id}.ics',
                        ics_content,
                        'text/calendar'
                    )
                    print("Calendar attachment generated")
                except Exception as e:
                    print(f"Failed to generate calendar attachment: {str(e)}")
                
                # Send the email
                result = email.send(fail_silently=False)
                
                # Update notification status
                notification.status = 'sent'
                notification.save()
                
                print(f"Email sent successfully to {notification.recipient.email}")
            except Exception as e:
                print(f"Error sending email: {str(e)}")
    
    # Check notification status after sending
    pending_after = notifications.filter(status='pending').count()
    sent = notifications.filter(status='sent').count()
    print(f"Notifications remaining pending: {pending_after}")
    print(f"Notifications sent: {sent}")

if __name__ == "__main__":
    check_and_send_notifications()
    print("Done!") 