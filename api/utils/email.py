import os
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from .calendar import generate_ics_for_appointment
from django.utils import timezone

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
        dict: Information about the email sending status
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
            
        # Get appropriate context based on appointment status
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'appointment_date': appointment.appointment_date,
            'appointment_date_only': appointment.appointment_date.strftime('%d %B, %Y'),
            'appointment_time_only': appointment.appointment_date.strftime('%I:%M %p'),
            'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}",
            'department_name': appointment.department.name,
            'hospital_name': appointment.hospital.name,
            'appointment_type': serializer_data.get('formatted_appointment_type'),
            'appointment_status': serializer_data.get('status_display'),
            'frontend_url': frontend_url,
            'hospital_phone': appointment.hospital.phone,
            'hospital_email': appointment.hospital.email,
            # Flags for template conditionals
            'is_confirmed': appointment.status == 'confirmed',
            'is_cancelled': appointment.status == 'cancelled',
            'is_completed': appointment.status == 'completed',
            'cancellation_reason': appointment.cancellation_reason if hasattr(appointment, 'cancellation_reason') else None,
        }
        
        # Special context for completed appointments
        if appointment.status == 'completed':
            # Include dashboard URL for accessing medical records
            dashboard_url = f"{frontend_url}/dashboard/medical-records"
            context['dashboard_url'] = dashboard_url
        
        # Add calendar attachment for confirmed appointments
        if appointment.status == 'confirmed':
            # Get calendar data from appointment
            from api.utils.calendar import generate_ics_for_appointment
            ics_content = generate_ics_for_appointment(appointment)
            
            # Important notes
            context['important_notes'] = [
                'Please arrive 15 minutes before your appointment',
                'Bring your ID and insurance card',
                'Bring any relevant medical records'
            ]
        else:
            ics_content = None
        
        # Also create notification records in the database
        from api.models.medical.appointment_notification import AppointmentNotification
        notification = AppointmentNotification.create_status_update_notification(appointment)
            
        # Send the actual email
        subject = f"Appointment Status Update - {appointment.appointment_id}"
        to_email = appointment.patient.email
        
        # Generate HTML content
        html_message = render_to_string('email/appointment_status_update.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
            to=[to_email]
        )
        email.content_subtype = "html"
        
        # Add calendar attachment if necessary
        calendar_attached = False
        if appointment.status == 'confirmed' and ics_content:
            email.attach(
                f'appointment_{appointment.appointment_id}.ics',
                ics_content,
                'text/calendar'
            )
            calendar_attached = True
            logger.info(f"Calendar attachment added for appointment {appointment.appointment_id}")
        
        # Send the email
        email.send(fail_silently=False)
        
        # Update notification status
        if notification:
            notification.status = 'sent'
            notification.sent_time = timezone.now()
            notification.save()
        
        # Log the send status
        logger.info(f"Appointment status update email sent to {to_email} for appointment {appointment.appointment_id}")
        
        # Return information about the send status
        return {
            'sent': True,
            'to': to_email,
            'subject': subject,
            'template': 'appointment_status_update',
            'appointment_id': appointment.appointment_id,
            'status': appointment.status,
            'notification_id': notification.id if notification else None,
            'calendar_attached': calendar_attached,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending appointment status update email: {str(e)}")
        return {
            'sent': False,
            'error': str(e),
            'appointment_id': appointment.appointment_id,
            'status': appointment.status,
            'timestamp': timezone.now().isoformat()
        }

def send_appointment_reassignment_email(appointment, previous_doctor, cancellation_reason):
    """
    Send an email when an appointment is reassigned to another doctor
    
    Args:
        appointment: The appointment object with the new doctor
        previous_doctor: The original doctor who is no longer available
        cancellation_reason: The reason the original doctor cannot fulfill the appointment
    
    Returns:
        dict: Information about the email sending status
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
        
        # Previous doctor's name
        previous_doctor_name = f"Dr. {previous_doctor.user.get_full_name()}"
        
        # New doctor's name
        new_doctor_name = serializer_data.get('doctor_full_name')
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment.appointment_id,
            'previous_doctor_name': previous_doctor_name,
            'doctor_name': new_doctor_name,
            'department_name': serializer_data.get('department_name'),
            'hospital_name': serializer_data.get('hospital_name'),
            'appointment_date': serializer_data.get('formatted_date_time'),
            'appointment_date_only': serializer_data.get('formatted_date'),
            'appointment_time_only': serializer_data.get('formatted_time'),
            'frontend_url': frontend_url,
            'cancellation_reason': cancellation_reason,
            'appointment_type': serializer_data.get('formatted_appointment_type'),
            'calendar_link_included': True
        }
        
        # Create notification record in the database
        from api.models.medical.appointment_notification import AppointmentNotification
        
        notification = AppointmentNotification.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_reassigned',
            recipient=appointment.patient,
            subject=f"Appointment Reassigned - {appointment.appointment_id}",
            template_name='appointment_reassigned',
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Create SMS notification if patient has phone
        sms_notification = None
        if appointment.patient.phone:
            sms_notification = AppointmentNotification.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='appointment_reassigned',
                recipient=appointment.patient,
                subject=f"Appointment Reassigned - {appointment.appointment_id}",
                message=(
                    f"Your appointment has been reassigned from {previous_doctor_name} to {new_doctor_name}. "
                    f"Same date and time: {appointment.appointment_date.strftime('%d/%m/%Y at %I:%M %p')}. "
                    f"Please check your email for details."
                ),
                status='pending',
                scheduled_time=timezone.now()
            )
        
        # Render the email template
        html_message = render_to_string('email/appointment_reassigned.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMessage(
            subject=f'Appointment Reassigned - {appointment.appointment_id}',
            body=html_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
            to=[appointment.patient.email]
        )
        email.content_subtype = "html"
        
        # Generate and attach the calendar file
        calendar_attached = False
        try:
            ics_content = generate_ics_for_appointment(appointment)
            email.attach(
                f'appointment_{appointment.appointment_id}.ics',
                ics_content,
                'text/calendar'
            )
            logger.info(f"Calendar attachment generated for reassigned appointment {appointment.appointment_id}")
            calendar_attached = True
        except Exception as e:
            logger.error(f"Failed to generate calendar attachment for reassigned appointment: {str(e)}")
        
        # Send the email
        email.send(fail_silently=False)
        
        # Update notification status to 'sent'
        notification.status = 'sent'
        notification.sent_time = timezone.now()
        notification.save()
        
        if sms_notification:
            sms_notification.status = 'sent'
            sms_notification.sent_time = timezone.now()
            sms_notification.save()
        
        logger.info(f"Appointment reassignment email sent to {appointment.patient.email} for appointment {appointment.appointment_id}")
        
        return {
            'success': True,
            'recipient': appointment.patient.email,
            'notification_id': notification.id,
            'sms_notification_id': sms_notification.id if sms_notification else None,
            'notification_status': 'sent',
            'calendar_attached': calendar_attached,
            'sent_at': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send appointment reassignment email: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'recipient': getattr(appointment, 'patient', {}).get('email', 'unknown')
        } 