import os
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
import os
import base64
from .calendar import generate_ics_for_appointment
from django.utils import timezone
from io import BytesIO
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

def _resolve_contact_email(email):
    """
    Resolve masked hospital admin emails to real contact emails
    
    Args:
        email: Email address (could be masked like admin.stnicholas@example.com)
        
    Returns:
        str: Real contact email address
    """
    try:
        # Check if this is a masked hospital admin email
        if email.endswith('@example.com') or email.endswith('@phb.com'):
            from api.models.medical.hospital_auth import HospitalAdmin
            
            try:
                admin = HospitalAdmin.objects.get(email=email)
                
                # Priority order for real email resolution:
                # 1. contact_email field (the real email)
                if admin.contact_email:
                    return admin.contact_email
                
                # 2. Hospital's contact email
                if hasattr(admin, 'hospital') and admin.hospital and admin.hospital.email:
                    return admin.hospital.email
                
                # 3. User's email (if different from admin username)
                if hasattr(admin, 'user') and admin.user and admin.user.email != email:
                    return admin.user.email
                
            except HospitalAdmin.DoesNotExist:
                logger.warning(f"Hospital admin not found for masked email: {email}")
    
    except Exception as e:
        logger.error(f"Error resolving contact email for {email}: {e}")
    
    # Return original email if resolution fails or not a masked email
    return email

def send_message_notification_email(recipient_email, recipient_name, sender_name, message_preview, conversation_title):
    """
    Send email notification when a new message is received
    Automatically resolves masked emails to real contact emails
    """
    try:
        # Resolve masked email to real contact email
        real_email = _resolve_contact_email(recipient_email)
        if real_email != recipient_email:
            logger.debug(f"Resolved masked email {recipient_email} to real email {real_email}")
            recipient_email = real_email
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')
        
        context = {
            'recipient_name': recipient_name,
            'sender_name': sender_name,
            'message_preview': message_preview,
            'conversation_title': conversation_title,
            'frontend_url': frontend_url,
            'timestamp': timezone.now()
        }
        
        # Try to use a dedicated template, fall back to simple HTML
        try:
            html_message = render_to_string('email/message_notification.html', context)
        except:
            # Fallback HTML template
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #007bff; margin-bottom: 20px;">💬 New Message</h2>
                    
                    <p>Hi {recipient_name},</p>
                    
                    <p>You have a new message from <strong>{sender_name}</strong> in the conversation:</p>
                    <h3 style="color: #495057;">{conversation_title}</h3>
                    
                    <div style="background: white; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #6c757d; font-style: italic;">"{message_preview}"</p>
                    </div>
                    
                    <a href="{frontend_url}/chat" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 20px;">
                        View Message
                    </a>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="color: #6c757d; font-size: 14px; margin: 0;">
                        This is an automated notification from your healthcare communication system.<br>
                        Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
            </html>
            """
        
        plain_message = f"""
        New Message from {sender_name}
        
        Hi {recipient_name},
        
        You have a new message in: {conversation_title}
        
        Message: "{message_preview}"
        
        View your messages at: {frontend_url}/chat
        
        Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        send_mail(
            subject=f'💬 New message from {sender_name}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=True,  # Don't break the message sending if email fails
        )
        
        logger.debug(f"Message notification email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send message notification email to {recipient_email}: {str(e)}")
        return False

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


