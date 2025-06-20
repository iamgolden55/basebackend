from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
import json
import logging

from api.models.medical.payment_transaction import PaymentTransaction
from api.models import Appointment, Hospital
from api.serializers import PaymentTransactionSerializer

logger = logging.getLogger(__name__)

class PaymentInitializeView(APIView):
    """Initialize a payment for an appointment"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # 🔍 DEBUG: Log complete request data to identify symptoms_data issue
            logger.debug(f"Payment initialize request data: {request.data}")
            logger.debug(f"Request data keys: {list(request.data.keys())}")
            if 'symptoms_data' in request.data:
                logger.debug(f"symptoms_data value: {request.data.get('symptoms_data')}")
                logger.debug(f"symptoms_data type: {type(request.data.get('symptoms_data'))}")
            else:
                logger.debug("symptoms_data NOT found in request data")
                
            # 🛡️ ROBUSTNESS: Ensure symptoms_data is always available as a list
            if 'symptoms_data' not in request.data or request.data.get('symptoms_data') is None:
                request.data['symptoms_data'] = []
                logger.debug("Set symptoms_data to empty list as fallback")
            
            # 🚫 CHECK IF PAYMENTS ARE DISABLED
            if not getattr(settings, 'PAYMENTS_ENABLED', True):
                logger.info("Payment disabled - handling appointment creation with waived payment")
                return self._handle_disabled_payment_flow(request)
            
            # Get request data
            appointment_id = request.data.get('appointment_id')  # 🎯 NOW OPTIONAL!
            amount = request.data.get('amount')
            payment_method = request.data.get('payment_method', 'card')
            payment_provider = request.data.get('payment_provider', 'paystack')
            
            logger.info(f"Payment initialization request: appointment_id={appointment_id}, amount={amount}, provider={payment_provider}")
            
            # Validate required fields (appointment_id is now optional!)
            if not amount:
                return Response({
                    'error': 'amount is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get appointment if provided
            appointment = None
            booking_details = None
            
            if appointment_id:
                appointment = get_object_or_404(Appointment, id=appointment_id)
                logger.info(f"Found appointment: {appointment.appointment_id}")
                
                # Check if user has permission to pay for this appointment
                if appointment.patient != request.user:
                    return Response({
                        'error': 'You can only pay for your own appointments'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Check if appointment already has a completed payment
                existing_payment = PaymentTransaction.objects.filter(
                    appointment=appointment,
                    payment_status='completed'
                ).first()
                
                if existing_payment:
                    return Response({
                        'error': 'This appointment already has a completed payment',
                        'payment_id': existing_payment.transaction_id
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # CRITICAL: Validate appointment for duplicate specialty conflicts
                # This prevents payment for invalid appointments
                logger.info(f"Validating appointment {appointment.appointment_id} for conflicts...")
                try:
                    # Skip duplicate check for emergency appointments
                    is_emergency = (
                        appointment.priority == 'emergency' or 
                        appointment.appointment_type == 'emergency'
                    )
                    
                    if is_emergency:
                        logger.info("Skipping conflict validation for emergency appointment")
                    else:
                        # Check for duplicate appointments in same specialty on same date
                        same_specialty_appointments = Appointment.objects.filter(
                            patient=appointment.patient,
                            appointment_date__date=appointment.appointment_date.date(),
                            department=appointment.department,
                            status__in=['pending', 'confirmed', 'in_progress', 'scheduled']
                        ).exclude(
                            status__in=['cancelled', 'completed', 'no_show']
                        ).exclude(
                            pk=appointment.pk  # Exclude the current appointment
                        )
                        
                        if same_specialty_appointments.exists():
                            existing_appointment = same_specialty_appointments.first()
                            logger.warning(f"Payment blocked: Duplicate appointment found {existing_appointment.appointment_id}")
                            return Response({
                                'error': f'You already have a {appointment.department.name} appointment on {appointment.appointment_date.date().strftime("%B %d, %Y")}. Please choose another date or specialty.',
                                'conflict_details': {
                                    'existing_appointment_id': existing_appointment.appointment_id,
                                    'department': appointment.department.name,
                                    'date': appointment.appointment_date.date().strftime('%Y-%m-%d'),
                                    'time': existing_appointment.appointment_date.strftime('%H:%M'),
                                    'status': existing_appointment.status
                                }
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        logger.info("Appointment validation passed - no conflicts found")
                    
                except Exception as validation_error:
                    logger.error(f"Appointment validation error: {str(validation_error)}")
                    return Response({
                        'error': f'Failed to validate appointment: {str(validation_error)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # 🚀 PAYMENT-FIRST APPROACH: Extract and store booking details for later appointment creation
                logger.info("Payment-first approach: extracting booking details from request")
                
                # Extract appointment booking details from request data
                booking_details = {
                    'department_id': request.data.get('department_id'),
                    'appointment_date': request.data.get('appointment_date'),
                    'appointment_type': request.data.get('appointment_type', 'consultation'),
                    'priority': request.data.get('priority', 'normal'),
                    'chief_complaint': request.data.get('chief_complaint', ''),
                    'symptoms': request.data.get('symptoms', ''),
                    'medical_history': request.data.get('medical_history', ''),
                    'allergies': request.data.get('allergies', ''),
                    'current_medications': request.data.get('current_medications', ''),
                    'hospital_id': request.data.get('hospital_id'),
                    'duration': request.data.get('duration', 30),
                    'is_insurance_based': request.data.get('is_insurance_based', False),
                    'insurance_details': request.data.get('insurance_details', {}),
                }
                
                logger.info(f"Booking details extracted: {booking_details}")
                
                # Validate required booking details for payment-first approach
                required_fields = ['department_id', 'appointment_date']
                missing_fields = [field for field in required_fields if not booking_details.get(field)]
                
                if missing_fields:
                    return Response({
                        'error': f'For payment-first booking, these fields are required: {", ".join(missing_fields)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            # No appointment_id provided - payment-first approach
            logger.info("No appointment_id provided - creating payment without appointment (payment-first approach)")
            
            # Create payment transaction (appointment can be null!)
            try:
                payment_data = {
                    'patient': request.user,
                    'amount': float(amount),
                    'payment_method': payment_method,
                    'payment_provider': payment_provider,
                    'currency': 'NGN',
                    'created_by': request.user,
                    'last_modified_by': request.user
                }
                
                # 🎯 ONLY ADD APPOINTMENT AND HOSPITAL IF APPOINTMENT EXISTS
                if appointment:
                    payment_data['appointment'] = appointment
                    payment_data['hospital'] = appointment.hospital
                elif booking_details:
                    # 🚀 PAYMENT-FIRST: Get hospital from booking details
                    if booking_details['hospital_id']:
                        from api.models import Hospital
                        try:
                            hospital = Hospital.objects.get(id=booking_details['hospital_id'])
                            payment_data['hospital'] = hospital
                        except Hospital.DoesNotExist:
                            logger.warning(f"Hospital {booking_details['hospital_id']} not found")
                
                payment = PaymentTransaction.objects.create(**payment_data)
                logger.info(f"Created payment transaction: {payment.transaction_id}")
                
                # 🚀 STORE BOOKING DETAILS in payment for payment-first approach
                if booking_details:
                    # Store booking details in payment's description for later use
                    import json
                    payment.description = json.dumps({
                        'type': 'payment_first_booking',
                        'booking_details': booking_details
                    })
                    payment.save()
                    logger.info(f"Stored booking details in payment {payment.transaction_id}")
            except Exception as create_error:
                logger.error(f"Failed to create payment transaction: {str(create_error)}")
                return Response({
                    'error': f'Failed to create payment: {str(create_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Initialize payment with provider
            try:
                # 🚨 TEMPORARY TEST: Skip provider initialization to test PaymentTransaction creation
                logger.info(f"🧪 TEST: PaymentTransaction created successfully: {payment.transaction_id}")
                logger.info(f"🧪 TEST: Payment provider: {payment.payment_provider}")
                logger.info(f"🧪 TEST: About to test provider initialization...")
                
                # Test getting payment provider
                provider = payment.get_payment_provider()
                logger.info(f"🧪 TEST: Provider retrieved: {provider}")
                
                if not provider:
                    logger.error("🚨 TEST: No payment provider found!")
                    return Response({
                        'error': 'No payment provider configured'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Try to initialize payment
                payment_url = provider.initialize_payment()
                logger.info(f"✅ TEST: Payment initialized successfully: {payment_url}")
                
                return Response({
                    'success': True,
                    'payment_id': payment.transaction_id,
                    'payment_url': payment_url,
                    'provider_reference': payment.provider_reference,
                    'amount': payment.amount_display,
                    'currency': payment.currency
                }, status=status.HTTP_201_CREATED)
                
            except ValidationError as e:
                logger.error(f"🚨 TEST: Payment provider validation error: {str(e)}")
                # Clean up failed payment
                payment.delete()
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as provider_error:
                logger.error(f"🚨 TEST: Unexpected payment provider error: {str(provider_error)}")
                logger.error(f"🚨 TEST: Error type: {type(provider_error).__name__}")
                import traceback
                logger.error(f"🚨 TEST: Full traceback: {traceback.format_exc()}")
                # Clean up failed payment
                payment.delete()
                return Response({
                    'error': f'Payment provider error: {str(provider_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Payment initialization error: {str(e)}")
            return Response({
                'error': f'Payment initialization failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_disabled_payment_flow(self, request):
        """Handle appointment creation when payments are disabled"""
        try:
            appointment_id = request.data.get('appointment_id')
            
            if appointment_id:
                # Traditional flow: update existing appointment to waived payment
                try:
                    appointment = get_object_or_404(Appointment, id=appointment_id)
                    
                    # Check if user owns this appointment
                    if appointment.patient != request.user:
                        return Response({
                            'error': 'You can only modify your own appointments'
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    # Update appointment payment status to waived
                    appointment.payment_status = 'waived'
                    appointment.payment_required = False
                    appointment.save()
                    
                    logger.info(f"Updated appointment {appointment.appointment_id} to waived payment status")
                    
                    return Response({
                        'success': True,
                        'payments_enabled': False,
                        'message': 'Appointment confirmed with waived payment',
                        'appointment_id': appointment.appointment_id,
                        'payment_status': 'waived',
                        'amount': 0,
                        'currency': 'NGN'
                    }, status=status.HTTP_200_OK)
                    
                except Appointment.DoesNotExist:
                    return Response({
                        'error': 'Appointment not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Payment-first flow: create appointment directly with waived payment
                return self._create_appointment_with_waived_payment(request)
                
        except Exception as e:
            logger.error(f"Disabled payment flow error: {str(e)}")
            return Response({
                'error': f'Failed to process appointment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_appointment_with_waived_payment(self, request):
        """Create appointment directly when payments are disabled"""
        try:
            # Extract appointment details from request
            booking_details = {
                'department_id': request.data.get('department_id'),
                'appointment_date': request.data.get('appointment_date'),
                'appointment_type': request.data.get('appointment_type', 'consultation'),
                'priority': request.data.get('priority', 'normal'),
                'chief_complaint': request.data.get('chief_complaint', ''),
                'symptoms': request.data.get('symptoms', ''),
                'symptoms_data': request.data.get('symptoms_data', []),  # Get symptoms_data from request
                'medical_history': request.data.get('medical_history', ''),
                'allergies': request.data.get('allergies', ''),
                'current_medications': request.data.get('current_medications', ''),
                'hospital_id': request.data.get('hospital_id'),
                'duration': request.data.get('duration', 30),
                'is_insurance_based': request.data.get('is_insurance_based', False),
                'insurance_details': request.data.get('insurance_details', {}),
            }
            
            # 🔍 DEBUG: Log symptoms_data handling
            logger.debug(f"symptoms_data from request: {request.data.get('symptoms_data')}")
            logger.debug(f"symptoms_data in booking_details: {booking_details['symptoms_data']}")
            logger.debug(f"symptoms_data type: {type(booking_details['symptoms_data'])}")
            
            # Validate required fields
            required_fields = ['department_id', 'appointment_date']
            missing_fields = [field for field in required_fields if not booking_details.get(field)]
            
            if missing_fields:
                return Response({
                    'error': f'Required fields missing: {", ".join(missing_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get department and hospital
            from api.models.medical.department import Department
            try:
                department = Department.objects.get(id=booking_details['department_id'])
            except Department.DoesNotExist:
                return Response({
                    'error': 'Department not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get hospital
            hospital = None
            if booking_details['hospital_id']:
                try:
                    hospital = Hospital.objects.get(id=booking_details['hospital_id'])
                except Hospital.DoesNotExist:
                    logger.warning(f"Hospital {booking_details['hospital_id']} not found")
            
            # Fallback to user's primary hospital if no hospital specified
            if not hospital:
                try:
                    from api.models.medical.hospital_registration import HospitalRegistration
                    primary_registration = HospitalRegistration.objects.filter(
                        user=request.user,
                        is_primary=True,
                        status='approved'
                    ).first()
                    if primary_registration:
                        hospital = primary_registration.hospital
                except Exception as reg_error:
                    logger.warning(f"Failed to get primary hospital: {reg_error}")
            
            if not hospital:
                return Response({
                    'error': 'No hospital found. Please specify hospital_id or register with a hospital first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse appointment date
            from django.utils.dateparse import parse_datetime
            try:
                appointment_date = parse_datetime(booking_details['appointment_date'])
                if not appointment_date:
                    from datetime import datetime
                    appointment_date = datetime.fromisoformat(booking_details['appointment_date'].replace('Z', '+00:00'))
            except Exception as date_error:
                return Response({
                    'error': f'Invalid appointment date format: {booking_details["appointment_date"]}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ensure symptoms_data is a proper list
            symptoms_data = booking_details.get('symptoms_data', [])
            if not isinstance(symptoms_data, list):
                logger.warning(f"symptoms_data is not a list, converting: {symptoms_data} (type: {type(symptoms_data)})")
                symptoms_data = [] if symptoms_data in [None, '', 'null'] else list(symptoms_data) if hasattr(symptoms_data, '__iter__') else []
            
            logger.debug(f"Final symptoms_data for appointment creation: {symptoms_data}")
            
            # Create appointment with waived payment
            appointment = Appointment.objects.create(
                appointment_id=Appointment.generate_appointment_id(),
                patient=request.user,
                hospital=hospital,
                department=department,
                appointment_date=appointment_date,
                appointment_type=booking_details.get('appointment_type', 'consultation'),
                priority=booking_details.get('priority', 'normal'),
                chief_complaint=booking_details.get('chief_complaint', ''),
                symptoms=booking_details.get('symptoms', ''),
                symptoms_data=symptoms_data,  # Use the validated symptoms_data
                medical_history=booking_details.get('medical_history', ''),
                allergies=booking_details.get('allergies', ''),
                current_medications=booking_details.get('current_medications', ''),
                duration=booking_details.get('duration', 30),
                is_insurance_based=booking_details.get('is_insurance_based', False),
                insurance_details=booking_details.get('insurance_details', {}),
                status='pending',
                payment_status='waived',  # Set payment as waived
                payment_required=False  # No payment required
            )
            
            logger.info(f"Created appointment {appointment.appointment_id} with waived payment (payments disabled)")
            
            return Response({
                'success': True,
                'payments_enabled': False,
                'message': 'Appointment created successfully with waived payment',
                'appointment_id': appointment.appointment_id,
                'payment_status': 'waived',
                'amount': 0,
                'currency': 'NGN',
                'appointment_date': appointment.appointment_date.isoformat(),
                'department': department.name,
                'hospital': hospital.name
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as ve:
            logger.error(f"Appointment validation error: {str(ve)}")
            return Response({
                'error': f'Appointment validation failed: {str(ve)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Create appointment error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Failed to create appointment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentVerifyView(APIView):
    """Verify a payment status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, reference):
        try:
            # 🚫 CHECK IF PAYMENTS ARE DISABLED
            if not getattr(settings, 'PAYMENTS_ENABLED', True):
                return Response({
                    'success': True,
                    'payments_enabled': False,
                    'message': 'Payments are currently disabled. All appointments have waived payment status.',
                    'payment_status': 'waived'
                }, status=status.HTTP_200_OK)
            
            # Find payment by reference
            payment = get_object_or_404(
                PaymentTransaction, 
                provider_reference=reference
            )
            
            # Check if user has permission to verify this payment
            if payment.patient != request.user:
                return Response({
                    'error': 'You can only verify your own payments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verify payment with provider
            try:
                logger.info(f"🔍 Starting payment verification for {reference}")
                logger.info(f"🔍 Payment status BEFORE verification: {payment.payment_status}")
                
                verification_result = payment.verify_payment(reference)
                
                logger.info(f"🔍 Payment status AFTER verification: {payment.payment_status}")
                logger.info(f"🔍 Verification result: {verification_result}")
                
                # 🚀 Send payment confirmation email if payment is completed
                if payment.payment_status == 'completed':
                    logger.info(f"✅ Payment is completed, sending confirmation email...")
                    from api.utils.email import send_payment_confirmation_email
                    email_result = send_payment_confirmation_email(payment)
                    logger.info(f"📧 Payment confirmation email result: {email_result}")
                else:
                    logger.warning(f"⚠️ Payment status is '{payment.payment_status}' - not sending email")
                
                # Log access
                payment.log_access(request.user)
                
                return Response({
                    'success': True,
                    'payment_id': payment.transaction_id,
                    'status': payment.payment_status,
                    'amount': payment.amount_display,
                    'currency': payment.currency,
                    'completed_at': payment.completed_at,
                    'verification_data': verification_result
                }, status=status.HTTP_200_OK)
                
            except ValidationError as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except PaymentTransaction.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return Response({
                'error': 'Payment verification failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentHistoryView(APIView):
    """Get user's payment history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's payments with pagination
            payments = PaymentTransaction.objects.filter(
                patient=request.user
            ).order_by('-created_at')
            
            # Serialize payments
            serializer = PaymentTransactionSerializer(payments, many=True)
            
            # Log access for each payment
            for payment in payments:
                payment.log_access(request.user)
            
            return Response({
                'success': True,
                'payments': serializer.data,
                'count': payments.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Payment history error: {str(e)}")
            return Response({
                'error': 'Failed to retrieve payment history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentWebhookView(APIView):
    """Handle payment provider webhooks"""
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        try:
            # 🚫 CHECK IF PAYMENTS ARE DISABLED
            if not getattr(settings, 'PAYMENTS_ENABLED', True):
                logger.info("Webhook received but payments are disabled - ignoring")
                return Response({
                    'success': True,
                    'message': 'Webhook received but payments are disabled'
                }, status=status.HTTP_200_OK)
            
            # Get webhook signature
            signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
            if not signature:
                return Response({
                    'error': 'Missing webhook signature'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get webhook data
            webhook_data = request.data
            
            # Find payment by reference
            reference = webhook_data.get('data', {}).get('reference')
            if not reference:
                return Response({
                    'error': 'Missing payment reference'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            payment = get_object_or_404(
                PaymentTransaction,
                provider_reference=reference
            )
            
            # Process webhook with payment provider
            provider = payment.get_payment_provider()
            if not provider:
                return Response({
                    'error': 'Payment provider not found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process webhook
            provider.process_webhook(webhook_data, signature)
            
            # 🚀 Send payment confirmation email if payment is now completed
            payment.refresh_from_db()  # Refresh to get updated status
            if payment.payment_status == 'completed':
                from api.utils.email import send_payment_confirmation_email
                email_result = send_payment_confirmation_email(payment)
                logger.info(f"Webhook payment confirmation email result: {email_result}")
            
            logger.info(f"Webhook processed successfully for payment {payment.transaction_id}")
            
            return Response({
                'success': True
            }, status=status.HTTP_200_OK)
            
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Webhook received for unknown payment reference: {reference}")
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Webhook validation error: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return Response({
                'error': 'Webhook processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatsView(APIView):
    """Get payment statistics for dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if payments are disabled
            payments_enabled = getattr(settings, 'PAYMENTS_ENABLED', True)
            
            if not payments_enabled:
                return Response({
                    'success': True,
                    'payments_enabled': False,
                    'stats': {
                        'total_payments': 0,
                        'completed_payments': 0,
                        'pending_payments': 0,
                        'failed_payments': 0,
                        'total_amount_paid': 0,
                        'recent_payments': [],
                        'message': 'Payments are currently disabled. All appointments have waived payment status.'
                    }
                }, status=status.HTTP_200_OK)
            
            # Get user's payment statistics
            user_payments = PaymentTransaction.objects.filter(patient=request.user)
            
            stats = {
                'total_payments': user_payments.count(),
                'completed_payments': user_payments.filter(payment_status='completed').count(),
                'pending_payments': user_payments.filter(payment_status='pending').count(),
                'failed_payments': user_payments.filter(payment_status='failed').count(),
                'total_amount_paid': sum(
                    p.amount for p in user_payments.filter(payment_status='completed')
                ),
                'recent_payments': PaymentTransactionSerializer(
                    user_payments.order_by('-created_at')[:5], many=True
                ).data
            }
            
            return Response({
                'success': True,
                'payments_enabled': True,
                'stats': stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Payment stats error: {str(e)}")
            return Response({
                'error': 'Failed to retrieve payment statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(APIView):
    """Get payment system status"""
    permission_classes = []  # Public endpoint
    
    def get(self, request):
        """Check if payments are enabled"""
        payments_enabled = getattr(settings, 'PAYMENTS_ENABLED', True)
        
        return Response({
            'payments_enabled': payments_enabled,
            'message': 'Payments are enabled' if payments_enabled else 'Payments are currently disabled - all appointments have waived payment status',
            'available_providers': ['paystack'] if payments_enabled else [],
            'free_appointments': not payments_enabled
        }, status=status.HTTP_200_OK)
