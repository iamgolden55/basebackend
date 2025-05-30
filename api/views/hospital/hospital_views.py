import os
import logging
import traceback
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.db.models import Q, F, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.generic.base import RedirectView

from rest_framework import generics, status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied

from api.models import (
    Hospital, HospitalRegistration, CustomUser, Appointment, Doctor
)
from api.models.medical.appointment_notification import AppointmentNotification
from api.models.medical.department import Department
from api.models.medical.appointment import AppointmentType
from api.models.medical.medication import Medication, MedicationCatalog
from api.models.medical.medical_record import MedicalRecord
from api.serializers import (
    HospitalRegistrationSerializer, HospitalSerializer, HospitalLocationSerializer,
    NearbyHospitalSerializer, AppointmentSerializer, AppointmentListSerializer,
    HospitalAdminRegistrationSerializer, ExistingUserToAdminSerializer,
    AppointmentCancelSerializer, AppointmentRescheduleSerializer,
    AppointmentApproveSerializer, AppointmentReferSerializer,
    MedicationSerializer, PrescriptionSerializer
)
from api.utils.location_utils import get_location_from_ip

# Logger setup
logger = logging.getLogger(__name__)

class HospitalRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Add debug logging
        print("Received data:", request.data)  # Debug print 🔍
        
        # Validate hospital exists
        hospital_id = request.data.get('hospital')
        if not hospital_id:
            return Response({
                'error': 'Hospital ID is required',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({
                'error': 'Hospital not found',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_404_NOT_FOUND)

        # Create serializer with modified data
        serializer = self.get_serializer(data={
            'hospital_id': hospital_id,  # Use hospital_id instead of hospital
            'is_primary': request.data.get('is_primary', False),
            'user': request.user.id  # Make sure user is included
        })
        
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "message": "Hospital registration request submitted successfully! 🏥",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)  # Debug print 🔍
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserHospitalRegistrationsView(generics.ListAPIView):
    serializer_class = HospitalRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status')
        
        if user.role == 'hospital_admin':
            # For hospital admins: show all registrations for their hospital
            # FIX: Get the hospital where this user is the admin
            admin_hospital = Hospital.objects.filter(user=user).first()
            if admin_hospital:
                queryset = HospitalRegistration.objects.filter(
                    hospital=admin_hospital
                ).select_related('user', 'hospital')
                
                # Apply status filter if provided
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                    
                return queryset
            else:
                # If admin is not linked to any hospital, return empty queryset
                return HospitalRegistration.objects.none()
        else:
            # For regular users: show their own registrations
            queryset = HospitalRegistration.objects.filter(
                user=user
            ).select_related('user', 'hospital')
            
            # Apply status filter if provided
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                
            return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Always return an array, even if empty
        return Response(serializer.data)

class SetPrimaryHospitalView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, hospital_id):
        success = request.user.set_primary_hospital(hospital_id)
        
        if success:
            return Response({
                "message": "Primary hospital updated successfully! 🏥✨",
            }, status=status.HTTP_200_OK)
        
        return Response({
            "error": "Could not set primary hospital. Please ensure you're registered with this hospital first! 🚫"
        }, status=status.HTTP_400_BAD_REQUEST)    

class ApproveHospitalRegistrationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, registration_id):
        # Get the registration
        registration = get_object_or_404(HospitalRegistration, id=registration_id)
        
        # Check if user is hospital admin
        if request.user.role != 'hospital_admin':
            return Response({
                "error": "Only hospital administrators can approve registrations! 🚫"
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if user is admin of this specific hospital
        if request.user.hospital != registration.hospital:
            return Response({
                "error": "You can only approve registrations for your hospital! 🏥"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Approve the registration
        registration.approve_registration()
        
        return Response({
            "message": "Registration approved successfully! 🎉",
            "registration": {
                "id": registration.id,
                "hospital": registration.hospital.name,
                "user": registration.user.email,
                "status": "approved",
                "approved_date": registration.approved_date
            }
        }, status=status.HTTP_200_OK)    

class HospitalAdminRegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Initially allow anyone, but you might want to restrict this
    
    def get_serializer_class(self):
        if self.request.data.get('existing_user', False):
            return ExistingUserToAdminSerializer
        return HospitalAdminRegistrationSerializer
    
    def post(self, request, *args, **kwargs):
        is_existing_user = request.data.get('existing_user', False)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        
        if serializer.is_valid():
            admin = serializer.save()
            
            response_data = {
                "message": "Hospital admin registered successfully! 🏥✨",
                "admin": {
                    "email": admin.email,
                    "name": admin.name,
                    "hospital": admin.hospital.name,
                    "position": admin.position
                }
            }
            
            if is_existing_user:
                response_data["admin"]["existing_user_converted"] = True
                
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments 🏥
    
    This ViewSet provides comprehensive functionality for managing medical appointments,
    including creating, retrieving, updating, and deleting appointments, as well as
    specialized actions like cancellation, rescheduling, approval, and referral.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['doctor__first_name', 'doctor__last_name', 'chief_complaint', 'status']
    ordering_fields = ['appointment_date', 'created_at', 'priority']
    ordering = ['-appointment_date']
    filterset_fields = ['status', 'appointment_type', 'priority', 'hospital', 'department']
    lookup_field = 'pk'  # Default lookup field
    lookup_value_regex = r'[0-9]+|APT-[A-Za-z0-9]+'  # Allow numeric IDs or APT-* format

    def get_object(self):
        """
        Custom get_object method to retrieve appointments by numeric ID or appointment_id
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # Check if the lookup value matches APT-* format
        if lookup_value.startswith('APT-'):
            # For appointment_id lookups, bypass the normal queryset filtering
            # to allow access to appointments where user is either patient or doctor
            user = self.request.user
            
            # Find appointment directly by appointment_id
            from django.db.models import Q
            all_appointments = Appointment.objects.filter(
                appointment_id=lookup_value
            ).select_related(
                'doctor', 'doctor__user', 'hospital', 'department', 'patient'
            )
            
            # Then check if user is the patient, the doctor, or a hospital admin
            if not all_appointments.exists():
                raise Http404(f"No appointment found with ID: {lookup_value}")
                
            appointment = all_appointments.first()
            
            # Check permissions - user must be either the patient, the doctor, or admin
            is_patient = appointment.patient == user
            is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
            is_department = hasattr(user, 'doctor_profile') and appointment.department == user.doctor_profile.department
            is_hospital_admin = hasattr(user, 'hospital_admin') and appointment.hospital == user.hospital_admin.hospital
            
            if not (is_patient or is_doctor or is_hospital_admin or is_department):
                self.permission_denied(
                    self.request,
                    message="You don't have permission to access this appointment"
                )
                
            return appointment
        else:
            # Default behavior for numeric IDs
            return super().get_object()

    def get_queryset(self):
        """
        Filter appointments based on user role and query parameters
        """
        user = self.request.user
        
        # Debug info
        print(f"\n--- Appointment filtering for user ID: {user.id} ---")
        print(f"User role: {user.role}")
        print(f"Has doctor_profile: {hasattr(user, 'doctor_profile')}")
        print(f"Has hospital_admin: {hasattr(user, 'hospital_admin')}")
        
        # Base queryset with select_related for better performance
        base_qs = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'hospital', 'department'
        )
        
        # Check for view_as parameter to override default role filtering
        view_as = self.request.query_params.get('view_as')
        print(f"View as parameter: {view_as}")
        
        # Filter based on view_as parameter first, then role
        if view_as == 'doctor' and hasattr(user, 'doctor_profile'):
            # Explicitly show appointments where user is the doctor
            queryset = base_qs.filter(doctor=user.doctor_profile)
            print("Filtering as doctor (explicit override)")
        elif view_as == 'patient':
            # Explicitly show appointments where user is the patient
            queryset = base_qs.filter(patient=user)
            print("Filtering as patient (explicit override)")
        elif hasattr(user, 'hospital_admin'):
            # Hospital admins see all appointments for their hospital
            queryset = base_qs.filter(hospital=user.hospital_admin.hospital)
            print("Filtering as hospital admin")
        else:
            # Default behavior: show patient appointments
            # This is the key change - all users (including doctors) 
            # see their patient appointments by default
            queryset = base_qs.filter(patient=user)
            print("Filtering as patient (default behavior)")
        
        # Apply date filters if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                queryset = queryset.filter(appointment_date__gte=start_date)
            
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d')
                ).replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(appointment_date__lte=end_date)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format in query params: {e}")
        
        # Filter by upcoming appointments if requested
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                appointment_date__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            )
        
        print(f"Query returned {queryset.count()} appointments")
        return queryset

    def get_serializer_class(self):
        """
        Use different serializers based on the action
        """
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'cancel':
            return AppointmentCancelSerializer
        elif self.action == 'reschedule':
            return AppointmentRescheduleSerializer
        elif self.action == 'approve':
            return AppointmentApproveSerializer
        elif self.action == 'refer':
            return AppointmentReferSerializer
        return AppointmentSerializer

    def create(self, request, *args, **kwargs):
        """Override create method to add debug logging and fix common issues"""
        import traceback
        import json
        
        print("\n\n====================================================")
        print("=============== APPOINTMENT CREATE DEBUG ============")
        print("====================================================")
        
        # Print request data in a more readable format
        print(f"REQUEST DATA (raw): {request.data}")
        
        # Try to print as formatted JSON for better readability
        try:
            if hasattr(request.data, '_mutable'):
                # For QueryDict
                data_copy = request.data.copy()
                print(f"REQUEST DATA (pretty): {json.dumps(data_copy, indent=2, default=str)}")
            else:
                # For regular dict or other data types
                print(f"REQUEST DATA (pretty): {json.dumps(request.data, indent=2, default=str)}")
        except Exception as e:
            print(f"Could not pretty-print request data: {e}")
        
        print(f"CONTENT TYPE: {request.content_type}")
        print(f"METHOD: {request.method}")
        print(f"USER: {request.user.id} - {request.user.email}")
        
        # Create a mutable copy of request.data
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Field name mapping - Fix common field name mismatches
        field_mapping = {
            'department_id': 'department',
            'doctor_id': 'doctor_id',  # Keep as is - serializer expects doctor_id
            'fee_id': None  # Remove fee_id completely
        }
        
        # Apply field name mapping
        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in data:
                # Only rename if backend field is different and not None
                if backend_field and backend_field != frontend_field:
                    data[backend_field] = data.pop(frontend_field)
                    print(f"Mapped field {frontend_field} to {backend_field}")
                # Remove if backend field is explicitly None
                elif backend_field is None:
                    data.pop(frontend_field)
                    print(f"Removed field {frontend_field}")
                # Otherwise, keep the field as is (e.g., doctor_id)
                else:
                    print(f"Kept field {frontend_field} as is")
        
        # CRITICAL FIX: If hospital is None, get the user's primary hospital
        if data.get('hospital') is None:
            try:
                # Get user's primary hospital
                from api.models.medical.hospital_registration import HospitalRegistration
                primary_hospital = HospitalRegistration.objects.filter(
                    user=request.user,
                    is_primary=True,
                    status='approved'
                ).first()
                
                if primary_hospital:
                    data['hospital'] = primary_hospital.hospital.id
                    print(f"Using user's primary hospital: {primary_hospital.hospital.id} ({primary_hospital.hospital.name})")
                else:
                    # If no primary hospital, get any approved hospital
                    any_hospital = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='approved'
                    ).first()
                    
                    if any_hospital:
                        data['hospital'] = any_hospital.hospital.id
                        print(f"Using user's approved hospital: {any_hospital.hospital.id} ({any_hospital.hospital.name})")
                    else:
                        print("User has no approved hospitals. Cannot proceed with appointment.")
                        return Response(
                            {"error": "You need to be registered with a hospital before booking appointments."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                print(f"Error getting user's hospital: {str(e)}")
        
        # Fix appointment_type - convert from display name to database value
        if data.get('appointment_type') == 'First Visit':
            data['appointment_type'] = 'first_visit'
            print("Fixed appointment_type: 'First Visit' -> 'first_visit'")
        elif data.get('appointment_type') == 'Follow Up':
            data['appointment_type'] = 'follow_up'
            print("Fixed appointment_type: 'Follow Up' -> 'follow_up'")
        
        # IMPORTANT FIX: If the doctor is from a different hospital than the patient's,
        # we should use an available doctor from the patient's hospital
        if 'doctor_id' in data and data.get('hospital') is not None:
            try:
                doctor = Doctor.objects.get(id=data['doctor_id'])
                if doctor.hospital.id != data['hospital']:
                    print(f"Doctor {doctor.id} is from hospital {doctor.hospital.id}, but patient's hospital is {data['hospital']}")
                    
                    # Find an available doctor from the correct hospital
                    from django.db.models import Q
                    available_doctors = Doctor.objects.filter(
                        Q(department_id=data.get('department')),
                        Q(hospital_id=data.get('hospital')),
                        Q(is_active=True),
                        Q(available_for_appointments=True)
                    )
                    
                    if available_doctors.exists():
                        # Use the first available doctor
                        new_doctor = available_doctors.first()
                        data['doctor_id'] = new_doctor.id
                        print(f"Found available doctor {new_doctor.id} from correct hospital {data['hospital']}")
                    else:
                        print(f"No available doctors found in department {data.get('department')} at hospital {data['hospital']}")
                        doctor_id = data.pop('doctor_id', None)
                        print(f"Removed doctor_id {doctor_id} to allow auto-assignment")
            except Doctor.DoesNotExist:
                print(f"Doctor with ID {data.get('doctor_id')} does not exist")
                data.pop('doctor_id', None)
            except Exception as e:
                print(f"Error checking doctor's hospital: {str(e)}")
        
        # Call parent create method but catch validation errors
        try:
            # Use our modified data
            print(f"PROCESSED DATA: {data}")
            serializer = self.get_serializer(data=data)
            
            # Check serializer validation
            if not serializer.is_valid():
                print(f"VALIDATION ERRORS: {serializer.errors}")
                
                # Print more specific details about each validation error
                for field, errors in serializer.errors.items():
                    print(f"  - Field '{field}': {errors}")
                
                # Create a more detailed error response
                detailed_response = {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors,
                    'data_received': {
                        key: value for key, value in data.items() 
                        if key not in ['password', 'token']  # Don't log sensitive data
                    },
                    'help': 'Check the error details for each field and ensure all required fields are provided correctly.'
                }
                
                return Response(
                    detailed_response,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print("SERIALIZER VALIDATED SUCCESSFULLY")
            print(f"VALIDATED DATA: {serializer.validated_data}")
            
            # Continue with normal create process
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            print(f"EXCEPTION TYPE: {type(e).__name__}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        finally:
            print("====================================================")
            print("=============== END DEBUG INFO =====================")
            print("====================================================\n\n")

    def perform_create(self, serializer):
        """
        Set the patient to the current user when creating an appointment
        """
        # Validate appointment date is not in the past
        appointment_date = serializer.validated_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.now():
            raise DjangoValidationError("Cannot create appointments in the past.")
        
        # Create appointment without a doctor
        appointment = serializer.save(
            patient=self.request.user,
            status='pending',
            doctor=None  # Explicitly set doctor to None
        )
        
        try:
            # Create notification for the patient
            AppointmentNotification.objects.create(
                appointment=appointment,
                notification_type='email',
                event_type='booking_confirmation',
                recipient=appointment.patient,
                subject=f"Appointment Booking Confirmation - {appointment.appointment_id}",
                message=(
                    f"Dear {appointment.patient.get_full_name()},\n\n"
                    f"Your appointment at {appointment.hospital.name} ({appointment.department.name}) "
                    f"on {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been booked.\n\n"
                    f"Appointment ID: {appointment.appointment_id}\n"
                    f"Status: Pending doctor's acceptance\n"
                ),
                template_name='appointment_booking_confirmation'
            )
            
            if appointment.patient.phone:
                AppointmentNotification.objects.create(
                    appointment=appointment,
                    notification_type='sms',
                    event_type='booking_confirmation',
                    recipient=appointment.patient,
                    subject=f"Appt Booked: {appointment.appointment_id}",
                    message=(
                        f"Appt Booked at {appointment.hospital.name}, "
                        f"{appointment.appointment_date.strftime('%b %d, %H:%M')}. "
                        f"ID: {appointment.appointment_id}. "
                        f"Status: Pending"
                    )
                )
            
            # Create notification for all doctors in the department
            doctors = Doctor.objects.filter(
                department=appointment.department,
                hospital=appointment.hospital,
                is_active=True
            )
            
            for doctor in doctors:
                AppointmentNotification.objects.create(
                    appointment=appointment,
                    notification_type='email',
                    event_type='new_appointment_available',
                    recipient=doctor.user,
                    subject=f"New Appointment Available - {appointment.appointment_id}",
                    message=(
                        f"Dear Dr. {doctor.user.get_full_name()},\n\n"
                        f"A new appointment is available in your department:\n"
                        f"Date: {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}\n"
                        f"Department: {appointment.department.name}\n"
                        f"Patient: {appointment.patient.get_full_name()}\n"
                        f"Chief Complaint: {appointment.chief_complaint}\n\n"
                        f"Please review and accept if you are available."
                    ),
                    template_name='new_appointment_notification'
                )
            
        except Exception as e:
            logger.error(f"Failed to send appointment notifications: {e}")
            # Don't raise the error - appointment creation should succeed even if notification fails
        
        return appointment

    def _is_doctor_available(self, doctor, appointment_date):
        """
        Check if a doctor is available for a given appointment date
        """
        print(f"\n--- Checking availability for Doctor {doctor.id} at {appointment_date} ---")
        
        # Check if date is within doctor's consultation days
        day_name = appointment_date.strftime('%a')  # Get 3-letter day name
        consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
        print(f"Day of appointment: {day_name}")
        print(f"Doctor consultation days: {consultation_days}")
        
        # Make the day check more flexible by ignoring case and allowing more formats
        day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                      any(day_name.lower() in day.lower() for day in consultation_days)
                      
        if not day_matches and day_name not in consultation_days:
            print(f"Doctor {doctor.id} doesn't work on {day_name}")
            return False
        
        # Check if time is within consultation hours
        appointment_time = appointment_date.time()
        print(f"Appointment time: {appointment_time}")
        print(f"Doctor hours: {doctor.consultation_hours_start} - {doctor.consultation_hours_end}")
        
        # Skip time check if consultation hours are not set
        if doctor.consultation_hours_start is None or doctor.consultation_hours_end is None:
            print(f"Doctor {doctor.id} has no consultation hours set, assuming available")
        else:
            if not (doctor.consultation_hours_start <= appointment_time <= doctor.consultation_hours_end):
                print(f"Appointment time {appointment_time} is outside doctor's hours ({doctor.consultation_hours_start} - {doctor.consultation_hours_end})")
                return False
        
        # Check for overlapping appointments
        appointment_end = appointment_date + timedelta(minutes=doctor.appointment_duration)
        print(f"Appointment duration: {doctor.appointment_duration} minutes")
        print(f"Checking for overlapping appointments between {appointment_date} and {appointment_end}")
        
        overlapping = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed', 'in_progress', 'scheduled', 'checking_in'],
            appointment_date__date=appointment_date.date(),  # Only check appointments on the same day
            appointment_date__gte=appointment_date - timedelta(minutes=doctor.appointment_duration),  # Start time is before or at the requested end time
            appointment_date__lt=appointment_end  # Start time is before the end of the requested slot
        )
        
        if overlapping.exists():
            print(f"Found {overlapping.count()} overlapping appointments:")
            for appt in overlapping:
                print(f"  - Appointment {appt.id} at {appt.appointment_date}")
            return False
        
        print(f"Doctor {doctor.id} is available at {appointment_date}")
        return True

    def _send_appointment_confirmation(self, appointment):
        """
        Send appointment confirmation with error handling
        """
        try:
            # Create email notification for the patient
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.patient,
                notification_type='email',
                event_type='booking_confirmation',
                subject='Appointment Confirmation',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                        f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create SMS notification for the patient
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.patient,
                notification_type='sms',
                event_type='booking_confirmation',
                subject='Appointment Confirmation',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                        f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create notification for the doctor
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.doctor.user,
                notification_type='email',
                event_type='booking_confirmation',
                subject='New Appointment',
                message=f'New appointment scheduled with {appointment.patient.get_full_name()} '
                        f'on {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create reminders
            appointment.create_reminders()
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            # Don't raise the error - appointment creation should succeed even if notification fails

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Get a detailed summary of the appointment, formatted like the email template.
        """
        appointment = self.get_object()
        serializer = self.get_serializer(appointment)
        
        # Format data to match email template structure
        summary_data = {
            "appointment_details": {
                "appointment_id": appointment.appointment_id,
                "doctor": serializer.data.get('doctor_full_name'),
                "date": serializer.data.get('formatted_date'),
                "time": serializer.data.get('formatted_time'),
                "formatted_date_time": serializer.data.get('formatted_date_time'),
                "hospital": serializer.data.get('hospital_name'),
                "department": serializer.data.get('department_name'),
                "type": serializer.data.get('formatted_appointment_type'),
                "priority": serializer.data.get('formatted_priority'),
                "duration": f"{appointment.duration} minutes",
                "status": serializer.data.get('status_display'),
            },
            "patient_details": {
                "name": serializer.data.get('patient_name'),
                "chief_complaint": appointment.chief_complaint,
                "symptoms": appointment.symptoms,
                "medical_history": appointment.medical_history,
                "allergies": appointment.allergies,
                "current_medications": appointment.current_medications
            },
            "important_notes": serializer.data.get('important_notes'),
            "payment_info": {
                "payment_required": appointment.payment_required,
                "payment_status": appointment.payment_status,
                "is_insurance_based": appointment.is_insurance_based,
                "insurance_details": appointment.insurance_details if appointment.is_insurance_based else None
            },
            "additional_info": {
                "notes": appointment.notes,
                "created_at": appointment.created_at.strftime("%B %d, %Y at %I:%M %p") if appointment.created_at else None,
                "updated_at": appointment.updated_at.strftime("%B %d, %Y at %I:%M %p") if appointment.updated_at else None,
            }
        }
        
        return Response(summary_data)
        
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update just the status of an appointment.
        
        This is a simpler endpoint for updating appointment status without needing
        to supply all the fields that the full update would require.
        """
        appointment = self.get_object()
        
        # Get the new status from the request data
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'Status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the status is valid
        valid_statuses = dict(Appointment.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Special handling for status changes
        old_status = appointment.status
        
        # Check if the transition is valid
        if not appointment._is_valid_status_transition(old_status, new_status):
            return Response(
                {'error': f'Invalid status transition from {old_status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update the status
        try:
            appointment.status = new_status
            
            # Add status-specific fields if provided
            if new_status == 'cancelled' and 'cancellation_reason' in request.data:
                appointment.cancellation_reason = request.data['cancellation_reason']
                appointment.cancelled_at = timezone.now()
                
            elif new_status == 'confirmed':
                appointment.approved_by = request.user
                appointment.approval_date = timezone.now()
                if 'approval_notes' in request.data:
                    appointment.approval_notes = request.data['approval_notes']
                    
            elif new_status == 'completed':
                appointment.completed_at = timezone.now()
                
            # Save the appointment
            appointment.save(bypass_validation=True)
            
            # Return the updated appointment
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class HospitalLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for location-based hospital search and registration.
    """
    queryset = Hospital.objects.all()
    serializer_class = HospitalLocationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Find nearby hospitals based on user's location or IP address.
        With fallback to user's profile location if no hospitals found.
        """
        # Get location parameters
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # Default 10km radius

        try:
            # If coordinates not provided, try to get location from IP
            if not (latitude and longitude):
                ip_address = request.META.get('REMOTE_ADDR')
                location_info = get_location_from_ip(ip_address)
                if location_info:
                    latitude = location_info.get('latitude')
                    longitude = location_info.get('longitude')

            # Convert to float and initialize hospitals to empty list
            hospitals = []
            
            # Only search by coordinates if we have them
            if latitude and longitude:
                # Convert to float
                latitude = float(latitude)
                longitude = float(longitude)
                radius = float(radius)

                # Find nearby hospitals
                hospitals = Hospital.find_nearby_hospitals(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=radius
                )

            # If no hospitals found through geolocation, fallback to user's profile location
            if not hospitals:
                user = request.user
                location_message = "No nearby hospitals found."
                
                # Check if user has state/city in their profile
                if user.state or user.city:
                    query = Q()
                    
                    # Add state and city filters if available
                    if user.city:
                        query |= Q(city__iexact=user.city)
                    
                    if user.state:
                        query |= Q(state__iexact=user.state)
                    
                    # Find hospitals matching the user's location
                    location_hospitals = Hospital.objects.filter(query)
                    
                    if location_hospitals.exists():
                        hospitals = location_hospitals
                        location_message = f"Showing hospitals in your profile location: {user.city or ''}, {user.state or ''}".strip(", ")
                
                # If still no hospitals, return all as last resort
                if not hospitals:
                    hospitals = Hospital.objects.all()
                    location_message = "No hospitals found in your area. Showing all hospitals."
                
                # Serialize the results
                serializer = HospitalSerializer(
                    hospitals,
                    many=True
                )
                
                return Response({
                    'message': location_message,
                    'hospitals': serializer.data
                })
            
            # Serialize the nearby results
            serializer = NearbyHospitalSerializer(
                hospitals,
                many=True,
                context={'request': request}
            )

            return Response({
                'hospitals': serializer.data,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius
                }
            })

        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid location parameters: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """
        Register the current user with a hospital.
        """
        hospital = self.get_object()
        user = request.user

        # Check if already registered
        existing_registration = HospitalRegistration.objects.filter(
            user=user,
            hospital=hospital
        ).first()

        if existing_registration:
            return Response({
                "error": "Already registered with this hospital",
                "registration": HospitalRegistrationSerializer(existing_registration).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new registration
        try:
            # Check if this is the user's first registration
            is_first_registration = not HospitalRegistration.objects.filter(
                user=user
            ).exists()

            registration = HospitalRegistration.objects.create(
                user=user,
                hospital=hospital,
                is_primary=is_first_registration,  # Set as primary if first registration
                status='pending'
            )

            return Response({
                "message": "Registration request submitted successfully",
                "registration": HospitalRegistrationSerializer(registration).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": f"Registration failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        Set a hospital as the user's primary hospital.
        """
        hospital = self.get_object()
        user = request.user

        try:
            # Check if registered and approved
            registration = HospitalRegistration.objects.filter(
                user=user,
                hospital=hospital,
                status='approved'
            ).first()

            if not registration:
                return Response({
                    "error": "Must be registered and approved with this hospital first"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update primary status
            HospitalRegistration.objects.filter(
                user=user,
                is_primary=True
            ).update(is_primary=False)

            registration.is_primary = True
            registration.save()

            return Response({
                "message": "Primary hospital updated successfully",
                "registration": HospitalRegistrationSerializer(registration).data
            })

        except Exception as e:
            return Response({
                "error": f"Failed to set primary hospital: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def has_primary_hospital(request):
    """
    Check if the authenticated user has a registered primary hospital
    
    Returns:
        {
            "has_primary": true/false,
            "primary_hospital": { hospital data } or null
        }
    """
    # Get the user's registered hospitals
    primary_registration = HospitalRegistration.objects.filter(
        user=request.user,
        is_primary=True
    ).first()
    
    if primary_registration:
        return Response({
            "has_primary": True,
            "primary_hospital": {
                "id": primary_registration.hospital.id,
                "name": primary_registration.hospital.name,
                "address": primary_registration.hospital.address,
                "city": primary_registration.hospital.city,
                "country": primary_registration.hospital.country,
                "registration_date": primary_registration.created_at,
                "status": primary_registration.status,
            }
        })
    else:
        return Response({
            "has_primary": False,
            "primary_hospital": None
        })

# existing views continue here...        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_registration(request, registration_id):
    # Check if user is hospital admin
    if not request.user.role == 'hospital_admin':
        return Response({
            'detail': 'Only hospital admins can approve registrations'
        }, status=403)
    
    # Get the registration
    try:
        registration = HospitalRegistration.objects.get(id=registration_id)
    except HospitalRegistration.DoesNotExist:
        return Response({
            'detail': 'Registration not found'
        }, status=404)
    
    # Check if admin belongs to the same hospital
    if request.user.hospital_admin_profile.hospital != registration.hospital:
        return Response({
            'detail': 'You can only approve registrations for your hospital'
        }, status=403)
    
    # Approve the registration
    registration.status = 'approved'
    registration.approved_date = timezone.now()
    registration.save()
    
    serializer = HospitalRegistrationSerializer(registration)
    return Response({
        'message': 'Registration approved successfully! 🎉',
        'registration': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hospital_registration(request):
    try:
        # Validate input data
        hospital_id = request.data.get('hospital')
        is_primary = request.data.get('is_primary', False)
        
        if not hospital_id:
            return Response({
                'error': 'Hospital ID is required',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the hospital
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({
                'error': 'Hospital not found',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if registration already exists
        if HospitalRegistration.objects.filter(user=request.user, hospital=hospital).exists():
            return Response({
                'error': 'You are already registered with this hospital'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create registration
        registration = HospitalRegistration.objects.create(
            user=request.user,
            hospital=hospital,
            is_primary=is_primary,
            status='pending'
        )
        
        serializer = HospitalRegistrationSerializer(registration)
        return Response({
            'message': 'Registration request submitted successfully! 🎉',
            'registration': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_list(request):
    hospitals = Hospital.objects.all()
    serializer = HospitalSerializer(hospitals, many=True)
    return Response({
        'hospitals': serializer.data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_exists(request):
    """
    Check if a user exists by email and if they're already a hospital admin.
    This is used in the hospital admin registration flow for converting existing users.
    
    Query params:
    - email: The email to check
    
    Returns:
    {
        "exists": true/false,
        "is_admin": true/false
    }
    """
    email = request.query_params.get('email')
    if not email:
        return Response({
            "error": "Email parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user_exists = CustomUser.objects.filter(email=email).exists()
    is_admin = False
    
    if user_exists:
        user = CustomUser.objects.get(email=email)
        is_admin = hasattr(user, 'hospital_admin_profile')
    
    return Response({
        "exists": user_exists,
        "is_admin": is_admin
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_types(request):
    # Filter by hospital if provided
    hospital_id = request.query_params.get('hospital')
    
    if hospital_id:
        # Get hospital-specific types and global types
        types = AppointmentType.objects.filter(
            (Q(hospital_id=hospital_id) | Q(hospital__isnull=True)),
            is_active=True
        ).order_by('name', '-hospital_id')
        # Deduplicate by name: prefer hospital-specific over global
        seen = set()
        unique_types = []
        for t in types:
            if t.name not in seen:
                unique_types.append(t)
                seen.add(t.name)
        types = unique_types
    else:
        # Get all active global types only
        types = AppointmentType.objects.filter(is_active=True, hospital__isnull=True)
    
    data = [{"id": type.id, "name": type.name, "description": type.description} for type in types]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def departments(request):
    # Get hospital_id from query params if provided
    hospital_id = request.query_params.get('hospital')
    
    if hospital_id:
        # If hospital_id is provided, verify user is registered with this hospital
        hospital_registration = HospitalRegistration.objects.filter(
            user=request.user,
            hospital_id=hospital_id,
            status='approved'
        ).first()
        
        if not hospital_registration:
            return Response({
                'status': 'error',
                'message': 'You are not registered with this hospital'
            }, status=status.HTTP_403_FORBIDDEN)
            
        departments = Department.objects.filter(hospital_id=hospital_id)
    else:
        # If no hospital_id provided, get departments from user's primary hospital
        primary_registration = HospitalRegistration.objects.filter(
            user=request.user,
            is_primary=True,
            status='approved'
        ).first()
        
        if not primary_registration:
            return Response({
                'status': 'error',
                'message': 'No primary hospital found. Please register with a hospital first.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        departments = Department.objects.filter(hospital=primary_registration.hospital)
    
    # 🛏️ ENHANCED WITH BED MAGIC! ✨
    # Build comprehensive department data with bed tracking, staff info, and patient statistics
    data = []
    for dept in departments:
        department_data = {
            # Basic Info
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "department_type": dept.department_type,
            "is_active": dept.is_active,
            "description": dept.description,
            
            # Location & Contact
            "floor_number": dept.floor_number,
            "wing": dept.wing,
            "extension_number": dept.extension_number,
            "emergency_contact": dept.emergency_contact,
            "email": dept.email,
            
            # 🛏️ BED TRACKING MAGIC:
            "total_beds": dept.total_beds,
            "occupied_beds": dept.occupied_beds,
            "available_beds": dept.available_beds,  # Calculated property
            "icu_beds": dept.icu_beds,
            "occupied_icu_beds": dept.occupied_icu_beds,
            "available_icu_beds": dept.available_icu_beds,  # Calculated property
            "bed_capacity": dept.bed_capacity,
            "total_available_beds": dept.total_available_beds,  # Calculated property
            "bed_utilization_rate": round(dept.bed_utilization_rate, 1),  # Calculated property
            
            # 👥 STAFF MANAGEMENT MAGIC:
            "current_staff_count": dept.current_staff_count,
            "minimum_staff_required": dept.minimum_staff_required,
            "is_understaffed": dept.is_understaffed,  # Calculated property
            "recommended_staff_ratio": dept.recommended_staff_ratio,
            "staff_utilization_rate": round(dept.staff_utilization_rate, 1),  # Calculated property
            
            # 🏥 PATIENT STATISTICS MAGIC:
            "current_patient_count": dept.current_patient_count,
            "utilization_rate": round(dept.utilization_rate, 1),  # Calculated property
            
            # ⏰ OPERATIONAL INFO:
            "is_24_hours": dept.is_24_hours,
            "operating_hours": dept.operating_hours,
            "appointment_duration": dept.appointment_duration,
            "max_daily_appointments": dept.max_daily_appointments,
            "requires_referral": dept.requires_referral,
            
            # 💰 BUDGET TRACKING:
            "annual_budget": float(dept.annual_budget) if dept.annual_budget else None,
            "budget_year": dept.budget_year,
            "budget_utilized": float(dept.budget_utilized) if dept.budget_utilized else 0,
            "budget_utilization_rate": round(dept.budget_utilization_rate, 1) if dept.annual_budget else 0,
            "remaining_budget": float(dept.remaining_budget) if dept.annual_budget else None,
            
            # 🏥 DEPARTMENT CLASSIFICATION:
            "is_clinical": dept.is_clinical,  # Calculated property
            "is_support": dept.is_support,    # Calculated property
            "is_administrative": dept.is_administrative,  # Calculated property
            "is_available_for_appointments": dept.is_available_for_appointments,  # Calculated property
        }
        data.append(department_data)
    
    return Response({
        'status': 'success',
        'departments': data,
        'total_departments': len(data),
        'message': f'Successfully retrieved {len(data)} departments with comprehensive bed tracking data! 🏥✨'
    })

# Add this new class for doctor assignment
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_hospital_registrations(request):
    """
    Lists all hospitals with pending user registrations.
    - Admin/staff users can see all hospitals with pending registrations
    - Hospital admins can see pending registrations for their own hospital
    - Regular users cannot access this endpoint
    """
    # Check permissions
    is_admin = request.user.is_staff or request.user.is_superuser
    is_hospital_admin = request.user.role == 'hospital_admin'
    
    if not (is_admin or is_hospital_admin):
        return Response({
            'error': 'You do not have permission to view pending registrations'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # For hospital admins, only show their hospital
    if is_hospital_admin and not is_admin:
        # Get the admin's hospital
        try:
            admin_hospital = request.user.hospital_admin_profile.hospital
            
            # Get pending registrations for this hospital
            pending_registrations = HospitalRegistration.objects.filter(
                status='pending',
                hospital=admin_hospital
            ).select_related('hospital', 'user')
            
            # Format the response
            registrations_list = []
            for registration in pending_registrations:
                registrations_list.append({
                    'id': registration.id,
                    'user_id': registration.user.id,
                    'user_email': registration.user.email,
                    'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                    'registration_date': registration.created_at
                })
            
            return Response({
                'hospital': {
                    'id': admin_hospital.id, 
                    'name': admin_hospital.name
                },
                'pending_registrations': registrations_list,
                'total_pending': len(registrations_list)
            })
        
        except Exception as e:
            return Response({
                'error': f'Error retrieving hospital information: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # For admin/staff, show all hospitals with pending registrations
    else:
        # Get all pending registrations
        pending_registrations = HospitalRegistration.objects.filter(
            status='pending'
        ).select_related('hospital', 'user')
        
        # Group registrations by hospital
        hospitals_with_pending = {}
        for registration in pending_registrations:
            hospital_id = registration.hospital.id
            hospital_name = registration.hospital.name
            
            if hospital_id not in hospitals_with_pending:
                hospitals_with_pending[hospital_id] = {
                    'id': hospital_id,
                    'name': hospital_name,
                    'pending_registrations': []
                }
            
            hospitals_with_pending[hospital_id]['pending_registrations'].append({
                'id': registration.id,
                'user_id': registration.user.id,
                'user_email': registration.user.email,
                'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                'registration_date': registration.created_at
            })
        
        # Add count to each hospital
        for hospital_id in hospitals_with_pending:
            hospitals_with_pending[hospital_id]['total_pending'] = len(
                hospitals_with_pending[hospital_id]['pending_registrations']
            )
        
        return Response({
            'hospitals_with_pending': list(hospitals_with_pending.values()),
            'total_hospitals': len(hospitals_with_pending),
            'total_pending_registrations': sum(
                len(h['pending_registrations']) for h in hospitals_with_pending.values()
            )
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_appointments(request):
    """
    Returns appointments where the current user is the doctor.
    This is specifically for users who are doctors to access their professional appointments.
    """
    user = request.user
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get doctor's appointments
        appointments = Appointment.objects.filter(
            doctor=user.doctor_profile
        ).select_related(
            'doctor', 'doctor__user', 'hospital', 'department', 'patient'
        ).order_by('-appointment_date')
        
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                appointments = appointments.filter(appointment_date__gte=start_date)
            
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d')
                ).replace(hour=23, minute=59, second=59)
                appointments = appointments.filter(appointment_date__lte=end_date)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format in query params: {e}")
        
        # Filter by upcoming appointments if requested
        upcoming = request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            appointments = appointments.filter(
                appointment_date__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            )
        
        # Serialize the appointments
        serializer = AppointmentListSerializer(appointments, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        import traceback
        error_msg = f"Error getting doctor appointments: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_pending_appointments(request):
    """
    Returns appointments in the doctor's department:
    - Pending appointments that need a doctor to accept them
    - Appointments assigned to the current doctor with various statuses
    
    This allows doctors to see both appointments they could potentially accept
    and track their own appointments in different states.
    
    Optional query parameters:
    - status: Filter by appointment status ('all', 'pending', 'confirmed', etc.)
    - doctor_id: For admins, view appointments for a specific doctor
    - start_date: Filter by start date (YYYY-MM-DD)
    - end_date: Filter by end date (YYYY-MM-DD)
    - priority: Filter by priority level
    """
    user = request.user
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Check if specific doctor_id is requested (for admin users)
        requested_doctor_id = request.query_params.get('doctor_id')
        is_admin = user.is_staff or user.is_superuser or user.role == 'hospital_admin'
        
        # If doctor_id is provided and user is admin, use that doctor instead
        if requested_doctor_id and is_admin:
            try:
                doctor = Doctor.objects.get(id=requested_doctor_id)
                if doctor.hospital != user.doctor_profile.hospital:
                    return Response({
                        'status': 'error',
                        'message': 'You can only view appointments for doctors in your hospital'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Doctor.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Doctor with ID {requested_doctor_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get status filter if provided, otherwise default to 'all'
        status_filter = request.query_params.get('status', 'all')
        
        # Initialize results dictionary
        result = {
            'pending_department_appointments': [],
            'my_appointments': {
                'confirmed': [],
                'in_progress': [],
                'completed': [],
                'cancelled': [],
                'no_show': [],
                'all': []
            },
            'doctor_info': {
                'id': doctor.id,
                'name': f"{doctor.user.first_name} {doctor.user.last_name}",
                'email': doctor.user.email,
                'specialization': doctor.specialization,
                'department': {
                    'id': doctor.department.id if doctor.department else None,
                    'name': doctor.department.name if doctor.department else None
                },
                'hospital': {
                    'id': doctor.hospital.id if doctor.hospital else None,
                    'name': doctor.hospital.name if doctor.hospital else None
                }
            }
        }
        
        # Get all pending appointments in the doctor's department and hospital
        # that don't have a doctor assigned yet
        if status_filter in ['all', 'pending']:
            pending_appointments = Appointment.objects.filter(
                department=doctor.department,
                hospital=doctor.hospital,
                status='pending',
                doctor__isnull=True  # No doctor assigned yet
            ).select_related(
                'hospital', 'department', 'patient'
            ).order_by('-priority', 'appointment_date')
            
            # Apply date filters if provided
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            try:
                if start_date:
                    start_date = timezone.make_aware(
                        datetime.strptime(start_date, '%Y-%m-%d')
                    )
                    pending_appointments = pending_appointments.filter(appointment_date__gte=start_date)
                
                if end_date:
                    end_date = timezone.make_aware(
                        datetime.strptime(end_date, '%Y-%m-%d')
                    ).replace(hour=23, minute=59, second=59)
                    pending_appointments = pending_appointments.filter(appointment_date__lte=end_date)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date format in query params: {e}")
            
            # Filter by priority if requested
            priority = request.query_params.get('priority')
            if priority:
                pending_appointments = pending_appointments.filter(priority=priority)
            
            # Serialize the pending appointments
            result['pending_department_appointments'] = AppointmentListSerializer(pending_appointments, many=True).data
        
        # Get doctor's own appointments with different statuses
        doctor_appointments_query = Appointment.objects.filter(
            doctor=doctor,
            hospital=doctor.hospital
        ).select_related(
            'doctor', 'doctor__user', 'hospital', 'department', 'patient'
        ).order_by('-appointment_date')
        
        # Apply date filters to doctor's appointments if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                doctor_appointments_query = doctor_appointments_query.filter(appointment_date__gte=start_date)
            
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d')
                ).replace(hour=23, minute=59, second=59)
                doctor_appointments_query = doctor_appointments_query.filter(appointment_date__lte=end_date)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format in query params: {e}")
        
        # Filter doctor's appointments by priority if requested
        priority = request.query_params.get('priority')
        if priority:
            doctor_appointments_query = doctor_appointments_query.filter(priority=priority)
        
        # Get all doctor's appointments
        doctor_appointments = doctor_appointments_query.all()
        result['my_appointments']['all'] = AppointmentListSerializer(doctor_appointments, many=True).data
        
        # Filter doctor's appointments by specific statuses
        # Only do this if status_filter is 'all' or specifically requested
        if status_filter in ['all', 'confirmed']:
            confirmed = doctor_appointments_query.filter(status='confirmed')
            result['my_appointments']['confirmed'] = AppointmentListSerializer(confirmed, many=True).data
        
        if status_filter in ['all', 'in_progress']:
            in_progress = doctor_appointments_query.filter(status='in_progress')
            result['my_appointments']['in_progress'] = AppointmentListSerializer(in_progress, many=True).data
        
        if status_filter in ['all', 'completed']:
            completed = doctor_appointments_query.filter(status='completed')
            result['my_appointments']['completed'] = AppointmentListSerializer(completed, many=True).data
        
        if status_filter in ['all', 'cancelled']:
            cancelled = doctor_appointments_query.filter(status='cancelled')
            result['my_appointments']['cancelled'] = AppointmentListSerializer(cancelled, many=True).data
        
        if status_filter in ['all', 'no_show']:
            no_show = doctor_appointments_query.filter(status='no_show')
            result['my_appointments']['no_show'] = AppointmentListSerializer(no_show, many=True).data
        
        # Add summary counts
        result['summary'] = {
            'pending_department_count': len(result['pending_department_appointments']),
            'my_appointments_count': {
                'confirmed': len(result['my_appointments']['confirmed']),
                'in_progress': len(result['my_appointments']['in_progress']),
                'completed': len(result['my_appointments']['completed']),
                'cancelled': len(result['my_appointments']['cancelled']),
                'no_show': len(result['my_appointments']['no_show']),
                'total': len(result['my_appointments']['all'])
            }
        }
        
        # Add additional fields like today's appointments count and upcoming appointments
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Count today's appointments
        today_count = doctor_appointments_query.filter(
            appointment_date__range=(today_start, today_end)
        ).count()
        
        # Count upcoming appointments (future dates with confirmed status)
        upcoming_count = doctor_appointments_query.filter(
            appointment_date__gt=today_end,
            status='confirmed'
        ).count()
        
        # Add to summary
        result['summary']['today_appointments'] = today_count
        result['summary']['upcoming_appointments'] = upcoming_count
        
        return Response(result)
    
    except Exception as e:
        import traceback
        error_msg = f"Error getting department appointments: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_appointment(request, appointment_id):
    """
    Allows a doctor to accept a pending appointment.
    This will assign the doctor to the appointment and change the status to confirmed.
    """
    user = request.user
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if appointment is in the same department as the doctor
        if appointment.department != doctor.department:
            return Response({
                'status': 'error',
                'message': 'You can only accept appointments from your department'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if appointment is in the same hospital as the doctor
        if appointment.hospital != doctor.hospital:
            return Response({
                'status': 'error',
                'message': 'You can only accept appointments from your hospital'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if appointment is pending
        if appointment.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending appointments can be accepted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if doctor is available at the appointment time
        appointment_date = appointment.appointment_date
        day_name = appointment_date.strftime('%a')  # Get 3-letter day name
        consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
        
        # Make the day check more flexible
        day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                    any(day_name.lower() in day.lower() for day in consultation_days)
                    
        if not day_matches and day_name not in consultation_days:
            return Response({
                'status': 'error',
                'message': f'You do not consult on {day_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if time is within consultation hours
        appointment_time = appointment_date.time()
        
        # Skip time check if consultation hours are not set
        if doctor.consultation_hours_start is not None and doctor.consultation_hours_end is not None:
            if not (doctor.consultation_hours_start <= appointment_time <= doctor.consultation_hours_end):
                return Response({
                    'status': 'error',
                    'message': f'Appointment time {appointment_time} is outside your consultation hours'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for overlapping appointments
        appointment_end = appointment_date + timezone.timedelta(minutes=doctor.appointment_duration)
        
        overlapping = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed', 'in_progress', 'scheduled', 'checking_in'],
            appointment_date__date=appointment_date.date(),  # Only check appointments on the same day
            appointment_date__gte=appointment_date - timezone.timedelta(minutes=doctor.appointment_duration),  # Start time is before or at the requested end time
            appointment_date__lt=appointment_end  # Start time is before the end of the requested slot
        )
        
        if overlapping.exists():
            return Response({
                'status': 'error',
                'message': 'You have overlapping appointments at this time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Accept the appointment
        try:
            appointment.approve(doctor)
            
            return Response({
                'status': 'success',
                'message': f'Successfully accepted appointment {appointment_id}',
                'appointment': AppointmentListSerializer(appointment).data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error accepting appointment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        import traceback
        error_msg = f"Error accepting appointment: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_consultation(request, appointment_id):
    """
    Allows a doctor to start the consultation for a confirmed appointment.
    This will change the status from confirmed to in_progress.
    """
    user = request.user
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the doctor is assigned to this appointment
        if appointment.doctor != doctor:
            return Response({
                'status': 'error',
                'message': 'You can only start consultations for appointments assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Start the consultation
        try:
            appointment.start_consultation(doctor)
            
            return Response({
                'status': 'success',
                'message': f'Successfully started consultation for appointment {appointment_id}',
                'appointment': AppointmentListSerializer(appointment).data
            })
        except DjangoValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error starting consultation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        import traceback
        error_msg = f"Error starting consultation: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_consultation(request, appointment_id):
    """
    Allows a doctor to complete the consultation for an in-progress appointment.
    This will change the status from in_progress to completed.
    Notes should be added separately using the add_doctor_notes endpoint.
    """
    user = request.user
    print("request.data", request.data)
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the doctor is assigned to this appointment
        if appointment.doctor != doctor:
            return Response({
                'status': 'error',
                'message': 'You can only complete consultations for appointments assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle notes if provided - notes are now handled here directly
        notes = request.data.get('notes', '')
        print("notes", notes)
        if notes:
            # Format the notes with proper timestamp and doctor attribution
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            formatted_note = f"\n\nDoctor's Notes ({timestamp}) - Dr. {doctor.user.get_full_name()}:\n{notes}"
            print("formatted_note", formatted_note)
            
            # Use direct SQL update to append notes without triggering validation
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE api_appointment SET notes = CONCAT(COALESCE(notes, ''), %s) WHERE appointment_id = %s",
                    [formatted_note, appointment_id]
                )
                print("Notes added successfully as part of consultation completion")
        
        # Complete the consultation - change status to completed
        try:
            # Apply status change directly with bypass_validation
            appointment.status = 'completed'
            appointment.completed_at = timezone.now()
            appointment.save(bypass_validation=True)
            
            # Refresh the appointment from the database to include the newly added notes
            appointment.refresh_from_db()
            
            return Response({
                'status': 'success',
                'message': f'Successfully completed consultation for appointment {appointment_id}',
                'appointment': AppointmentListSerializer(appointment).data
            })
        except DjangoValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        import traceback
        error_msg = f"Error completing consultation: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_doctor_notes(request, appointment_id):
    """
    Allows a doctor to add notes to an appointment without changing its status.
    This is a dedicated endpoint for adding medical notes during or after a consultation.
    """
    user = request.user
    print("ADD NOTES request.data:", request.data)
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
            print(f"Found appointment: {appointment.appointment_id} with status: {appointment.status}")
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the doctor is assigned to this appointment
        if appointment.doctor != doctor:
            return Response({
                'status': 'error',
                'message': 'You can only add notes to appointments assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the notes from the request
        notes = request.data.get('notes', '')
        if not notes:
            return Response({
                'status': 'error',
                'message': 'Notes cannot be empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add the notes to the appointment
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        
        # Prefix the note with the doctor's name and timestamp
        formatted_note = f"\n\nDoctor's Notes ({timestamp}) - Dr. {doctor.user.get_full_name()}:\n{notes}"
        print(f"Adding notes: {formatted_note[:50]}...")
        
        try:
            # Use direct update in the database to avoid validation
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE api_appointment SET notes = CONCAT(notes, %s) WHERE appointment_id = %s",
                    [formatted_note, appointment_id]
                )
                print("Notes added successfully using direct SQL update")
                
            # Refresh the appointment from the database
            appointment.refresh_from_db()
            
            return Response({
                'status': 'success',
                'message': 'Notes added successfully',
                'appointment': AppointmentListSerializer(appointment).data
            })
        except Exception as e:
            import traceback
            print(f"Error adding notes: {str(e)}\n{traceback.format_exc()}")
            return Response({
                'status': 'error',
                'message': f'Error adding notes: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        import traceback
        error_msg = f"Error adding doctor notes: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_appointment(request, appointment_id):
    """
    Allows a doctor or patient to cancel an appointment.
    This changes the status from 'pending' or 'confirmed' to 'cancelled'.
    """
    user = request.user
    print("request.data", request.data)
    
    try:
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permission to cancel
        # User must be either the patient, the assigned doctor, or hospital admin
        is_patient = appointment.patient == user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        is_hospital_admin = hasattr(user, 'hospital_admin_profile') and appointment.hospital == user.hospital_admin_profile.hospital
        
        if not (is_patient or is_doctor or is_hospital_admin):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to cancel this appointment'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if appointment can be cancelled
        if appointment.status not in ['pending', 'confirmed']:
            return Response({
                'status': 'error',
                'message': f'Cannot cancel appointment with status {appointment.status}. Only pending or confirmed appointments can be cancelled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cancellation reason
        cancellation_reason = request.data.get('cancellation_reason', '')
        if not cancellation_reason:
            return Response({
                'status': 'error',
                'message': 'Cancellation reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set the user type who cancelled
        cancelled_by_type = 'doctor' if is_doctor else 'patient' if is_patient else 'admin'
        
        # Update appointment status and add cancellation info
        try:
            # Use direct SQL update to avoid validation issues
            from django.db import connection
            with connection.cursor() as cursor:
                # Update appointment status and cancellation details
                cursor.execute(
                    """
                    UPDATE api_appointment 
                    SET status = 'cancelled', 
                        cancellation_reason = %s, 
                        cancelled_at = %s 
                    WHERE appointment_id = %s
                    """,
                    [cancellation_reason, timezone.now(), appointment_id]
                )
                print(f"Appointment {appointment_id} cancelled successfully")
            
            # Refresh appointment from database
            appointment.refresh_from_db()
            
            # Send cancellation notification to the patient
            try:
                # Create email notification
                AppointmentNotification.objects.create(
                    appointment=appointment,
                    notification_type='email',
                    event_type='appointment_cancelled',
                    recipient=appointment.patient,
                    subject=f"Appointment Cancelled - {appointment.appointment_id}",
                    message=(
                        f"Dear {appointment.patient.get_full_name()},\n\n"
                        f"Your appointment ({appointment.appointment_id}) scheduled for "
                        f"{appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')} "
                        f"has been cancelled by {cancelled_by_type}.\n\n"
                        f"Reason: {cancellation_reason}\n\n"
                        f"Please contact us if you need to reschedule or have any questions."
                    ),
                    template_name='appointment_cancelled'
                )
                
                # Create SMS notification if patient has phone number
                if appointment.patient.phone:
                    AppointmentNotification.objects.create(
                        appointment=appointment,
                        notification_type='sms',
                        event_type='appointment_cancelled',
                        recipient=appointment.patient,
                        subject=f"Appt Cancelled: {appointment.appointment_id}",
                        message=(
                            f"Your appointment on {appointment.appointment_date.strftime('%b %d')} "
                            f"has been cancelled. Reason: {cancellation_reason[:50]}"
                        )
                    )
                
                # If cancelled by patient, notify the doctor (if assigned)
                if is_patient and appointment.doctor:
                    AppointmentNotification.objects.create(
                        appointment=appointment,
                        notification_type='email',
                        event_type='appointment_cancelled',
                        recipient=appointment.doctor.user,
                        subject=f"Patient Cancelled Appointment - {appointment.appointment_id}",
                        message=(
                            f"Dear Dr. {appointment.doctor.user.get_full_name()},\n\n"
                            f"Your appointment ({appointment.appointment_id}) with {appointment.patient.get_full_name()} "
                            f"scheduled for {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')} "
                            f"has been cancelled by the patient.\n\n"
                            f"Reason: {cancellation_reason}"
                        ),
                        template_name='appointment_cancelled_doctor'
                    )
            except Exception as e:
                print(f"Error sending cancellation notifications: {str(e)}")
                # Continue even if notification fails
            
            return Response({
                'status': 'success',
                'message': f'Appointment {appointment_id} cancelled successfully',
                'appointment': AppointmentListSerializer(appointment).data
            })
            
        except Exception as e:
            print(f"Error cancelling appointment: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Error cancelling appointment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        import traceback
        error_msg = f"Error processing cancellation: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_appointment_no_show(request, appointment_id):
    """
    Allows a doctor to mark a patient as 'no-show' for an appointment.
    This changes the status from 'confirmed' to 'no_show'.
    Only doctors can mark appointments as no-show.
    """
    user = request.user
    print("request.data", request.data)
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'Only doctors can mark appointments as no-show'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Find the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the doctor is assigned to this appointment
        if appointment.doctor != doctor:
            return Response({
                'status': 'error',
                'message': 'You can only mark no-show for appointments assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if appointment can be marked as no-show
        if appointment.status != 'confirmed':
            return Response({
                'status': 'error',
                'message': f'Cannot mark no-show for appointment with status {appointment.status}. Only confirmed appointments can be marked as no-show.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure appointment date is in the past
        if appointment.appointment_date > timezone.now():
            return Response({
                'status': 'error',
                'message': 'Cannot mark no-show for future appointments'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Optional notes about no-show
        notes = request.data.get('notes', '')
        
        try:
            # Add no-show notes if provided
            if notes:
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                no_show_note = f"\n\nNo-Show Note ({timestamp}) - Dr. {doctor.user.get_full_name()}:\n{notes}"
                
                # Append notes using direct SQL
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE api_appointment SET notes = CONCAT(notes, %s) WHERE appointment_id = %s",
                        [no_show_note, appointment_id]
                    )
            
            # Update appointment status to no_show
            appointment.status = 'no_show'
            appointment.save(bypass_validation=True)
            
            # Send no-show notification to the patient
            try:
                # Create email notification
                AppointmentNotification.objects.create(
                    appointment=appointment,
                    notification_type='email',
                    event_type='appointment_no_show',
                    recipient=appointment.patient,
                    subject=f"Missed Appointment - {appointment.appointment_id}",
                    message=(
                        f"Dear {appointment.patient.get_full_name()},\n\n"
                        f"We noticed you missed your appointment ({appointment.appointment_id}) scheduled for "
                        f"{appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                        f"Please contact us to reschedule if needed. "
                        f"Regular attendance at scheduled appointments is important for your care.\n\n"
                        f"If you have any questions or need assistance, please don't hesitate to reach out."
                    ),
                    template_name='appointment_no_show'
                )
                
                # Create SMS notification if patient has phone number
                if appointment.patient.phone:
                    AppointmentNotification.objects.create(
                        appointment=appointment,
                        notification_type='sms',
                        event_type='appointment_no_show',
                        recipient=appointment.patient,
                        subject=f"Missed Appt: {appointment.appointment_id}",
                        message=(
                            f"We noticed you missed your appointment on "
                            f"{appointment.appointment_date.strftime('%b %d')}. "
                            f"Please call to reschedule."
                        )
                    )
            except Exception as e:
                print(f"Error sending no-show notifications: {str(e)}")
                # Continue even if notification fails
                
            return Response({
                'status': 'success',
                'message': f'Appointment {appointment_id} marked as no-show',
                'appointment': AppointmentListSerializer(appointment).data
            })
            
        except Exception as e:
            print(f"Error marking appointment as no-show: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Error marking appointment as no-show: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        import traceback
        error_msg = f"Error processing no-show request: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription(request, appointment_id=None):
    """
    Create new prescriptions for a patient based on an appointment.
    Doctors can prescribe multiple medications in a single request.
    
    Request body format:
    {
        "appointment_id": "APT-ABC123",  (optional if provided in URL)
        "medications": [
            {
                "medication_name": "Amoxicillin",
                "strength": "500 mg",
                "form": "capsule",
                "route": "oral",
                "dosage": "1 capsule",
                "frequency": "every 8 hours",
                "start_date": "2023-05-01",  (optional, defaults to today)
                "end_date": "2023-05-10",    (optional)
                "duration": "10 days",       (optional)
                "patient_instructions": "Take with food",  (optional)
                "pharmacy_instructions": "",  (optional)
                "indication": "Bacterial infection",  (optional)
                "refills_authorized": 0,  (optional, defaults to 0)
                "pharmacy_name": ""  (optional)
            },
            {
                // Additional medications...
            }
        ]
    }
    """
    user = request.user
    
    try:
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'You are not registered as a doctor in the system'
            }, status=status.HTTP_403_FORBIDDEN)
        
        doctor = user.doctor_profile
        
        # Get appointment_id from URL parameter or request data
        if not appointment_id:
            appointment_id = request.data.get('appointment_id')
        
        # Prepare data for validation
        data = {
            'appointment_id': appointment_id,
            'medications': request.data.get('medications', [])
        }
        
        # Validate the data
        serializer = PrescriptionSerializer(data=data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the doctor is assigned to this appointment
        if appointment.doctor != doctor:
            return Response({
                'status': 'error',
                'message': 'You can only prescribe medications for appointments assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create patient's medical record
        medical_record, created = MedicalRecord.objects.get_or_create(
            user=appointment.patient,
            defaults={
                'hpn': f"PHN-{appointment.patient.id}"
            }
        )
        
        # Create medications
        created_medications = []
        for med_data in serializer.validated_data['medications']:
            # Look for matching catalog entry (optional)
            catalog_entry = None
            if 'generic_name' in med_data:
                catalog_entries = MedicationCatalog.objects.filter(
                    generic_name__iexact=med_data.get('generic_name')
                )
                if catalog_entries.exists():
                    catalog_entry = catalog_entries.first()
            
            # Convert string dates to datetime objects
            start_date = timezone.now().date()
            if 'start_date' in med_data:
                start_date = datetime.strptime(med_data['start_date'], '%Y-%m-%d').date()
            
            end_date = None
            if 'end_date' in med_data:
                end_date = datetime.strptime(med_data['end_date'], '%Y-%m-%d').date()
            
            # Create the medication
            medication = Medication.objects.create(
                medical_record=medical_record,
                catalog_entry=catalog_entry,
                prescribed_by=doctor,
                appointment=appointment,  # Store the appointment reference
                medication_name=med_data['medication_name'],
                generic_name=med_data.get('generic_name', ''),
                strength=med_data['strength'],
                form=med_data['form'],
                route=med_data['route'],
                dosage=med_data['dosage'],
                frequency=med_data['frequency'],
                start_date=start_date,
                end_date=end_date,
                duration=med_data.get('duration', ''),
                patient_instructions=med_data.get('patient_instructions', ''),
                pharmacy_instructions=med_data.get('pharmacy_instructions', ''),
                indication=med_data.get('indication', ''),
                refills_authorized=med_data.get('refills_authorized', 0),
                refills_remaining=med_data.get('refills_authorized', 0),
                pharmacy_name=med_data.get('pharmacy_name', ''),
                status='active'
            )
            
            created_medications.append(medication)
        
        # Add a note to the appointment about the prescription
        medication_names = ", ".join([m.medication_name for m in created_medications])
        prescription_note = f"\n\nPrescription ({timezone.now().strftime('%Y-%m-%d %H:%M')}) - Dr. {doctor.user.get_full_name()}:\n"
        prescription_note += f"Prescribed: {medication_names}"
        
        # Use direct SQL update to append notes without triggering validation
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE api_appointment SET notes = CONCAT(COALESCE(notes, ''), %s) WHERE appointment_id = %s",
                [prescription_note, appointment_id]
            )
        
        # Return the created medications
        return Response({
            'status': 'success',
            'message': f'Successfully created {len(created_medications)} prescriptions',
            'medications': MedicationSerializer(created_medications, many=True).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        error_msg = f"Error creating prescriptions: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_prescriptions(request, appointment_id=None):
    """
    Get prescriptions for a patient based on an appointment.
    Doctors can see prescriptions for appointments assigned to them.
    Patients can see their own prescriptions.
    """
    user = request.user
    
    try:
        # If appointment_id is provided, get prescriptions for that appointment
        if appointment_id:
            try:
                appointment = Appointment.objects.get(appointment_id=appointment_id)
            except Appointment.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Appointment with ID {appointment_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            is_patient = appointment.patient == user
            is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
            is_hospital_admin = hasattr(user, 'hospital_admin') and appointment.hospital == user.hospital_admin.hospital
            
            if not (is_patient or is_doctor or is_hospital_admin):
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to view these prescriptions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get medical record for the patient
            try:
                medical_record = MedicalRecord.objects.get(user=appointment.patient)
            except MedicalRecord.DoesNotExist:
                return Response({
                    'status': 'success',
                    'message': 'No medical record found for this patient',
                    'medications': []
                }, status=status.HTTP_200_OK)
            
            # Get medications for this medical record
            medications = Medication.objects.filter(
                medical_record=medical_record
            ).order_by('-start_date')
            
            return Response({
                'status': 'success',
                'appointment_id': appointment_id,
                'patient_name': appointment.patient.get_full_name(),
                'medications': MedicationSerializer(medications, many=True).data
            }, status=status.HTTP_200_OK)
        
        """# If no appointment_id is provided, get prescriptions for the user
        # based on their role
        if hasattr(user, 'doctor_profile'):
            # Doctor: Get all prescriptions they have prescribed
            doctor = user.doctor_profile
            medications = Medication.objects.filter(
                prescribed_by=doctor
            ).order_by('-start_date')
            
            return Response({
                'status': 'success',
                'medications': MedicationSerializer(medications, many=True).data
            }, status=status.HTTP_200_OK)
        else:"""
        # Patient: Get their own prescriptions
        try:
            medical_record = MedicalRecord.objects.get(user=user)
        except MedicalRecord.DoesNotExist:
            return Response({
                'status': 'success',
                'message': 'No medical record found',
                'medications': []
            }, status=status.HTTP_200_OK)
        
        medications = Medication.objects.filter(
            medical_record=medical_record
        ).order_by('-start_date')
        
        return Response({
            'status': 'success',
            'medications': MedicationSerializer(medications, many=True).data
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving prescriptions: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_prescriptions(request, appointment_id):
    """
    Get prescriptions specifically for a given appointment.
    This differs from patient_prescriptions as it only returns medications
    that were prescribed during this specific appointment.
    
    Doctors can see prescriptions for appointments assigned to them.
    Patients can see prescriptions for their own appointments.
    """
    user = request.user
    
    try:
        # Get the appointment
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Appointment with ID {appointment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        is_patient = appointment.patient == user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        is_hospital_admin = hasattr(user, 'hospital_admin') and appointment.hospital == user.hospital_admin.hospital
        
        if not (is_patient or is_doctor or is_hospital_admin):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view these prescriptions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get medications specifically for this appointment
        medications = Medication.objects.filter(
            appointment=appointment
        ).order_by('-created_at')
        
        return Response({
            'status': 'success',
            'appointment_id': appointment_id,
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}" if appointment.doctor else None,
            'appointment_date': appointment.appointment_date,
            'medications': MedicationSerializer(medications, many=True).data,
            'medication_count': medications.count()
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving appointment prescriptions: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return Response({
            'status': 'error',
            'message': str(e),
            'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)