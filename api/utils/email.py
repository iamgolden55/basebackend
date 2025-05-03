import os
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from .calendar import generate_ics_for_appointment

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """
    Send a welcome email to newly verified users with their account details
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL').rstrip('/')
        
        context = {
            'user': user,
            'frontend_url': frontend_url
        }
        
        html_message = render_to_string('email/welcome.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Welcome to PHB - Your Account is Ready! 🎉',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False

def send_verification_email(user, verification_link):
    """
    Send an email verification link to new users
    """
    try:
        context = {
            'user': user,
            'verification_link': verification_link,
        }
        
        html_message = render_to_string('email/verification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Verify Your PHB Account',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False

def send_appointment_confirmation_email(appointment):
    """
    Send a booking summary confirmation email after appointment is confirmed
    
    Args:
        appointment: The appointment object with all booking details
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', '').rstrip('/')
        
        # Patient's full name
        patient_name = appointment.patient.get_full_name()
        if not patient_name:
            patient_name = appointment.patient.email
            
        # Doctor's full name
        doctor_name = appointment.doctor.full_name
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'doctor_name': doctor_name,
            'department_name': appointment.department.name,
            'hospital_name': appointment.hospital.name,
            'appointment_date': appointment.appointment_date,
            'is_insurance_based': appointment.is_insurance_based,
            'payment_status': appointment.payment_status,
            'frontend_url': frontend_url,
            'appointment_type': dict(appointment.APPOINTMENT_TYPE_CHOICES).get(appointment.appointment_type, appointment.appointment_type),
            'priority': dict(appointment.PRIORITY_CHOICES).get(appointment.priority, appointment.priority),
            'chief_complaint': appointment.chief_complaint,
            'calendar_link_included': True,
        }
        
        html_message = render_to_string('email/appointment_booking_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMessage(
            subject=f'Your Appointment Confirmation - {appointment.appointment_id}',
            body=html_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
            to=[appointment.patient.email]
        )
        email.content_subtype = "html"
        
        # Generate and attach the calendar file
        try:
            ics_content = generate_ics_for_appointment(appointment)
            email.attach(
                f'appointment_{appointment.appointment_id}.ics',
                ics_content,
                'text/calendar'
            )
            logger.info(f"Calendar attachment generated for appointment {appointment.appointment_id}")
        except Exception as e:
            logger.error(f"Failed to generate calendar attachment: {str(e)}")
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.info(f"Appointment confirmation email sent to {appointment.patient.email} for appointment {appointment.appointment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send appointment confirmation email: {str(e)}")
        return False 