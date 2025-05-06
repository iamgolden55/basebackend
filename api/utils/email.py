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
        
        # Use serializer to get formatted data
        from api.serializers import AppointmentSerializer
        serializer = AppointmentSerializer(appointment)
        serializer_data = serializer.data
        
        # Patient's full name
        patient_name = serializer_data.get('patient_name')
        if not patient_name:
            patient_name = appointment.patient.email
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'doctor_name': serializer_data.get('doctor_full_name'),
            'department_name': serializer_data.get('department_name'),
            'hospital_name': serializer_data.get('hospital_name'),
            'appointment_date': serializer_data.get('formatted_date_time'),
            'appointment_date_only': serializer_data.get('formatted_date'),
            'appointment_time_only': serializer_data.get('formatted_time'),
            'is_insurance_based': appointment.is_insurance_based,
            'payment_status': appointment.payment_status,
            'frontend_url': frontend_url,
            'appointment_type': serializer_data.get('formatted_appointment_type'),
            'priority': serializer_data.get('formatted_priority'),
            'chief_complaint': appointment.chief_complaint,
            'calendar_link_included': True,
            'important_notes': serializer_data.get('important_notes'),
            'duration': serializer_data.get('appointment_duration_display')
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

def send_appointment_status_update_email(appointment):
    """
    Send a status update email when an appointment's status changes
    
    Args:
        appointment: The appointment object with updated status
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', '').rstrip('/')
        
        # Use serializer to get formatted data
        from api.serializers import AppointmentSerializer
        serializer = AppointmentSerializer(appointment)
        serializer_data = serializer.data
        
        # Patient's full name
        patient_name = serializer_data.get('patient_name')
        if not patient_name:
            patient_name = appointment.patient.email
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'doctor_name': serializer_data.get('doctor_full_name'),
            'department_name': serializer_data.get('department_name'),
            'hospital_name': serializer_data.get('hospital_name'),
            'appointment_date': serializer_data.get('formatted_date_time'),
            'appointment_date_only': serializer_data.get('formatted_date'),
            'appointment_time_only': serializer_data.get('formatted_time'),
            'appointment_status': serializer_data.get('status_display'),
            'appointment_status_code': appointment.status,
            'frontend_url': frontend_url,
            'is_cancelled': appointment.status == 'cancelled',
            'cancellation_reason': appointment.cancellation_reason if appointment.status == 'cancelled' else None,
            'is_completed': appointment.status == 'completed',
            'is_confirmed': appointment.status == 'confirmed',
            'appointment_type': serializer_data.get('formatted_appointment_type'),
            'calendar_link_included': True,
            'important_notes': serializer_data.get('important_notes')
        }
        
        html_message = render_to_string('email/appointment_status_update.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMessage(
            subject=f'Appointment Status Update - {appointment.appointment_id}',
            body=html_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
            to=[appointment.patient.email]
        )
        email.content_subtype = "html"
        
        # Generate and attach the calendar file if appointment is still active
        if appointment.status in ['confirmed', 'pending', 'rescheduled']:
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
        
        logger.info(f"Appointment status update email sent to {appointment.patient.email} for appointment {appointment.appointment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send appointment status update email: {str(e)}")
        return False

def send_appointment_reassignment_email(appointment, previous_doctor, cancellation_reason):
    """
    Send an email notification when an appointment is reassigned to another doctor
    
    Args:
        appointment: The appointment object that has been reassigned
        previous_doctor: The doctor who was previously assigned
        cancellation_reason: The reason the original doctor cancelled
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', '').rstrip('/')
        
        # Use serializer to get formatted data
        from api.serializers import AppointmentSerializer
        serializer = AppointmentSerializer(appointment)
        serializer_data = serializer.data
        
        # Patient's full name
        patient_name = serializer_data.get('patient_name')
        if not patient_name:
            patient_name = appointment.patient.email
        
        # Get previous doctor's name
        previous_doctor_name = f"Dr. {previous_doctor.user.get_full_name()}"
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'previous_doctor_name': previous_doctor_name,
            'new_doctor_name': serializer_data.get('doctor_full_name'),
            'department_name': serializer_data.get('department_name'),
            'hospital_name': serializer_data.get('hospital_name'),
            'appointment_date': serializer_data.get('formatted_date_time'),
            'appointment_date_only': serializer_data.get('formatted_date'),
            'appointment_time_only': serializer_data.get('formatted_time'),
            'cancellation_reason': cancellation_reason,
            'frontend_url': frontend_url,
            'appointment_type': serializer_data.get('formatted_appointment_type'),
            'calendar_link_included': True,
            'important_notes': serializer_data.get('important_notes')
        }
        
        html_message = render_to_string('email/appointment_reassignment.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMessage(
            subject=f'Your Appointment Has Been Reassigned - {appointment.appointment_id}',
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
        
        logger.info(f"Appointment reassignment email sent to {appointment.patient.email} for appointment {appointment.appointment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send appointment reassignment email: {str(e)}")
        return False 