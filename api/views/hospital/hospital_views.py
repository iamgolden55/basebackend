import os
import logging
import traceback
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from rest_framework import generics, status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import ValidationError

from api.models import (
    Hospital, HospitalRegistration, CustomUser, Appointment, Doctor
)
from api.models.medical.appointment_notification import AppointmentNotification
from api.models.medical.department import Department
from api.models.medical.appointment import AppointmentType
from api.serializers import (
    HospitalRegistrationSerializer, HospitalSerializer, HospitalLocationSerializer,
    NearbyHospitalSerializer, AppointmentSerializer, AppointmentListSerializer,
    HospitalAdminRegistrationSerializer, ExistingUserToAdminSerializer,
    AppointmentCancelSerializer, AppointmentRescheduleSerializer,
    AppointmentApproveSerializer, AppointmentReferSerializer
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
        if hasattr(user, 'is_hospital_admin') and user.is_hospital_admin:
            # For hospital admins: show all registrations for their hospital
            return HospitalRegistration.objects.filter(
                hospital=user.hospital
            ).select_related('user', 'hospital')
        else:
            # For regular users: show their own registrations
            return HospitalRegistration.objects.filter(
                user=user
            ).select_related('user', 'hospital')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        if not serializer.data:
            return Response({
                "message": "No registrations found! 🔍",
                "hint": "Users need to register first using /api/hospitals/register/"
            }, status=status.HTTP_200_OK)
            
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
            is_hospital_admin = hasattr(user, 'hospital_admin') and appointment.hospital == user.hospital_admin.hospital
            
            if not (is_patient or is_doctor or is_hospital_admin):
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
            raise ValidationError("Cannot create appointments in the past.")
        
        # No fee handling needed anymore - removing all fee-related code
        
        hospital = serializer.validated_data.get('hospital')
        department = serializer.validated_data.get('department')
        
        # Check if doctor_id is provided
        doctor = serializer.validated_data.get('doctor')
        
        # If no doctor provided or doctor is not available, find an available doctor
        if not doctor or not self._is_doctor_available(doctor, appointment_date):
            if doctor:
                print(f"Doctor {doctor.id} is not available at {appointment_date}")
            else:
                print(f"No doctor specified, finding available doctor")
            
            # Find available doctors from the user's hospital
            try:
                from django.db.models import Q
                available_doctors = Doctor.objects.filter(
                    Q(department=department),
                    Q(hospital=hospital),
                    Q(is_active=True),
                    Q(available_for_appointments=True)
                )
                
                print(f"Found {available_doctors.count()} potential doctors in department {department.id} at hospital {hospital.id}")
                
                # Try to find an available doctor
                doctor_found = False
                for doc in available_doctors:
                    if self._is_doctor_available(doc, appointment_date):
                        doctor = doc
                        serializer.validated_data['doctor'] = doctor
                        print(f"Found available doctor: {doctor.id}")
                        doctor_found = True
                        break
                
                if not doctor_found:
                    print("No available doctors found at the specified time")
                    raise ValidationError("No doctors available at the requested time. Please choose a different time or department.")
            except Exception as e:
                print(f"Error finding available doctor: {str(e)}")
                raise ValidationError(f"Error finding available doctor: {str(e)}")
        
        # Save the appointment - no need to set fee-related fields
        appointment = serializer.save(patient=self.request.user)
        
        # Send confirmation (with error handling)
        try:
            self._send_appointment_confirmation(appointment)
        except Exception as e:
            logger.error(f"Failed to send appointment confirmation: {e}")
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
    
    data = [{"id": dept.id, "name": dept.name, "code": dept.code} for dept in departments]
    return Response({
        'status': 'success',
        'departments': data
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