def send_payment_confirmation_email(payment_transaction):
    """
    Send a payment confirmation email after successful payment
    
    Args:
        payment_transaction: The PaymentTransaction object with payment details
    
    Returns:
        dict: Information about the email sending status
    """
    try:
        
        frontend_url = os.environ.get('NEXTJS_URL', '').rstrip('/')
        
        # Patient's name
        patient = payment_transaction.patient
        patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email
        
        logger.debug(f"Sending payment confirmation email to {patient.email} for payment {payment_transaction.transaction_id}")
        
        # Build context based on whether appointment exists (payment-first vs appointment-first)
        context = {
            'patient_name': patient_name,
            'payment_id': payment_transaction.transaction_id,
            'payment_status': payment_transaction.get_payment_status_display(),
            'amount': payment_transaction.amount_display,
            'currency': payment_transaction.currency,
            'payment_method': payment_transaction.get_payment_method_display(),
            'payment_provider': payment_transaction.payment_provider.title(),
            'payment_date': payment_transaction.completed_at or payment_transaction.created_at,
            'frontend_url': frontend_url,
        }
        
        # If appointment exists, add appointment details
        if payment_transaction.appointment:
            appointment = payment_transaction.appointment
            
            # Get formatted appointment data
            from api.serializers import AppointmentSerializer
            serializer = AppointmentSerializer(appointment)
            serializer_data = serializer.data
            
            context.update({
                'appointment_id': appointment.appointment_id,
                'appointment_date': appointment.appointment_date,
                'doctor_name': serializer_data.get('doctor_full_name'),
                'department_name': serializer_data.get('department_name'),
                'hospital_name': serializer_data.get('hospital_name'),
                'has_appointment': True,
                'appointment_type': serializer_data.get('formatted_appointment_type'),
            })
            
            email_subject = f'Payment Confirmation - {appointment.appointment_id}'
        else:
            # Payment-first approach - no appointment yet
            context.update({
                'has_appointment': False,
                'appointment_id': 'Pending',
                'doctor_name': 'To be assigned',
                'hospital_name': 'PHB Network Hospital',
                'department_name': 'To be determined',
            })
            
            email_subject = f'Payment Received - {payment_transaction.transaction_id}'
        
        
        # Render Gmail-optimized HTML template (NO PLAIN TEXT!)
        html_message = render_to_string('email/payment_confirmation_html_only.html', context)
        
        
        # Create Gmail-friendly HTML-only email
        email = EmailMessage(
            subject=email_subject,
            body=html_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
            to=[patient.email]
        )
        email.content_subtype = "html"  # Force HTML display
        
        # Gmail-specific headers to force HTML rendering
        email.extra_headers = {
            'Content-Type': 'text/html; charset=UTF-8',
            'MIME-Version': '1.0',
            'X-Priority': '3',
            'X-MSMail-Priority': 'Normal',
            'X-Mailer': 'PHB Hospital System',
            'X-MimeOLE': 'Produced By PHB Medical Platform'
        }
        
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.debug(f"Payment confirmation email sent to {patient.email} for payment {payment_transaction.transaction_id}")
        
        return {
            'success': True,
            'recipient': patient.email,
            'subject': email_subject,
            'payment_id': payment_transaction.transaction_id,
            'has_appointment': payment_transaction.appointment is not None,
            'sent_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        logger.error(f"Payment {payment_transaction.transaction_id} email error: {type(e).__name__}")
        return {
            'success': False,
            'error': str(e),
            'payment_id': payment_transaction.transaction_id,
            'recipient': payment_transaction.patient.email if payment_transaction.patient else 'unknown'
        }


# ============================================================================
# PRESCRIPTION REQUEST EMAIL FUNCTIONS
# ============================================================================

def send_prescription_request_confirmation(
    patient_email,
    patient_name,
    request_reference,
    medications,
    urgency,
    expected_days,
    pharmacy_name,
    pharmacy_address,
    hospital_name,
    request_date
):
    """
    Send confirmation email to patient after submitting prescription request

    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        request_reference (str): Prescription request reference number (e.g., REQ-123456)
        medications (list): List of medication dicts with: name, strength, form, is_repeat
        urgency (str): 'urgent' or 'routine'
        expected_days (str): Expected processing time (e.g., "1-3" or "7-10")
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        hospital_name (str): Name of patient's primary hospital
        request_date (datetime): When the request was submitted

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        context = {
            'patient_name': patient_name,
            'request_reference': request_reference,
            'request_date': request_date.strftime('%d %B, %Y at %I:%M %p'),
            'urgency': urgency,
            'medication_count': len(medications),
            'medications': medications,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'hospital_name': hospital_name,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_request_confirmation.html', context)
        plain_message = strip_tags(html_message)

        subject = f'Prescription Request Received - {request_reference}'
        if urgency == 'urgent':
            subject = f'🚨 URGENT Prescription Request Received - {request_reference}'

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[patient_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Prescription request confirmation email sent to {patient_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send prescription request confirmation email: {str(e)}")
        return False


def send_prescription_request_to_doctors(
    hospital_id,
    request_reference,
    patient_name,
    patient_hpn,
    patient_dob,
    patient_age,
    allergies,
    medications,
    urgency,
    request_notes,
    pharmacy_name,
    pharmacy_address,
    request_date
):
    """
    Notify all prescribing doctors in a hospital about new prescription request

    Args:
        hospital_id (int): ID of the hospital
        request_reference (str): Prescription request reference number
        patient_name (str): Patient's full name
        patient_hpn (str): Patient's HPN (Health Person Number)
        patient_dob (str): Patient's date of birth
        patient_age (int): Patient's age in years
        allergies (str): Known allergies (comma-separated) or None
        medications (list): List of medication dicts with: name, strength, form, is_repeat, reason
        urgency (str): 'urgent' or 'routine'
        request_notes (str): Additional notes from patient
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        request_date (datetime): When the request was submitted

    Returns:
        dict: Information about the email sending status
    """
    try:
        from api.models.medical.doctor import Doctor

        # Get all doctors at the hospital who can prescribe
        doctors = Doctor.objects.filter(
            hospital_id=hospital_id,
            can_prescribe=True,
            user__is_active=True
        ).select_related('user')

        if not doctors.exists():
            logger.warning(f"No prescribing doctors found for hospital {hospital_id}")
            return {
                'success': False,
                'error': 'No prescribing doctors found',
                'doctors_notified': 0
            }

        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        sent_count = 0
        failed_emails = []

        for doctor in doctors:
            try:
                context = {
                    'doctor_name': doctor.user.get_full_name(),
                    'patient_name': patient_name,
                    'patient_hpn': patient_hpn,
                    'patient_dob': patient_dob,
                    'patient_age': patient_age,
                    'allergies': allergies,
                    'request_reference': request_reference,
                    'request_date': request_date.strftime('%d %B, %Y at %I:%M %p'),
                    'urgency': urgency,
                    'medication_count': len(medications),
                    'medications': medications,
                    'request_notes': request_notes,
                    'pharmacy_name': pharmacy_name,
                    'pharmacy_address': pharmacy_address,
                    'frontend_url': frontend_url,
                }

                html_message = render_to_string('email/prescription_request_new_doctor.html', context)
                plain_message = strip_tags(html_message)

                subject = f'New Prescription Request - {request_reference}'
                if urgency == 'urgent':
                    subject = f'🚨 URGENT Prescription Request - {request_reference}'

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
                    recipient_list=[doctor.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                sent_count += 1
                logger.info(f"Prescription request notification sent to Dr. {doctor.user.get_full_name()}")

            except Exception as e:
                logger.error(f"Failed to send email to doctor {doctor.user.email}: {str(e)}")
                failed_emails.append({
                    'doctor_email': doctor.user.email,
                    'error': str(e)
                })

        return {
            'success': True,
            'doctors_notified': sent_count,
            'total_doctors': doctors.count(),
            'failed_emails': failed_emails
        }

    except Exception as e:
        logger.error(f"Failed to send prescription request to doctors: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'doctors_notified': 0
        }


def send_prescription_approved_notification(
    patient_email,
    patient_name,
    request_reference,
    doctor_name,
    medications,
    clinical_notes,
    pharmacy_name,
    pharmacy_address,
    pickup_deadline,
    approval_date,
    requires_payment=False,
    is_exempt=False
):
    """
    Notify patient that their prescription request has been approved

    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        request_reference (str): Prescription request reference number
        doctor_name (str): Name of prescribing doctor
        medications (list): List of approved medication dicts with: name, strength, form, quantity, dosage_instructions, refills_allowed
        clinical_notes (str): Clinical notes from prescriber
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        pickup_deadline (datetime): Deadline for collecting prescription
        approval_date (datetime): When prescription was approved
        requires_payment (bool): Whether patient needs to pay prescription fee
        is_exempt (bool): Whether patient is exempt from prescription charges

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        # Check if any medications have refills
        has_refills = any(med.get('refills_allowed', 0) > 0 for med in medications)

        context = {
            'patient_name': patient_name,
            'request_reference': request_reference,
            'doctor_name': doctor_name,
            'approval_date': approval_date.strftime('%d %B, %Y'),
            'medications': medications,
            'clinical_notes': clinical_notes,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'pickup_deadline': pickup_deadline.strftime('%d %B, %Y'),
            'has_refills': has_refills,
            'requires_payment': requires_payment,
            'is_exempt': is_exempt,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_approved.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Prescription Approved ✅ - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[patient_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Prescription approval email sent to {patient_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send prescription approval email: {str(e)}")
        return False


def send_prescription_rejected_notification(
    patient_email,
    patient_name,
    request_reference,
    doctor_name,
    rejection_reason,
    medications,
    requires_follow_up,
    review_date
):
    """
    Notify patient that their prescription request has been rejected

    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        request_reference (str): Prescription request reference number
        doctor_name (str): Name of reviewing doctor
        rejection_reason (str): Detailed reason for rejection
        medications (list): List of medication dicts with: name, strength, form, approved (bool)
        requires_follow_up (bool): Whether follow-up appointment is required
        review_date (datetime): When request was reviewed

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        # Check if any medications were partially approved
        has_partial_approval = any(med.get('approved', False) for med in medications)

        context = {
            'patient_name': patient_name,
            'request_reference': request_reference,
            'doctor_name': doctor_name,
            'review_date': review_date.strftime('%d %B, %Y'),
            'rejection_reason': rejection_reason,
            'medications': medications,
            'requires_follow_up': requires_follow_up,
            'has_partial_approval': has_partial_approval,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_rejected.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Prescription Request - Action Required ⚠️ - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[patient_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Prescription rejection email sent to {patient_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send prescription rejection email: {str(e)}")
        return False


def send_prescription_ready_notification(
    patient_email,
    patient_name,
    request_reference,
    medications,
    pharmacy_name,
    pharmacy_address,
    pharmacy_phone,
    pharmacy_hours,
    pickup_deadline,
    requires_payment=False,
    is_exempt=False
):
    """
    Notify patient that their prescription is ready for collection at pharmacy

    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        request_reference (str): Prescription request reference number
        medications (list): List of medication dicts with: name, strength, form, quantity, refills_allowed
        pharmacy_name (str): Name of pharmacy
        pharmacy_address (str): Full address of pharmacy
        pharmacy_phone (str): Pharmacy phone number or None
        pharmacy_hours (str): Opening hours or None
        pickup_deadline (datetime): Deadline for collecting prescription
        requires_payment (bool): Whether patient needs to pay prescription fee
        is_exempt (bool): Whether patient is exempt from prescription charges

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        # Check if any medications have refills
        has_refills = any(med.get('refills_allowed', 0) > 0 for med in medications)

        context = {
            'patient_name': patient_name,
            'request_reference': request_reference,
            'medication_count': len(medications),
            'medications': medications,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'pharmacy_phone': pharmacy_phone,
            'pharmacy_hours': pharmacy_hours,
            'pickup_deadline': pickup_deadline.strftime('%d %B, %Y'),
            'has_refills': has_refills,
            'requires_payment': requires_payment,
            'is_exempt': is_exempt,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_ready_collection.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Prescription Ready for Collection 💊 - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[patient_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Prescription ready notification sent to {patient_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send prescription ready notification: {str(e)}")
        return False


# ==================== PHARMACIST TRIAGE EMAIL FUNCTIONS ====================


def send_prescription_request_to_pharmacist(
    pharmacist_email,
    pharmacist_name,
    patient_name,
    patient_hpn,
    patient_dob,
    patient_age,
    request_reference,
    request_date,
    urgency,
    medications,
    pharmacy_name,
    pharmacy_address,
    triage_category,
    triage_reason,
    allergies=None,
    current_medications=None,
    request_notes=None
):
    """
    Notify clinical pharmacist of a new prescription request for triage and review

    Args:
        pharmacist_email (str): Pharmacist's email address
        pharmacist_name (str): Pharmacist's full name
        patient_name (str): Patient's full name
        patient_hpn (str): Patient's HPN number
        patient_dob (str): Patient's date of birth (formatted)
        patient_age (int): Patient's age in years
        request_reference (str): Prescription request reference number
        request_date (str): Date request was submitted (formatted)
        urgency (str): 'urgent' or 'routine'
        medications (list): List of medication dicts with: name, strength, form, quantity, dosage, is_repeat, reason
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        triage_category (str): Auto-assigned triage category (e.g., 'ROUTINE_REPEAT', 'URGENT_NEW')
        triage_reason (str): Explanation of triage category assignment
        allergies (str, optional): Known allergies
        current_medications (str, optional): Current medications
        request_notes (str, optional): Patient's additional notes

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        context = {
            'pharmacist_name': pharmacist_name,
            'patient_name': patient_name,
            'patient_hpn': patient_hpn,
            'patient_dob': patient_dob,
            'patient_age': patient_age,
            'request_reference': request_reference,
            'request_date': request_date,
            'urgency': urgency,
            'medication_count': len(medications),
            'medications': medications,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'triage_category': triage_category,
            'triage_reason': triage_reason,
            'allergies': allergies,
            'current_medications': current_medications,
            'request_notes': request_notes,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_request_new_pharmacist.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'{"🚨 URGENT" if urgency == "urgent" else "💊 New"} Prescription Request for Review - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[pharmacist_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Pharmacist triage notification sent to {pharmacist_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send pharmacist triage notification: {str(e)}")
        return False


def send_pharmacist_approved_prescription_to_doctor(
    doctor_email,
    doctor_name,
    pharmacist_name,
    patient_name,
    patient_hpn,
    patient_dob,
    patient_age,
    request_reference,
    request_id,
    request_date,
    review_date,
    medications,
    pharmacy_name,
    pharmacy_address,
    pharmacist_notes=None,
    drug_interactions=None,
    monitoring_required=None,
    allergies=None
):
    """
    Notify physician that pharmacist has approved prescription and it's ready for final authorization

    Args:
        doctor_email (str): Doctor's email address
        doctor_name (str): Doctor's full name
        pharmacist_name (str): Pharmacist's full name
        patient_name (str): Patient's full name
        patient_hpn (str): Patient's HPN number
        patient_dob (str): Patient's date of birth (formatted)
        patient_age (int): Patient's age in years
        request_reference (str): Prescription request reference number
        request_id (str): Database ID of the request
        request_date (str): Date request was submitted (formatted)
        review_date (str): Date pharmacist reviewed (formatted)
        medications (list): List of medication dicts with: name, strength, form, approved_quantity, approved_dosage, refills_allowed
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        pharmacist_notes (str, optional): Pharmacist's clinical notes
        drug_interactions (str, optional): Drug interaction check results
        monitoring_required (str, optional): Required monitoring (e.g., lab tests)
        allergies (str, optional): Known allergies

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        context = {
            'doctor_name': doctor_name,
            'pharmacist_name': pharmacist_name,
            'patient_name': patient_name,
            'patient_hpn': patient_hpn,
            'patient_dob': patient_dob,
            'patient_age': patient_age,
            'request_reference': request_reference,
            'request_id': request_id,
            'request_date': request_date,
            'review_date': review_date,
            'medication_count': len(medications),
            'medications': medications,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'pharmacist_notes': pharmacist_notes,
            'drug_interactions': drug_interactions,
            'monitoring_required': monitoring_required,
            'allergies': allergies,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_pharmacist_approved.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Pharmacist-Approved Prescription - Awaiting Your Authorization - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[doctor_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Pharmacist-approved prescription notification sent to {doctor_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send pharmacist-approved prescription notification: {str(e)}")
        return False


def send_prescription_escalation_to_physician(
    doctor_email,
    doctor_name,
    pharmacist_name,
    patient_name,
    patient_hpn,
    patient_dob,
    patient_age,
    request_reference,
    request_id,
    request_date,
    review_date,
    urgency,
    escalation_category,
    escalation_reason,
    medications,
    pharmacy_name,
    pharmacy_address,
    clinical_concerns=None,
    pharmacist_recommendation=None,
    allergies=None,
    current_medications=None,
    medical_conditions=None,
    request_notes=None
):
    """
    Notify physician that prescription request requires escalation and direct physician review

    Args:
        doctor_email (str): Doctor's email address
        doctor_name (str): Doctor's full name
        pharmacist_name (str): Pharmacist's full name
        patient_name (str): Patient's full name
        patient_hpn (str): Patient's HPN number
        patient_dob (str): Patient's date of birth (formatted)
        patient_age (int): Patient's age in years
        request_reference (str): Prescription request reference number
        request_id (str): Database ID of the request
        request_date (str): Date request was submitted (formatted)
        review_date (str): Date pharmacist escalated (formatted)
        urgency (str): 'urgent' or 'routine'
        escalation_category (str): Escalation category (e.g., 'COMPLEX_CASE', 'CONTROLLED_SUBSTANCE')
        escalation_reason (str): Detailed reason for escalation
        medications (list): List of medication dicts with: name, strength, form, quantity, dosage, is_repeat, controlled, flagged, flag_reason
        pharmacy_name (str): Name of nominated pharmacy
        pharmacy_address (str): Full address of pharmacy
        clinical_concerns (str, optional): Specific clinical concerns identified
        pharmacist_recommendation (str, optional): Pharmacist's recommendation
        allergies (str, optional): Known allergies
        current_medications (str, optional): Current medications
        medical_conditions (str, optional): Known medical conditions
        request_notes (str, optional): Patient's additional notes

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        context = {
            'doctor_name': doctor_name,
            'pharmacist_name': pharmacist_name,
            'patient_name': patient_name,
            'patient_hpn': patient_hpn,
            'patient_dob': patient_dob,
            'patient_age': patient_age,
            'request_reference': request_reference,
            'request_id': request_id,
            'request_date': request_date,
            'review_date': review_date,
            'urgency': urgency,
            'escalation_category': escalation_category,
            'escalation_reason': escalation_reason,
            'medication_count': len(medications),
            'medications': medications,
            'pharmacy_name': pharmacy_name,
            'pharmacy_address': pharmacy_address,
            'clinical_concerns': clinical_concerns,
            'pharmacist_recommendation': pharmacist_recommendation,
            'allergies': allergies,
            'current_medications': current_medications,
            'medical_conditions': medical_conditions,
            'request_notes': request_notes,
            'frontend_url': frontend_url,
        }

        html_message = render_to_string('email/prescription_needs_physician_review.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'{"🚨 URGENT" if urgency == "urgent" else "⚕️"} Prescription Escalation - Physician Review Required - {request_reference}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[doctor_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Prescription escalation notification sent to {doctor_email} for {request_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send prescription escalation notification: {str(e)}")
        return False


# =============================================================================
# PROFESSIONAL REGISTRATION EMAIL FUNCTIONS
# =============================================================================

def send_professional_application_confirmation_email(user, application, password=None):
    """
    Send confirmation email when a professional submits their application.

    Args:
        user: User object who submitted the application
        application: ProfessionalApplication object
        password: Optional password (for new users only)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')

        context = {
            'user_name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'professional_type': application.get_professional_type_display(),
            'application_number': application.application_reference,  # Use application_reference
            'application_reference': application.application_reference,
            'submitted_date': application.submitted_date if application.submitted_date else application.created_at,
            'registration_body': application.home_registration_body,
            'registration_number': application.home_registration_number,
            'password': password,  # Only included for new users
            'is_new_user': password is not None,
            'frontend_url': frontend_url,
            'dashboard_url': f"{frontend_url}/registry/dashboard",
            'current_year': timezone.now().year,
            'is_draft': application.status == 'draft',
        }

        # Try to use a dedicated template, fall back to inline HTML
        try:
            html_message = render_to_string('email/professional_application_confirmation.html', context)
        except:
            # Fallback HTML template
            login_credentials = f"""
            <div style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px;">
                <h3 style="color: #856404; margin-top: 0;">🔐 Your Login Credentials</h3>
                <p style="margin: 10px 0;"><strong>Username:</strong> {user.email}</p>
                <p style="margin: 10px 0;"><strong>Password:</strong> {password}</p>
                <p style="color: #856404; margin: 10px 0; font-size: 14px;">
                    ⚠️ Please save these credentials securely.
                </p>
                <p style="color: #d9534f; margin: 10px 0; font-size: 14px; font-weight: bold;">
                    📌 IMPORTANT: You must LOG IN with these credentials before accessing your dashboard to track your application.
                </p>
            </div>
            """ if password else ""

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 20px;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #007bff;">
                        <h1 style="color: #007bff; margin: 0;">PHB National Professional Registry</h1>
                        <p style="color: #6c757d; margin: 5px 0;">Nigerian Healthcare Professional Licensing</p>
                    </div>

                    <h2 style="color: #28a745; margin-top: 30px;">✅ Application Created Successfully</h2>

                    <p>Dear {context['user_name']},</p>

                    <p>Thank you for starting your professional registration application with the PHB National Registry.</p>

                    {'<p style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px;"><strong>📌 Next Step Required:</strong> Please upload all required verification documents and submit your application for review.</p>' if context['is_draft'] else ''}

                    <div style="background: #e7f3ff; padding: 20px; border-radius: 4px; margin: 20px 0;">
                        <h3 style="color: #0056b3; margin-top: 0;">📋 Application Details</h3>
                        <table style="width: 100%; font-size: 14px;">
                            <tr>
                                <td style="padding: 8px 0; color: #6c757d;"><strong>Application Number:</strong></td>
                                <td style="padding: 8px 0;">{context['application_number']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6c757d;"><strong>Reference Number:</strong></td>
                                <td style="padding: 8px 0;">{context['application_reference']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6c757d;"><strong>Professional Type:</strong></td>
                                <td style="padding: 8px 0;">{context['professional_type']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6c757d;"><strong>Home Registration:</strong></td>
                                <td style="padding: 8px 0;">{context['registration_body']} - {context['registration_number']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6c757d;"><strong>Submitted On:</strong></td>
                                <td style="padding: 8px 0;">{context['submitted_date'].strftime('%B %d, %Y at %I:%M %p')}</td>
                            </tr>
                        </table>
                    </div>

                    {login_credentials}

                    <div style="background: #d1ecf1; padding: 20px; border-left: 4px solid #17a2b8; margin: 20px 0; border-radius: 4px;">
                        <h3 style="color: #0c5460; margin-top: 0;">📝 Next Steps</h3>
                        <ol style="color: #0c5460; margin: 10px 0; padding-left: 20px;">
                            {'<li style="margin: 10px 0;">Login to your dashboard using the credentials above</li><li style="margin: 10px 0;">Upload all required verification documents</li><li style="margin: 10px 0;">Review and submit your application</li><li style="margin: 10px 0;">Our team will verify your credentials within 5-10 business days</li>' if context['is_draft'] else '<li style="margin: 10px 0;">Our review team will verify your credentials and documents</li><li style="margin: 10px 0;">You may be contacted if additional documentation is needed</li><li style="margin: 10px 0;">Review typically takes 5-10 business days</li><li style="margin: 10px 0;">You\'ll receive an email notification once review is complete</li>'}
                        </ol>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{context['dashboard_url']}" style="display: inline-block; background: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            Track Application Status
                        </a>
                    </div>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                    <p style="color: #6c757d; font-size: 14px;">
                        <strong>Need Help?</strong><br>
                        If you have questions about your application, please contact our support team or visit your dashboard.
                    </p>

                    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                        This is an automated message from PHB National Professional Registry.<br>
                        © {context['current_year']} PHB. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"✅ Professional Application Submitted - {application.application_reference}",
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Professional application confirmation email sent to {user.email} for {application.application_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send professional application confirmation email: {str(e)}")
        return False


def send_new_application_alert_to_admins(application):
    """
    Send alert to admin staff when a new professional application is submitted.

    Args:
        application: ProfessionalApplication object

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get all staff users who should receive notifications
        from django.contrib.auth import get_user_model
        User = get_user_model()

        admin_emails = list(User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True))

        if not admin_emails:
            logger.warning("No admin users found to send new application notification")
            return False

        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')
        admin_url = f"{frontend_url}/admin/registry/applications/{application.id}"

        context = {
            'applicant_name': f"{application.first_name} {application.last_name}",
            'professional_type': application.get_professional_type_display(),
            'application_number': application.application_reference,  # Use application_reference
            'application_reference': application.application_reference,
            'submitted_date': application.submitted_date,
            'registration_body': application.home_registration_body,
            'registration_number': application.home_registration_number,
            'email': application.email,
            'phone': application.phone,
            'specialization': application.specialization,
            'years_experience': application.years_of_experience,
            'admin_url': admin_url,
            'current_year': timezone.now().year,
        }

        # Try to use a dedicated template, fall back to inline HTML
        try:
            html_message = render_to_string('email/admin_new_application_alert.html', context)
        except:
            # Fallback HTML template
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 20px;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background: #007bff; color: white; padding: 20px; border-radius: 4px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🆕 New Professional Application</h1>
                        <p style="margin: 10px 0 0 0; font-size: 14px;">PHB National Registry - Admin Alert</p>
                    </div>

                    <div style="background: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; border-radius: 4px;">
                        <p style="margin: 0; color: #856404;">
                            <strong>⚠️ Action Required:</strong> A new professional registration application requires review.
                        </p>
                    </div>

                    <h2 style="color: #0056b3; margin-top: 20px;">Applicant Details</h2>

                    <table style="width: 100%; font-size: 14px; margin: 20px 0;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Name:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['applicant_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Professional Type:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['professional_type']}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Specialization:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['specialization']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Experience:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['years_experience']} years</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Home Registration:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['registration_body']} - {context['registration_number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Email:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['email']}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Phone:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['phone']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Application Number:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>{context['application_number']}</strong></td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Submitted:</strong></td>
                            <td style="padding: 12px; border: 1px solid #dee2e6;">{context['submitted_date'].strftime('%B %d, %Y at %I:%M %p')}</td>
                        </tr>
                    </table>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{context['admin_url']}" style="display: inline-block; background: #28a745; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            Review Application →
                        </a>
                    </div>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                    <p style="color: #6c757d; font-size: 12px; margin: 0;">
                        This is an automated admin notification from PHB National Professional Registry.<br>
                        © {context['current_year']} PHB. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"🆕 New Professional Application: {application.get_professional_type_display()} - {application.application_reference}",
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"New application alert sent to {len(admin_emails)} admins for {application.application_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send new application alert to admins: {str(e)}")
        return False


def send_professional_application_approved_email(user, application, license_number):
    """
    Send email when a professional application is approved and license is issued.

    Args:
        user: User object
        application: ProfessionalApplication object
        license_number: The issued PHB license number

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')

        context = {
            'user_name': f"{user.first_name} {user.last_name}",
            'professional_type': application.get_professional_type_display(),
            'license_number': license_number,
            'application_number': application.application_reference,  # Use application_reference
            'approved_date': application.reviewed_date or timezone.now(),
            'specialization': application.specialization,
            'registration_body': application.home_registration_body,
            'registration_number': application.home_registration_number,
            'frontend_url': frontend_url,
            'dashboard_url': f"{frontend_url}/professional/dashboard",
            'certificate_url': f"{frontend_url}/professional/certificate",
            'current_year': timezone.now().year,
        }

        # Try to use a dedicated template, fall back to inline HTML
        try:
            html_message = render_to_string('email/professional_application_approved.html', context)
        except:
            # Fallback HTML template
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 20px;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 4px; text-align: center;">
                        <h1 style="margin: 0; font-size: 32px;">🎉 Congratulations!</h1>
                        <p style="margin: 15px 0 0 0; font-size: 18px;">Your Professional License Has Been Approved</p>
                    </div>

                    <p style="font-size: 16px; margin: 30px 0;">Dear {context['user_name']},</p>

                    <p style="font-size: 16px; line-height: 1.6;">
                        We are pleased to inform you that your application for registration with the PHB National Professional Registry has been <strong>APPROVED</strong>!
                    </p>

                    <div style="background: #d4edda; padding: 25px; border-left: 4px solid #28a745; margin: 30px 0; border-radius: 4px; text-align: center;">
                        <h2 style="color: #155724; margin: 0 0 15px 0;">Your PHB License Number</h2>
                        <div style="background: white; padding: 20px; border-radius: 4px; font-size: 28px; font-weight: bold; color: #28a745; letter-spacing: 2px; font-family: 'Courier New', monospace;">
                            {context['license_number']}
                        </div>
                        <p style="color: #155724; margin: 15px 0 0 0; font-size: 14px;">
                            Please keep this number for your records
                        </p>
                    </div>

                    <h3 style="color: #0056b3; margin: 30px 0 15px 0;">License Details</h3>
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="padding: 10px 0; color: #6c757d;"><strong>Professional Type:</strong></td>
                            <td style="padding: 10px 0;">{context['professional_type']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #6c757d;"><strong>Specialization:</strong></td>
                            <td style="padding: 10px 0;">{context['specialization']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #6c757d;"><strong>Application Number:</strong></td>
                            <td style="padding: 10px 0;">{context['application_number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #6c757d;"><strong>Approval Date:</strong></td>
                            <td style="padding: 10px 0;">{context['approved_date'].strftime('%B %d, %Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #6c757d;"><strong>Home Registration:</strong></td>
                            <td style="padding: 10px 0;">{context['registration_body']} - {context['registration_number']}</td>
                        </tr>
                    </table>

                    <div style="background: #cfe2ff; padding: 20px; border-left: 4px solid #0d6efd; margin: 30px 0; border-radius: 4px;">
                        <h3 style="color: #084298; margin-top: 0;">✅ What's Next?</h3>
                        <ul style="color: #084298; margin: 10px 0; padding-left: 20px; line-height: 1.8;">
                            <li>Access your professional dashboard</li>
                            <li>Download your digital certificate</li>
                            <li>Update your practice information</li>
                            <li>Start accepting patient appointments</li>
                            <li>Access prescription triage system</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{context['dashboard_url']}" style="display: inline-block; background: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 5px;">
                            Access Dashboard →
                        </a>
                        <a href="{context['certificate_url']}" style="display: inline-block; background: #28a745; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 5px;">
                            Download Certificate →
                        </a>
                    </div>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                    <p style="color: #6c757d; font-size: 14px;">
                        <strong>Important Notice:</strong><br>
                        Your license is now active and searchable in the public registry. Patients and healthcare facilities can verify your credentials using your license number.
                    </p>

                    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                        This is an automated message from PHB National Professional Registry.<br>
                        © {context['current_year']} PHB. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"🎉 Your PHB Professional License Has Been Approved - {license_number}",
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Professional application approval email sent to {user.email} with license {license_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send professional application approval email: {str(e)}")
        return False


def send_professional_application_rejected_email(user, application, reason):
    """
    Send email when a professional application is rejected.

    Args:
        user: User object
        application: ProfessionalApplication object
        reason: Rejection reason

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')

        context = {
            'user_name': f"{user.first_name} {user.last_name}",
            'professional_type': application.get_professional_type_display(),
            'application_number': application.application_reference,  # Use application_reference
            'rejection_reason': reason,
            'reviewed_date': application.reviewed_date or timezone.now(),
            'frontend_url': frontend_url,
            'reapply_url': f"{frontend_url}/registry/apply",
            'support_url': f"{frontend_url}/support",
            'current_year': timezone.now().year,
        }

        # Try to use a dedicated template, fall back to inline HTML
        try:
            html_message = render_to_string('email/professional_application_rejected.html', context)
        except:
            # Fallback HTML template
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 20px;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background: #dc3545; color: white; padding: 20px; border-radius: 4px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Application Status Update</h1>
                        <p style="margin: 10px 0 0 0; font-size: 14px;">PHB National Professional Registry</p>
                    </div>

                    <p style="font-size: 16px; margin: 30px 0;">Dear {context['user_name']},</p>

                    <p style="font-size: 16px; line-height: 1.6;">
                        Thank you for your interest in registering with the PHB National Professional Registry. After careful review, we regret to inform you that your application <strong>cannot be approved</strong> at this time.
                    </p>

                    <div style="background: #f8d7da; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 4px;">
                        <h3 style="color: #721c24; margin-top: 0;">Reason for Rejection</h3>
                        <p style="color: #721c24; margin: 0; line-height: 1.6;">
                            {context['rejection_reason']}
                        </p>
                    </div>

                    <div style="background: #d1ecf1; padding: 20px; border-left: 4px solid #17a2b8; margin: 20px 0; border-radius: 4px;">
                        <h3 style="color: #0c5460; margin-top: 0;">What You Can Do</h3>
                        <ul style="color: #0c5460; margin: 10px 0; padding-left: 20px; line-height: 1.8;">
                            <li>Review the rejection reason carefully</li>
                            <li>Address the issues mentioned</li>
                            <li>Gather any missing or corrected documentation</li>
                            <li>Contact our support team if you need clarification</li>
                            <li>Submit a new application when ready</li>
                        </ul>
                    </div>

                    <table style="width: 100%; font-size: 14px; margin: 20px 0;">
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d;"><strong>Application Number:</strong></td>
                            <td style="padding: 8px 0;">{context['application_number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d;"><strong>Professional Type:</strong></td>
                            <td style="padding: 8px 0;">{context['professional_type']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d;"><strong>Review Date:</strong></td>
                            <td style="padding: 8px 0;">{context['reviewed_date'].strftime('%B %d, %Y')}</td>
                        </tr>
                    </table>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{context['support_url']}" style="display: inline-block; background: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 5px;">
                            Contact Support
                        </a>
                        <a href="{context['reapply_url']}" style="display: inline-block; background: #28a745; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 5px;">
                            Submit New Application
                        </a>
                    </div>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                    <p style="color: #6c757d; font-size: 14px;">
                        We appreciate your interest in the PHB National Professional Registry. If you have questions about this decision, please don't hesitate to contact our support team.
                    </p>

                    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                        This is an automated message from PHB National Professional Registry.<br>
                        © {context['current_year']} PHB. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"Application Status Update - {application.application_reference}",
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Professional application rejection email sent to {user.email} for {application.application_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send professional application rejection email: {str(e)}")
        return False


def send_document_rejection_email(application, document):
    """
    Send email notification when a document is rejected.
    Notifies applicant that specific document needs resubmission.

    Args:
        application: ProfessionalApplication instance
        document: ApplicationDocument instance that was rejected

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        user = application.user
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        # Format deadline
        deadline_str = document.resubmission_deadline.strftime('%B %d, %Y at %I:%M %p') if document.resubmission_deadline else 'Not set'

        context = {
            'applicant_name': application.get_full_name(),
            'application_reference': application.application_reference,
            'document_type_display': document.get_document_type_display(),
            'rejection_reason': document.verification_notes,
            'rejection_count': document.rejection_count,
            'max_attempts': document.max_rejection_attempts,
            'attempts_remaining': document.attempts_remaining,
            'resubmission_deadline': deadline_str,
            'application_url': f'{frontend_url}/registry/applications/{application.id}',
            'support_email': 'support@phb.ng',
            'current_year': timezone.now().year,
        }

        # HTML email template
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa;">
            <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <!-- Header with alert icon -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: #dc3545; width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; color: white; font-size: 30px;">
                        ⚠️
                    </div>
                    <h2 style="color: #dc3545; margin: 0;">Document Rejected - Action Required</h2>
                </div>

                <p>Dear {context['applicant_name']},</p>

                <p>A document in your professional registration application <strong>{context['application_reference']}</strong> has been rejected and requires your attention.</p>

                <!-- Document Details -->
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #856404;">Rejected Document:</p>
                    <p style="margin: 0; font-size: 16px;"><strong>{context['document_type_display']}</strong></p>
                </div>

                <!-- Rejection Reason -->
                <div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #721c24;">Reason for Rejection:</p>
                    <p style="margin: 0; color: #721c24;">{context['rejection_reason']}</p>
                </div>

                <!-- Attempt Information -->
                <div style="background: #d1ecf1; border-left: 4px solid #0c5460; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 5px 0; color: #0c5460;"><strong>Attempts Remaining:</strong></td>
                            <td style="padding: 5px 0; text-align: right;"><strong>{context['attempts_remaining']} of {context['max_attempts']}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; color: #0c5460;"><strong>Resubmission Deadline:</strong></td>
                            <td style="padding: 5px 0; text-align: right;"><strong>{context['resubmission_deadline']}</strong></td>
                        </tr>
                    </table>
                </div>

                <!-- Action Required -->
                <div style="background: #e2e3e5; padding: 20px; border-radius: 4px; margin: 25px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #383d41;">What You Need to Do:</h3>
                    <ol style="margin: 0; padding-left: 20px; color: #383d41;">
                        <li style="margin-bottom: 10px;">Review the rejection reason carefully</li>
                        <li style="margin-bottom: 10px;">Prepare a corrected version of the document</li>
                        <li style="margin-bottom: 10px;">Log in to your application and upload the new document</li>
                        <li>Submit before the deadline to avoid application rejection</li>
                    </ol>
                </div>

                <!-- Warning if low attempts -->
                {f'<div style="background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0;"><p style="margin: 0; color: #856404;"><strong>⚠️ Important:</strong> You have only {context["attempts_remaining"]} attempt(s) remaining. Please ensure the document meets all requirements before resubmitting.</p></div>' if context['attempts_remaining'] <= 1 else ''}

                <!-- CTA Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{context['application_url']}" style="display: inline-block; background: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                        Upload Corrected Document
                    </a>
                </div>

                <!-- Support Information -->
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                <p style="color: #6c757d; font-size: 14px;">
                    <strong>Need Help?</strong><br>
                    If you have questions about why your document was rejected or need assistance, please contact our support team at
                    <a href="mailto:{context['support_email']}" style="color: #007bff;">{context['support_email']}</a>
                </p>

                <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                    This is an automated notification from PHB National Professional Registry.<br>
                    Application Reference: {context['application_reference']}<br>
                    © {context['current_year']} PHB. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"Document Rejected - Action Required: {application.application_reference}",
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Document rejection email sent to {user.email} for document {document.document_type} in application {application.application_reference}")
        return True

    except Exception as e:
        logger.error(f"Failed to send document rejection email: {str(e)}")
        return False


def send_application_approved_email(application, registry_entry):
    """
    Send email notification when a professional application is approved.

    Args:
        application: ProfessionalApplication instance
        registry_entry: PHBProfessionalRegistry instance
    """
    subject = f"Application Approved - PHB Professional Registry"

    # Build context with approval details
    context = {
        'applicant_name': application.get_full_name(),
        'professional_type': application.get_professional_type_display(),
        'specialization': application.get_specialization_display() if hasattr(application, 'get_specialization_display') else application.specialization or '',
        'license_number': registry_entry.phb_license_number,
        'issue_date': registry_entry.license_issue_date.strftime('%B %d, %Y'),
        'expiry_date': registry_entry.license_expiry_date.strftime('%B %d, %Y') if registry_entry.license_expiry_date else 'N/A',
        'application_reference': application.application_reference,
        'registry_url': f"{settings.FRONTEND_URL}/registry/professionals/{registry_entry.id}",
        'dashboard_url': f"{settings.FRONTEND_URL}/professional/dashboard",
    }

    # Plain text message
    plain_message = f"""
Congratulations {context['applicant_name']}!

Your application for PHB Professional Registry has been APPROVED!

LICENSE DETAILS:
License Number: {context['license_number']}
Professional Type: {context['professional_type']}
Specialization: {context['specialization']}
Issue Date: {context['issue_date']}
Expiry Date: {context['expiry_date']}

Your profile is now live in the PHB National Professional Registry and can be searched by patients and healthcare facilities.

NEXT STEPS:
1. Log in to your professional dashboard
2. Complete your public profile and biography
3. Update your practice information and services
4. Start accepting patient consultations

Access your dashboard: {context['dashboard_url']}
View your public profile: {context['registry_url']}

Congratulations on joining the PHB Professional Registry!

Best regards,
PHB Registration Team
"""

    # HTML email template - Minimal, professional design (AWS/Stripe/NHS style)
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333333; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; }}

        /* Simple Header */
        .header {{
            padding: 32px 40px 24px;
            border-bottom: 2px solid #000000;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #000000;
            margin: 0;
        }}
        .subtitle {{
            font-size: 14px;
            color: #666666;
            margin: 4px 0 0 0;
        }}

        /* Content */
        .content {{ padding: 40px; }}
        .title {{
            font-size: 20px;
            font-weight: 600;
            color: #000000;
            margin: 0 0 24px 0;
        }}
        .text {{
            font-size: 15px;
            color: #333333;
            margin: 0 0 16px 0;
            line-height: 1.5;
        }}

        /* License Information Box */
        .info-box {{
            background: #f9f9f9;
            border: 1px solid #e5e5e5;
            padding: 24px;
            margin: 24px 0;
        }}
        .info-heading {{
            font-size: 12px;
            font-weight: 600;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0 0 16px 0;
        }}
        .license-number {{
            font-size: 18px;
            font-weight: 700;
            color: #000000;
            margin: 0 0 20px 0;
            font-family: 'Courier New', monospace;
        }}

        /* Details Table */
        .details-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .details-table td {{
            padding: 8px 0;
            font-size: 14px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .details-table td:first-child {{
            color: #666666;
            width: 40%;
        }}
        .details-table td:last-child {{
            color: #000000;
            font-weight: 500;
        }}
        .details-table tr:last-child td {{
            border-bottom: none;
        }}

        /* Next Steps */
        .steps-section {{
            margin: 32px 0;
        }}
        .steps-heading {{
            font-size: 16px;
            font-weight: 600;
            color: #000000;
            margin: 0 0 16px 0;
        }}
        .step {{
            margin-bottom: 16px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .step strong {{
            color: #000000;
        }}

        /* Button */
        .button {{
            display: inline-block;
            background: #000000;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            margin: 24px 0 8px 0;
        }}
        .button-link {{
            display: inline-block;
            color: #000000;
            text-decoration: underline;
            font-size: 14px;
            margin: 8px 16px 0 0;
        }}

        /* Footer */
        .footer {{
            padding: 32px 40px;
            background: #f9f9f9;
            border-top: 1px solid #e5e5e5;
            font-size: 12px;
            color: #666666;
            line-height: 1.6;
        }}
        .footer p {{
            margin: 0 0 8px 0;
        }}
        .footer a {{
            color: #000000;
            text-decoration: none;
        }}
        .footer-divider {{
            height: 1px;
            background: #e5e5e5;
            margin: 16px 0;
        }}

        @media only screen and (max-width: 600px) {{
            .header, .content, .footer {{ padding: 24px 20px; }}
            .button {{ display: block; text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">PHB</div>
            <div class="subtitle">Public Health Bureau - Professional Registry</div>
        </div>

        <!-- Content -->
        <div class="content">
            <h1 class="title">Application Approved</h1>

            <p class="text">
                Dear {context['applicant_name']},
            </p>

            <p class="text">
                Your application to the PHB Professional Registry has been approved. Your professional license has been issued and is detailed below.
            </p>

            <!-- License Information -->
            <div class="info-box">
                <div class="info-heading">Professional License</div>
                <div class="license-number">{context['license_number']}</div>

                <table class="details-table">
                    <tr>
                        <td>License Holder</td>
                        <td>{context['applicant_name']}</td>
                    </tr>
                    <tr>
                        <td>Professional Type</td>
                        <td>{context['professional_type']}</td>
                    </tr>
                    <tr>
                        <td>Specialization</td>
                        <td>{context['specialization']}</td>
                    </tr>
                    <tr>
                        <td>Issue Date</td>
                        <td>{context['issue_date']}</td>
                    </tr>
                    <tr>
                        <td>Valid Until</td>
                        <td>{context['expiry_date']}</td>
                    </tr>
                </table>
            </div>

            <p class="text">
                Your profile is now live in the national registry and searchable by patients and healthcare facilities.
            </p>

            <!-- Next Steps -->
            <div class="steps-section">
                <div class="steps-heading">Next Steps</div>

                <div class="step">
                    <strong>1. Complete your profile:</strong> Add your biography, services, and practice information to help patients find you.
                </div>

                <div class="step">
                    <strong>2. Verify your details:</strong> Ensure your contact information and specializations are accurate and current.
                </div>

                <div class="step">
                    <strong>3. Access your dashboard:</strong> Log in to manage your profile, view consultation requests, and update your information.
                </div>
            </div>

            <!-- Actions -->
            <a href="{context['dashboard_url']}" class="button">Access Dashboard</a>
            <a href="{context['registry_url']}" class="button-link">View Public Profile</a>

            <p class="text" style="margin-top: 32px; font-size: 13px; color: #666666;">
                If you have questions, contact our registry support team at <a href="mailto:registry@phb.ng" style="color: #000000;">registry@phb.ng</a>
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>Public Health Bureau</strong></p>
            <p>Professional Registry Division</p>
            <p>Federal Capital Territory, Abuja, Nigeria</p>

            <div class="footer-divider"></div>

            <p>
                Application Reference: {context['application_reference']}<br>
                Email: <a href="mailto:registry@phb.ng">registry@phb.ng</a> |
                Phone: +234 (0) 800 CALL PHB
            </p>

            <p style="margin-top: 16px;">
                <a href="{settings.FRONTEND_URL}/privacy">Privacy Policy</a> |
                <a href="{settings.FRONTEND_URL}/terms">Terms of Service</a>
            </p>

            <p style="margin-top: 16px; color: #999999;">
                © 2025 Public Health Bureau. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Approval email sent to {application.email} for application {application.application_reference}")
        return True
    except Exception as e:
        logger.error(f"Failed to send approval email: {str(e)}")
        return False



def send_practice_page_approved_email(practice_page):
    """
    Send email notification when a professional practice page is approved.
    
    Args:
        practice_page: ProfessionalPracticePage instance
    """
    subject = f"Practice Page Approved - {practice_page.practice_name}"
    
    # Build context with approval details
    context = {
        'owner_name': practice_page.owner.get_full_name(),
        'practice_name': practice_page.practice_name,
        'service_type': practice_page.get_service_type_display(),
        'license_number': practice_page.linked_registry_entry.phb_license_number,
        'professional_type': practice_page.linked_registry_entry.get_professional_type_display(),
        'verification_date': practice_page.verified_date.strftime('%B %d, %Y') if practice_page.verified_date else 'Today',
        'page_url': f"{settings.FRONTEND_URL}/pages/{practice_page.slug}",
        'dashboard_url': f"{settings.FRONTEND_URL}/professional/my-practice",
        'city': practice_page.city,
        'state': practice_page.state,
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL,
        'phb_phone': settings.PHB_PHONE,
    }
    
    # Render HTML from template
    html_message = render_to_string('email/practice_page_approved.html', context)
    
    # Plain text message
    plain_message = f"""
Congratulations {context['owner_name']}!

Your practice page "{context['practice_name']}" has been APPROVED!

PAGE DETAILS:
Practice Name: {context['practice_name']}
Service Type: {context['service_type']}
Location: {context['city']}, {context['state']}
PHB License: {context['license_number']}
Professional Type: {context['professional_type']}
Approved Date: {context['verification_date']}

Your practice page is now live and searchable by patients looking for healthcare services in your area.

NEXT STEPS:
1. View your public practice page
2. Share your page link with patients
3. Keep your information up-to-date
4. Respond to patient inquiries promptly

Your public page: {context['page_url']}
Manage your page: {context['dashboard_url']}

Congratulations on your approved practice page!

Best regards,
PHB Registry Team
"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[practice_page.owner.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Practice page approval email sent to {practice_page.owner.email} for page '{practice_page.practice_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send practice page approval email: {str(e)}")
        return False


def send_practice_page_flagged_email(practice_page, flag_reason, has_penalty=False, penalty_amount=None):
    """
    Send email notification when a professional practice page is flagged for review.

    Args:
        practice_page: ProfessionalPracticePage instance
        flag_reason: Reason for flagging the page
        has_penalty: Whether a penalty fee applies
        penalty_amount: Penalty amount if applicable
    """
    subject = f"Practice Page Flagged for Review - {practice_page.practice_name}"

    # Build context with flagging details
    context = {
        'owner_name': practice_page.owner.get_full_name(),
        'practice_name': practice_page.practice_name,
        'flag_reason': flag_reason,
        'flagged_date': practice_page.verified_date.strftime('%B %d, %Y') if practice_page.verified_date else 'Today',
        'has_penalty': has_penalty,
        'penalty_amount': penalty_amount,
        'registry_email': settings.REGISTRY_EMAIL,
        'phb_phone': settings.PHB_PHONE,
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL,
    }

    # Render HTML from template
    html_message = render_to_string('email/practice_page_flagged.html', context)

    # Plain text message
    plain_message = f"""
IMPORTANT: Your Practice Page Has Been Flagged for Review

Dear {context['owner_name']},

Your professional practice page has been flagged for review by our registry team and has been temporarily removed from public view while we investigate.

FLAGGED PRACTICE PAGE:
Practice Name: {context['practice_name']}
Date Flagged: {context['flagged_date']}
Current Status: Under Review

REASON FOR FLAGGING:
{flag_reason}

Your practice page has been removed from the public directory and will not be visible to patients until the issue is resolved and your page is reactivated.

REQUIRED ACTIONS:
1. Review the reason: Carefully read the flagging reason above and understand what needs to be corrected.
2. Make necessary corrections: Update your practice page information to address the concerns raised.
3. Contact our team: Reach out to {context['registry_email']} to discuss the issue and request reactivation.
4. Pay any applicable fees: If a penalty fee applies, you will be notified separately with payment details.
"""

    if has_penalty and penalty_amount:
        plain_message += f"""
PENALTY FEE NOTICE:
A penalty fee of ₦{penalty_amount} applies to this violation. Payment instructions will be sent separately. Your page cannot be reactivated until the fee is paid and the issue is resolved.
"""

    plain_message += f"""
WHAT HAPPENS NEXT:
1. Our registry team will investigate the reported issue
2. You may be contacted for additional information
3. Once resolved, your page can be reactivated
4. If unresolved within 30 days, your page may be permanently suspended

If you believe this flagging was made in error, please contact our registry team immediately at {context['registry_email']} or call {context['phb_phone']}.

Best regards,
PHB Registry Team
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[practice_page.owner.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Practice page flagged email sent to {practice_page.owner.email} for page '{practice_page.practice_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send practice page flagged email: {str(e)}")
        return False


def send_practice_page_suspended_email(practice_page, suspension_reason, has_penalty=False, penalty_amount=None):
    """
    Send email notification when a professional practice page is suspended.

    Args:
        practice_page: ProfessionalPracticePage instance
        suspension_reason: Reason for suspension
        has_penalty: Whether a penalty fee applies
        penalty_amount: Penalty amount if applicable
    """
    subject = f"Practice Page Suspended - {practice_page.practice_name}"

    # Build context with suspension details
    context = {
        'owner_name': practice_page.owner.get_full_name(),
        'practice_name': practice_page.practice_name,
        'suspension_reason': suspension_reason,
        'suspended_date': practice_page.verified_date.strftime('%B %d, %Y') if practice_page.verified_date else 'Today',
        'has_penalty': has_penalty,
        'penalty_amount': penalty_amount,
        'registry_email': settings.REGISTRY_EMAIL,
        'phb_phone': settings.PHB_PHONE,
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL,
    }

    # Render HTML from template
    html_message = render_to_string('email/practice_page_suspended.html', context)

    # Plain text message
    plain_message = f"""
URGENT: Your Practice Page Has Been Suspended

Dear {context['owner_name']},

Your professional practice page has been SUSPENDED by our registry team and has been removed from public view.

SUSPENDED PRACTICE PAGE:
Practice Name: {context['practice_name']}
Date Suspended: {context['suspended_date']}
Current Status: Suspended

REASON FOR SUSPENSION:
{suspension_reason}

Your practice page has been permanently removed from the public directory and will not be visible to patients. This is a serious action taken due to violations of PHB registry policies.

REQUIRED ACTIONS:
1. Review the suspension reason carefully
2. Address all violations mentioned above
3. Contact our registry team at {context['registry_email']} to discuss reinstatement
4. Pay any applicable penalty fees
5. Provide evidence of corrective actions taken
"""

    if has_penalty and penalty_amount:
        plain_message += f"""
PENALTY FEE NOTICE:
A penalty fee of ₦{penalty_amount} applies to this violation. Payment instructions will be sent separately. Your page cannot be reinstated until the fee is paid and the issue is resolved.
"""

    plain_message += f"""
REINSTATEMENT PROCESS:
Your page will remain suspended until:
1. You contact our team and discuss the suspension
2. All violations are addressed
3. Any penalty fees are paid
4. Your page content is updated to comply with policies
5. Our team reviews and approves reinstatement

WARNING: Repeated violations may result in permanent suspension and removal from the PHB professional registry.

If you believe this suspension was made in error, please contact our registry team immediately at {context['registry_email']} or call {context['phb_phone']}.

Best regards,
PHB Registry Team
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[practice_page.owner.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Practice page suspended email sent to {practice_page.owner.email} for page '{practice_page.practice_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send practice page suspended email: {str(e)}")
        return False


def send_practice_page_reactivated_email(practice_page, reactivation_notes=None):
    """
    Send email notification when a professional practice page is reactivated after being flagged/suspended.

    Args:
        practice_page: ProfessionalPracticePage instance
        reactivation_notes: Optional notes about the reactivation
    """
    subject = f"Practice Page Reactivated - {practice_page.practice_name}"

    # Build context with reactivation details
    context = {
        'owner_name': practice_page.owner.get_full_name(),
        'practice_name': practice_page.practice_name,
        'reactivation_notes': reactivation_notes,
        'reactivated_date': practice_page.verified_date.strftime('%B %d, %Y') if practice_page.verified_date else 'Today',
        'practice_page_url': f"{settings.FRONTEND_URL}/practice-pages/{practice_page.slug}",
        'registry_email': settings.REGISTRY_EMAIL,
        'phb_phone': settings.PHB_PHONE,
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL,
    }

    # Render HTML from template
    html_message = render_to_string('email/practice_page_reactivated.html', context)

    # Plain text message
    plain_message = f"""
Your Practice Page Has Been Reactivated

Dear {context['owner_name']},

Good news! Your professional practice page has been REACTIVATED by our registry team and is now visible to the public again.

REACTIVATED PRACTICE PAGE:
Practice Name: {context['practice_name']}
Date Reactivated: {context['reactivated_date']}
Current Status: Verified & Active
"""

    if reactivation_notes:
        plain_message += f"""
REACTIVATION NOTES:
{reactivation_notes}
"""

    plain_message += f"""
Your practice page is now fully active in the PHB professional registry and will appear in search results. Patients can find and contact you through the directory.

IMPORTANT: MAINTAINING COMPLIANCE
Please ensure you:
✓ Keep all information accurate and up-to-date
✓ Follow PHB registry policies and professional standards
✓ Maintain professional conduct in all content and interactions
✓ Respond promptly to patient inquiries
✓ Report any significant changes to your practice

⚠️ IMPORTANT WARNING:
This is your opportunity to maintain good standing in the PHB registry. Your page was previously flagged or suspended due to policy violations. Please ensure you understand and comply with all PHB registry policies going forward.

Repeated violations may result in permanent suspension and removal from the professional registry, which could affect your ability to practice and your professional reputation.

View your practice page: {context['practice_page_url']}

If you have any questions about maintaining compliance or need clarification on any policies, please contact our registry team at {context['registry_email']} or call {context['phb_phone']}.

Best regards,
PHB Registry Team
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[practice_page.owner.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Practice page reactivated email sent to {practice_page.owner.email} for page '{practice_page.practice_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send practice page reactivated email: {str(e)}")
        return False

def send_controlled_substance_alert(pharmacy_email, pharmacy_name, patient_name, 
                                    medication_name, nafdac_schedule, prescription_id):
    """
    Send URGENT email alert for controlled substance prescriptions.
    Only sent for NAFDAC Schedule 2/3 drugs (NOT routine prescriptions).
    
    This prevents email overload - only critical alerts are sent, not individual
    emails for every prescription. Pharmacy dashboard shows all prescriptions.
    
    Args:
        pharmacy_email (str): Pharmacy email address
        pharmacy_name (str): Pharmacy name
        patient_name (str): Patient full name  
        medication_name (str): Name of controlled substance
        nafdac_schedule (str): '2', '3', or 'Manual'
        prescription_id (str): PHB-RX-XXXXXXXX format
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        context = {
            'pharmacy_name': pharmacy_name,
            'patient_name': patient_name,
            'medication_name': medication_name,
            'nafdac_schedule': nafdac_schedule,
            'prescription_id': prescription_id,
            'alert_date': timezone.now().strftime('%d %B %Y at %H:%M'),
            'dashboard_url': f"{os.environ.get('NEXTJS_URL', 'http://localhost:3001')}/professional/pharmacy/queue",
        }
        
        # Try to render from template, fall back to inline HTML
        try:
            html_message = render_to_string('email/controlled_substance_alert.html', context)
        except Exception:
            # Fallback inline HTML template
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f5f5f5; padding: 30px; }}
                    .alert-box {{ background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; }}
                    .info-box {{ background-color: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                    .cta-button {{ display: inline-block; background-color: #d32f2f; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                    .footer {{ background-color: #5e35b1; color: white; padding: 20px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 28px;">🔴 URGENT: Controlled Substance</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">NAFDAC Schedule {nafdac_schedule} - Action Required</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #d32f2f;">Hello {pharmacy_name},</h2>
                        
                        <p style="font-size: 16px;">
                            A controlled substance prescription has been issued and requires your immediate attention:
                        </p>
                        
                        <div class="info-box">
                            <h3 style="color: #1976d2; margin-top: 0;">Prescription Details</h3>
                            <p style="margin: 5px 0;"><strong>Prescription ID:</strong> <span style="font-family: monospace; font-size: 16px;">{prescription_id}</span></p>
                            <p style="margin: 5px 0;"><strong>Patient:</strong> {patient_name}</p>
                            <p style="margin: 5px 0;"><strong>Medication:</strong> <span style="color: #d32f2f; font-weight: bold;">{medication_name}</span></p>
                            <p style="margin: 5px 0;"><strong>NAFDAC Schedule:</strong> <span style="background-color: #d32f2f; color: white; padding: 2px 8px; border-radius: 3px;">{nafdac_schedule}</span></p>
                            <p style="margin: 5px 0;"><strong>Alert Date:</strong> {context['alert_date']}</p>
                        </div>
                        
                        <div class="alert-box">
                            <h4 style="color: #f57c00; margin-top: 0;">⚠️ Important: Enhanced Verification Required</h4>
                            <p style="margin: 10px 0;">This controlled substance requires additional verification steps:</p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>Patient ID Verification:</strong> Verify government-issued ID (NIN, Driver License, or Passport)</li>
                                <li><strong>Prescription Authentication:</strong> Scan and verify electronic prescription token</li>
                                <li><strong>Controlled Drugs Register:</strong> Record in controlled substances logbook</li>
                                <li><strong>Pharmacist Authorization:</strong> Authorized pharmacist must dispense</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 16px;">
                            <strong>Next Steps:</strong>
                        </p>
                        <ol style="line-height: 1.8;">
                            <li>Patient will contact you to arrange collection</li>
                            <li>Verify their identity with government-issued ID</li>
                            <li>Scan the electronic prescription token they present</li>
                            <li>Verify prescription authenticity in your dashboard</li>
                            <li>Complete controlled drugs register entry</li>
                            <li>Dispense medication and log in PHB system</li>
                        </ol>
                        
                        <div style="text-align: center;">
                            <a href="{context['dashboard_url']}" class="cta-button">
                                View in Pharmacy Dashboard
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px; font-size: 14px; color: #666;">
                            <strong>Note:</strong> This prescription will also appear in your Pharmacy Dashboard queue with a "Controlled" priority flag.
                            Daily digest emails will include a summary count of controlled substances.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p style="margin: 0; font-size: 14px;">
                            PHB Electronic Prescription Service - Controlled Substance Alert<br>
                            This is an automated security notification
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Plain text version
        plain_message = f"""
🔴 URGENT: Controlled Substance Prescription - Action Required

Hello {pharmacy_name},

A NAFDAC Schedule {nafdac_schedule} controlled substance prescription has been issued and requires your immediate attention.

PRESCRIPTION DETAILS:
- Prescription ID: {prescription_id}
- Patient: {patient_name}
- Medication: {medication_name}
- NAFDAC Schedule: {nafdac_schedule}
- Alert Date: {context['alert_date']}

⚠️ ENHANCED VERIFICATION REQUIRED:
This controlled substance requires additional verification steps:
✓ Patient ID Verification (NIN, Driver License, or Passport)
✓ Prescription Authentication (scan electronic token)
✓ Controlled Drugs Register entry
✓ Authorized pharmacist must dispense

NEXT STEPS:
1. Patient will contact you to arrange collection
2. Verify their identity with government-issued ID
3. Scan the electronic prescription token
4. Verify prescription authenticity in your dashboard
5. Complete controlled drugs register entry
6. Dispense medication and log in PHB system

View in Dashboard: {context['dashboard_url']}

Note: This prescription also appears in your Pharmacy Dashboard queue with "Controlled" priority.

PHB Electronic Prescription Service
This is an automated security notification
        """
        
        # Send email
        send_mail(
            subject=f'🔴 URGENT: Controlled Substance Prescription - {medication_name}',
            message=plain_message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pharmacy_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(
            f"Controlled substance alert sent to {pharmacy_name} ({pharmacy_email}) "
            f"for {medication_name} (Schedule {nafdac_schedule})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send controlled substance alert: {str(e)}")
        return False


def generate_hospital_certificate_pdf(hospital):
    """
    Generate a PDF certificate for hospital approval with elegant professional design

    Args:
        hospital: Hospital model instance

    Returns:
        BytesIO: PDF file in memory, or None if generation fails
    """
    try:
        # Load signature image from database if available
        from api.models import AdminSignature
        signature_base64 = ''

        try:
            active_signature = AdminSignature.objects.filter(is_active=True).first()
            if active_signature and active_signature.signature_image:
                signature_base64 = base64.b64encode(active_signature.signature_image.read()).decode('utf-8')
                logger.info(f"✍️ Admin signature loaded for certificate: {active_signature.name}")
            else:
                logger.warning(f"⚠️ No active signature found in database")
        except Exception as sig_error:
            logger.error(f"❌ Error loading signature: {str(sig_error)}")

        # Create elegant certificate HTML template with Google Fonts for beautiful cursive
        certificate_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHB Hospital Certificate of Approval</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&family=Montserrat:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4 landscape;
            margin: 0;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Montserrat', Georgia, sans-serif;
            background-color: #fdfaf7;
        }}
        .certificate-container {{
            width: 297mm;
            height: 210mm;
            background-color: #fdfaf7;
            border: 10px solid #1a5c3a;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 35px;
            page-break-inside: avoid;
        }}
        .background-lines {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            opacity: 0.15;
            z-index: 0;
        }}
        .background-lines::before {{
            content: '';
            position: absolute;
            top: -20%;
            left: -20%;
            width: 140%;
            height: 140%;
            background:
                radial-gradient(circle at 10% 80%, transparent 38%, #2d5f3d 40%, transparent 42%),
                radial-gradient(circle at 90% 20%, transparent 38%, #2d5f3d 40%, transparent 42%);
            background-size: 50% 50%;
            transform: rotate(-15deg);
        }}
        .background-lines::after {{
            content: '';
            position: absolute;
            top: -20%;
            left: -20%;
            width: 140%;
            height: 140%;
            background:
                radial-gradient(circle at 20% 70%, transparent 38%, #2d5f3d 40%, transparent 42%),
                radial-gradient(circle at 80% 30%, transparent 38%, #2d5f3d 40%, transparent 42%);
            background-size: 50% 50%;
            transform: rotate(5deg);
        }}
        .content {{
            position: relative;
            z-index: 1;
            width: 100%;
        }}
        .org-header {{
            font-family: 'Montserrat', sans-serif;
            font-size: 10px;
            color: #1a5c3a;
            margin-bottom: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .title {{
            font-family: 'Dancing Script', cursive;
            font-size: 90px;
            color: #000000;
            margin-bottom: 3px;
            line-height: 0.9;
            font-weight: 700;
        }}
        .subtitle {{
            font-family: 'Montserrat', sans-serif;
            font-size: 16px;
            color: #666;
            margin-bottom: 25px;
            letter-spacing: 3px;
            text-transform: uppercase;
            font-weight: 400;
        }}
        .proudly-presented {{
            font-family: 'Montserrat', sans-serif;
            font-size: 14px;
            color: #555;
            margin-bottom: 12px;
            font-style: italic;
            font-weight: 400;
        }}
        .name {{
            font-family: 'Dancing Script', cursive;
            font-size: 54px;
            color: #1a5c3a;
            margin-bottom: 10px;
            border-bottom: 1.5px solid #888;
            padding-bottom: 6px;
            display: inline-block;
            max-width: 85%;
            font-weight: 700;
            line-height: 1.1;
        }}
        .course-description {{
            font-family: 'Montserrat', sans-serif;
            font-size: 12px;
            color: #555;
            margin-bottom: 30px;
            max-width: 750px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.6;
            font-weight: 400;
        }}
        .signatures {{
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            width: 90%;
            margin: 25px auto 0 auto;
            position: relative;
        }}
        .signature-block {{
            flex: 1;
            text-align: center;
            padding: 0 20px;
        }}
        .signature-line {{
            border-bottom: 1.5px solid #888;
            width: 70%;
            margin: 0 auto 8px auto;
        }}
        .signature-img {{
            max-width: 150px;
            height: auto;
            margin: 0 auto 5px;
            display: block;
        }}
        .signer-name {{
            font-family: 'Montserrat', sans-serif;
            font-size: 12px;
            color: #444;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .signer-title {{
            font-family: 'Montserrat', sans-serif;
            font-size: 11px;
            color: #777;
            font-weight: 400;
        }}
        .seal {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 130px;
            height: 130px;
            border-radius: 50%;
            border: 3px dashed #1a5c3a;
            background: linear-gradient(135deg, #e8f3ed 0%, #d4e8dc 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Montserrat', sans-serif;
            font-size: 10px;
            color: #1a5c3a;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            line-height: 1.3;
            padding: 15px;
            box-sizing: border-box;
            z-index: 2;
            transform: translate(-50%, -50%) rotate(-15deg);
            margin-top: 120px;
            font-weight: 700;
        }}
        .seal-text {{
            transform: rotate(15deg);
            text-align: center;
        }}
        .cert-number {{
            position: absolute;
            bottom: 22px;
            left: 40px;
            font-size: 8px;
            color: #999;
            text-align: left;
            font-family: 'Montserrat', sans-serif;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="certificate-container">
        <div class="background-lines"></div>

        <div class="content">
            <p class="org-header">Public Health Bureau - Federal Republic of Nigeria</p>
            <h1 class="title">Certificate</h1>
            <p class="subtitle">OF APPROVAL</p>

            <p class="proudly-presented">proudly presented to</p>
            <p class="name">{hospital.name}</p>
            <p class="course-description">
                In recognition of successfully completing the comprehensive registration and verification
                process with the Public Health Bureau (PHB). This hospital has met all required standards
                and is hereby authorized as a verified member of the PHB Healthcare Network, with full
                access to the Electronic Health Records System, Electronic Prescription Service, and all
                integrated healthcare platform services.
            </p>

            <div class="signatures">
                <div class="signature-block">
                    {f'<img src="data:image/png;base64,{signature_base64}" class="signature-img" alt="Signature" />' if signature_base64 else ''}
                    <div class="signature-line"></div>
                    <p class="signer-name">PHB Administration</p>
                    <p class="signer-title">authorized signature</p>
                </div>

                <div class="seal">
                    <span class="seal-text">Verified<br>&amp;<br>Approved</span>
                </div>

                <div class="signature-block">
                    <div class="signature-line"></div>
                    <p class="signer-name">{timezone.now().strftime('%d %B %Y').upper()}</p>
                    <p class="signer-title">date of issue</p>
                </div>
            </div>

            <div class="cert-number">
                Certificate ID: PHB-CERT-{hospital.id:04d}-{timezone.now().strftime('%Y%m%d')}<br/>
                Registration: {hospital.registration_number} | Location: {hospital.city}, {hospital.state}<br/>
                Verify at: https://phb.ng/verify/{hospital.registration_number}
            </div>
        </div>
    </div>
</body>
</html>
"""

        # Generate PDF using WeasyPrint for better font support
        pdf_buffer = BytesIO()
        HTML(string=certificate_html).write_pdf(pdf_buffer)
        
        pdf_buffer.seek(0)
        logger.info(f"✅ PDF certificate generated for {hospital.name}")
        return pdf_buffer

    except Exception as e:
        logger.error(f"❌ Failed to generate PDF certificate: {str(e)}")
        return None


def send_hospital_professional_certificate(hospital):
    """
    Send PHB Professional Certificate of Approval to newly registered hospital.

    This email is sent when an admin manually registers a hospital after
    completing background checks. It serves as official PHB certification
    and includes hospital credentials and next steps.

    Args:
        hospital: Hospital model instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if not hospital.email:
            logger.warning(f"Cannot send certificate to {hospital.name} - no email address")
            return False

        # Get hospital admin user if exists
        admin_user = hospital.user if hasattr(hospital, 'user') else None

        # Email subject
        subject = f'🏥 PHB Professional Certificate of Approval - {hospital.name}'

        # Plain text version
        plain_message = f"""
PHB (Public Health Bureau) - Certificate of Hospital Approval

Dear {hospital.name} Team,

Congratulations! Your hospital has been successfully registered with the Public Health Bureau (PHB) healthcare network.

═══════════════════════════════════════════════════════════
HOSPITAL REGISTRATION DETAILS
═══════════════════════════════════════════════════════════

Hospital Name: {hospital.name}
Registration Number: {hospital.registration_number}
Hospital Type: {hospital.get_hospital_type_display()}
Location: {hospital.city}, {hospital.state}, {hospital.country}

Registration Status: ✅ APPROVED
Verification Status: {'✅ VERIFIED' if hospital.is_verified else '⏳ PENDING VERIFICATION'}

═══════════════════════════════════════════════════════════
OFFICIAL PHB CERTIFICATION
═══════════════════════════════════════════════════════════

This email serves as your official PHB Professional Certificate of Approval.
{hospital.name} has successfully passed our background verification process
and is now an authorized member of the PHB healthcare network.

As a certified PHB hospital, you have access to:
✓ PHB Electronic Health Records (EHR) System
✓ Electronic Prescription Service (EPS)
✓ Patient Appointment Management
✓ Telemedicine Platform Integration
✓ Medical Staff Credentialing System
✓ Insurance Claims Processing
✓ Quality Metrics Dashboard

═══════════════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════════════

To complete your hospital setup, please:

1. LICENSE UPLOAD
   • Upload government operating licenses
   • Upload specialist service licenses
   • Upload pharmacy licenses (if applicable)
   • All licenses must be current and valid

2. COMPLIANCE DOCUMENTATION
   • HIPAA Compliance Certificate
   • Nigeria Data Protection Compliance
   • Medical Device Regulations (if applicable)

3. STAFF REGISTRATION
   • Register medical director
   • Add doctors and medical staff
   • Create department structures
   • Assign staff roles and permissions

4. PHARMACY AFFILIATION (Optional)
   • Link to affiliated pharmacies
   • Enable electronic prescription routing
   • Set up medication dispensing workflows

5. OPERATIONAL SETUP
   • Configure appointment types and schedules
   • Set up emergency contact protocols
   • Configure billing and insurance integrations
   • Enable patient registration

═══════════════════════════════════════════════════════════
IMPORTANT INFORMATION
═══════════════════════════════════════════════════════════

Hospital Status: The hospital status will remain "PENDING" until all
required licenses and compliance documents are uploaded through the
PHB admin dashboard.

Admin Access: {'Hospital admin credentials have been sent separately.' if admin_user else 'Please contact PHB support to create hospital admin accounts.'}

Support: For technical assistance or questions, contact:
• Email: support@phb.ng
• Phone: +234 xxx xxx xxxx
• Portal: https://phb.ng/support

═══════════════════════════════════════════════════════════

Welcome to the PHB Healthcare Network!

We're excited to have {hospital.name} as part of our mission to improve
healthcare access and quality across Nigeria.

Best regards,
PHB Administration Team
Public Health Bureau
https://phb.ng

---
This is an automated system message from PHB.
Certificate issued on: {timezone.now().strftime('%B %d, %Y at %H:%M %Z')}
"""

        # HTML version with clean, professional styling matching practice page template
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333333; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; }}

        /* Header */
        .header {{
            padding: 32px 40px 24px;
            border-bottom: 2px solid #000000;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #000000;
            margin: 0;
        }}
        .subtitle {{
            font-size: 14px;
            color: #666666;
            margin: 4px 0 0 0;
        }}

        /* Success Banner - Green for approval */
        .success-banner {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px 40px;
            margin: 0;
        }}
        .success-banner h2 {{
            margin: 0 0 8px 0;
            font-size: 18px;
            color: #155724;
        }}
        .success-banner p {{
            margin: 0;
            font-size: 14px;
            color: #155724;
        }}

        /* Content */
        .content {{ padding: 40px; }}
        .text {{
            font-size: 15px;
            color: #333333;
            margin: 0 0 16px 0;
            line-height: 1.5;
        }}

        /* Info Box */
        .info-box {{
            background: #f9f9f9;
            border: 1px solid #e5e5e5;
            padding: 24px;
            margin: 24px 0;
        }}
        .info-heading {{
            font-size: 12px;
            font-weight: 600;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0 0 16px 0;
        }}
        .hospital-name {{
            font-size: 18px;
            font-weight: 700;
            color: #000000;
            margin: 0 0 20px 0;
        }}
        .detail-row {{
            margin: 8px 0;
            font-size: 14px;
            color: #333333;
        }}
        .detail-row strong {{
            color: #666666;
            font-weight: 600;
        }}

        /* Badge */
        .badge {{
            display: inline-block;
            background: #dcfce7;
            color: #166534;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin: 4px 4px 4px 0;
        }}

        /* Requirements Section */
        .requirements-section {{
            margin: 32px 0;
        }}
        .requirements-heading {{
            font-size: 16px;
            font-weight: 600;
            color: #000000;
            margin: 0 0 16px 0;
        }}
        .requirement {{
            margin-bottom: 16px;
            font-size: 14px;
            line-height: 1.5;
            padding-left: 20px;
            position: relative;
        }}
        .requirement:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
            font-size: 18px;
        }}

        /* Next Steps */
        .steps {{
            margin: 24px 0;
        }}
        .step {{
            margin-bottom: 20px;
            padding: 16px;
            background: #f9f9f9;
            border-left: 3px solid #000000;
            border-radius: 0 4px 4px 0;
        }}
        .step-title {{
            font-size: 14px;
            font-weight: 600;
            color: #000000;
            margin: 0 0 8px 0;
        }}
        .step-desc {{
            font-size: 13px;
            color: #666666;
            margin: 0;
            line-height: 1.5;
        }}

        /* Warning Box */
        .warning-box {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 24px;
            margin: 24px 0;
        }}
        .warning-heading {{
            font-size: 16px;
            font-weight: 600;
            color: #856404;
            margin: 0 0 12px 0;
        }}
        .warning-text {{
            font-size: 14px;
            color: #856404;
            margin: 0 0 8px 0;
        }}

        /* Footer */
        .footer {{
            padding: 32px 40px;
            background: #f9f9f9;
            border-top: 1px solid #e5e5e5;
            font-size: 12px;
            color: #666666;
            line-height: 1.6;
        }}
        .footer p {{
            margin: 0 0 8px 0;
        }}
        .footer a {{
            color: #000000;
            text-decoration: none;
        }}
        .footer-divider {{
            height: 1px;
            background: #e5e5e5;
            margin: 16px 0;
        }}

        @media only screen and (max-width: 600px) {{
            .header, .content, .footer, .success-banner {{ padding: 24px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">PHB</div>
            <div class="subtitle">Public Health Bureau - Healthcare Network</div>
        </div>

        <!-- Success Banner -->
        <div class="success-banner">
            <h2>🏥 Hospital Approved & Verified</h2>
            <p>Welcome to the PHB Healthcare Network</p>
        </div>

        <!-- Content -->
        <div class="content">
            <p class="text">
                Dear {hospital.name} Team,
            </p>

            <p class="text">
                <strong>Congratulations!</strong> Your hospital has been successfully registered with the Public Health Bureau (PHB) healthcare network after completing our comprehensive background verification process.
            </p>

            <p class="text">
                🎉 <strong>A PDF certificate is attached to this email</strong> for your records.
            </p>

            <!-- Hospital Information -->
            <div class="info-box">
                <div class="info-heading">Hospital Registration Details</div>
                <div class="hospital-name">{hospital.name}</div>

                <div class="detail-row"><strong>Registration Number:</strong> {hospital.registration_number}</div>
                <div class="detail-row"><strong>Hospital Type:</strong> {hospital.get_hospital_type_display()}</div>
                <div class="detail-row"><strong>Location:</strong> {hospital.city}, {hospital.state}, {hospital.country}</div>
                <div class="detail-row"><strong>Date Approved:</strong> {timezone.now().strftime('%B %d, %Y')}</div>

                <p style="margin: 16px 0 0 0;">
                    <span class="badge">✅ APPROVED</span>
                    <span class="badge">✅ VERIFIED</span>
                </p>
            </div>

            <!-- Network Benefits -->
            <div class="info-box">
                <div class="info-heading">PHB Network Access</div>
                <p style="margin: 0 0 12px 0; font-size: 14px; color: #333333;">
                    As a certified PHB hospital, you now have full access to:
                </p>

                <div class="requirement">
                    <strong>PHB Electronic Health Records (EHR) System</strong>
                </div>
                <div class="requirement">
                    <strong>Electronic Prescription Service (EPS)</strong>
                </div>
                <div class="requirement">
                    <strong>Patient Appointment Management</strong>
                </div>
                <div class="requirement">
                    <strong>Telemedicine Platform Integration</strong>
                </div>
                <div class="requirement">
                    <strong>Medical Staff Credentialing System</strong>
                </div>
                <div class="requirement">
                    <strong>Insurance Claims Processing</strong>
                </div>
                <div class="requirement">
                    <strong>Quality Metrics Dashboard</strong>
                </div>
            </div>

            <!-- Next Steps -->
            <div class="requirements-section">
                <div class="requirements-heading">Next Steps to Complete Setup</div>

                <div class="steps">
                    <div class="step">
                        <div class="step-title">1. License Upload</div>
                        <p class="step-desc">Upload all government operating licenses, specialist service licenses, and pharmacy licenses through the PHB admin dashboard. All licenses must be current and valid.</p>
                    </div>

                    <div class="step">
                        <div class="step-title">2. Compliance Documentation</div>
                        <p class="step-desc">Upload HIPAA compliance, Nigeria Data Protection compliance, and any applicable medical device regulation certificates.</p>
                    </div>

                    <div class="step">
                        <div class="step-title">3. Staff Registration</div>
                        <p class="step-desc">Register your medical director, add doctors and medical staff, create department structures, and assign roles.</p>
                    </div>

                    <div class="step">
                        <div class="step-title">4. Pharmacy Affiliation (Optional)</div>
                        <p class="step-desc">Link to affiliated pharmacies to enable electronic prescription routing and medication dispensing workflows.</p>
                    </div>

                    <div class="step">
                        <div class="step-title">5. Operational Setup</div>
                        <p class="step-desc">Configure appointment types, emergency protocols, billing integrations, and enable patient registration.</p>
                    </div>
                </div>
            </div>

            <!-- Important Notice -->
            <div class="warning-box">
                <div class="warning-heading">⚠️ Important Information</div>
                <p class="warning-text">
                    <strong>Hospital Status:</strong> Your hospital status will remain "PENDING" until all required licenses and compliance documents are uploaded through the PHB admin dashboard.
                </p>
                <p class="warning-text" style="margin-bottom: 0;">
                    <strong>Admin Access:</strong> {'Hospital admin credentials have been sent separately.' if admin_user else 'Please contact PHB support at support@phb.ng to create hospital admin accounts.'}
                </p>
            </div>

            <p class="text" style="margin-top: 32px; font-size: 16px;">
                <strong>Welcome to the PHB Healthcare Network!</strong>
            </p>

            <p class="text">
                We're excited to have {hospital.name} as part of our mission to improve healthcare access and quality across Nigeria.
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>Public Health Bureau</strong></p>
            <p>Healthcare Network Division</p>
            <p>Federal Capital Territory, Abuja, Nigeria</p>

            <div class="footer-divider"></div>

            <p>
                Hospital: {hospital.name}<br>
                Email: <a href="mailto:support@phb.ng">support@phb.ng</a> |
                Website: <a href="https://phb.ng">phb.ng</a>
            </p>

            <p style="margin-top: 16px; color: #999999;">
                Certificate issued on {timezone.now().strftime('%B %d, %Y at %H:%M %Z')}<br>
                Certificate ID: PHB-CERT-{hospital.id}-{timezone.now().strftime('%Y%m%d')}
            </p>

            <p style="margin-top: 16px; color: #999999;">
                © 2025 Public Health Bureau. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""

        # Generate PDF certificate
        pdf_buffer = generate_hospital_certificate_pdf(hospital)

        # Send email with PDF attachment
        email = EmailMessage(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[hospital.email],
        )

        # Add HTML alternative
        email.content_subtype = "html"
        email.body = html_message

        # Attach PDF certificate if generation was successful
        if pdf_buffer:
            filename = f"PHB_Certificate_{hospital.name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
            email.attach(filename, pdf_buffer.read(), 'application/pdf')
            logger.info(f"📎 PDF certificate attached: {filename}")
        else:
            logger.warning(f"⚠️ Email sent without PDF attachment - generation failed")

        email.send(fail_silently=False)

        logger.info(
            f"✅ PHB Professional Certificate sent to {hospital.name} ({hospital.email})"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send hospital professional certificate: {str(e)}")
        return False


def send_hospital_admin_credentials(hospital, admin_email, password):
    """
    Send hospital admin login credentials email.

    This email is sent when an admin creates a hospital and includes
    the generated organization login credentials for hospital management.

    Args:
        hospital: Hospital model instance
        admin_email: Generated admin email address
        password: Generated password for the admin account

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if not hospital.email:
            logger.warning(f"Cannot send credentials to {hospital.name} - no email address")
            return False

        subject = f'🔐 Hospital Admin Credentials - {hospital.name}'

        # Plain text version
        plain_message = f"""
PHB (Public Health Bureau) - Hospital Admin Credentials

Dear {hospital.name} Team,

Your hospital has been successfully registered with PHB. Below are your login credentials
for accessing the hospital management portal.

═══════════════════════════════════════════════════════════
YOUR LOGIN CREDENTIALS
═══════════════════════════════════════════════════════════

Hospital Code: {hospital.registration_number}

Username/Login Email: {admin_email}

Password: {password}

Please keep these credentials secure.

═══════════════════════════════════════════════════════════
IMPORTANT INFORMATION
═══════════════════════════════════════════════════════════

Login Portal: http://localhost:5173/organization/login

Next Steps:
1. Login using the credentials above
2. Upload required government licenses
3. Complete compliance documentation
4. Register medical staff
5. Set up operational schedules

Your hospital status will remain "PENDING" until all required licenses
and compliance documents are uploaded and reviewed by PHB administrators.

═══════════════════════════════════════════════════════════

For technical assistance, contact:
• Email: support@phb.ng
• Phone: +234 xxx xxx xxxx

Best regards,
PHB Administration Team
Public Health Bureau

---
This is an automated system message from PHB.
Credentials issued on: {timezone.now().strftime('%B %d, %Y at %H:%M %Z')}
"""

        # HTML version with professional styling
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            margin: 20px auto;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .credentials-box {{
            background: #fff3cd;
            padding: 25px;
            border-left: 5px solid #ffc107;
            border-radius: 6px;
            margin: 25px 0;
        }}
        .credential-item {{
            margin: 15px 0;
            padding: 12px;
            background: white;
            border-radius: 4px;
            border: 1px solid #ffd454;
        }}
        .credential-label {{
            font-weight: 600;
            color: #856404;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .credential-value {{
            font-size: 18px;
            color: #1e293b;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }}
        .warning-box {{
            background: #ffeeba;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            border: 1px solid #ffc107;
        }}
        .info-box {{
            background: #e7f3ff;
            padding: 20px;
            border-left: 4px solid #2563eb;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 14px 28px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .steps {{
            list-style: none;
            padding: 0;
        }}
        .steps li {{
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .steps li:before {{
            content: "✓ ";
            color: #2563eb;
            font-weight: bold;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">🔐 Hospital Admin Access</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.95;">PHB Hospital Management Portal</p>
        </div>

        <p style="font-size: 16px;">Dear {hospital.name} Team,</p>

        <p>Your hospital has been successfully registered with the Public Health Bureau. Below are your login credentials for accessing the hospital management portal.</p>

        <div class="credentials-box">
            <h3 style="margin-top: 0; color: #856404;">🔑 Your Login Credentials</h3>

            <div class="credential-item">
                <div class="credential-label">Hospital Code:</div>
                <div class="credential-value">{hospital.registration_number}</div>
            </div>

            <div class="credential-item">
                <div class="credential-label">Username/Login Email:</div>
                <div class="credential-value">{admin_email}</div>
            </div>

            <div class="credential-item">
                <div class="credential-label">Password:</div>
                <div class="credential-value">{password}</div>
            </div>

            <div class="warning-box">
                <strong>⚠️ Please keep these credentials secure.</strong>
            </div>
        </div>

        <div style="text-align: center;">
            <a href="http://localhost:5173/organization/login" class="btn">
                🔐 Login to Hospital Portal
            </a>
        </div>

        <div class="info-box">
            <h3 style="margin-top: 0; color: #1e40af;">📋 Next Steps</h3>
            <ul class="steps">
                <li>Login using the credentials above</li>
                <li>Upload required government licenses</li>
                <li>Complete compliance documentation</li>
                <li>Register medical director and staff</li>
                <li>Set up appointment schedules</li>
            </ul>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 25px 0;">
            <p style="margin: 0; color: #6c757d;"><strong>Important:</strong> Your hospital status will remain <strong style="color: #ffc107;">"PENDING"</strong> until all required licenses and compliance documents are uploaded and reviewed by PHB administrators.</p>
        </div>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e2e8f0;">

        <p style="color: #6c757d; font-size: 14px;">
            <strong>Need Help?</strong><br>
            For technical assistance, contact:<br>
            • Email: support@phb.ng<br>
            • Phone: +234 xxx xxx xxxx
        </p>

        <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">
            This is an automated message from PHB.<br>
            Credentials issued on: {timezone.now().strftime('%B %d, %Y at %H:%M %Z')}
        </p>
    </div>
</body>
</html>
"""

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[hospital.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"✅ Hospital admin credentials sent to {hospital.name} ({hospital.email})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send hospital admin credentials: {str(e)}")
        return False


def send_hospital_registration_approved_email(
    patient_email,
    patient_name,
    hospital_name,
    hospital_address,
    approval_date,
    hpn=None,
    hospital_phone=None,
    hospital_email=None,
    hospital_profile_url=None
):
    """
    Send email notification when a hospital approves a patient's registration request

    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        hospital_name (str): Name of the hospital
        hospital_address (str): Full address of the hospital
        approval_date (datetime): Date when registration was approved
        hpn (str, optional): Patient's Health Profile Number
        hospital_phone (str, optional): Hospital contact phone number
        hospital_email (str, optional): Hospital contact email
        hospital_profile_url (str, optional): URL to hospital's profile page

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        frontend_url = os.environ.get('NEXTJS_URL', 'http://localhost:3001').rstrip('/')

        # Format approval date
        formatted_approval_date = approval_date.strftime('%B %d, %Y')

        # Build context for template
        context = {
            'patient_name': patient_name,
            'hospital_name': hospital_name,
            'hospital_address': hospital_address,
            'approval_date': formatted_approval_date,
            'hpn': hpn,
            'hospital_phone': hospital_phone,
            'hospital_email': hospital_email,
            'hospital_profile_url': hospital_profile_url,
            'dashboard_url': f"{frontend_url}/account",
            'help_url': f"{frontend_url}/help",
        }

        # Render email template
        html_message = render_to_string('email/hospital_registration_approved.html', context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=f'Hospital Registration Approved ✅ - {hospital_name}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[patient_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"✅ Hospital registration approval email sent to {patient_email} for {hospital_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send hospital registration approval email: {str(e)}")
        return False
