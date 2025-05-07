import logging
from datetime import datetime

from django.utils import timezone
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.models import Appointment, Doctor, HospitalRegistration
from api.models.medical.department import Department
from api.models.medical.appointment import AppointmentType
from api.serializers import AppointmentSerializer  # If you use it elsewhere in this file

from api.utils.location_utils import get_location_from_ip
from django.utils.dateparse import parse_date

# Logger setup
logger = logging.getLogger(__name__)

class DoctorAssignmentView(APIView):
    """
    API endpoint for doctor assignment based on department, hospital, and appointment details.
    This endpoint allows finding available time slots without exposing individual doctor names.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Log incoming request data for debugging
        print(f"DoctorAssignment received data: {request.data}")
        data = request.data
        
        try:
            # Extract data from request - accepting frontend parameter names
            # Fix: We're now using the variable names that match the frontend
            department_id = data.get('department')
            appointment_type = data.get('appointment_type')
            appointment_date = data.get('preferred_date')
            hospital_id = data.get('hospital')
            
            # These are additional parameters from frontend that we'll accept but not require
            chief_complaint = data.get('chief_complaint')
            priority = data.get('priority')
            preferred_language = data.get('preferred_language')
            
            print(f"Extracted fields: department={department_id}, "
                  f"appointment_type={appointment_type}, "
                  f"preferred_date={appointment_date}, "
                  f"hospital={hospital_id}, "
                  f"chief_complaint={chief_complaint}, "
                  f"priority={priority}, "
                  f"preferred_language={preferred_language}")
            
            # Validate required fields
            missing_fields = []
            if not department_id:
                missing_fields.append('department')
            if not appointment_type:
                missing_fields.append('appointment_type')
            if not appointment_date:
                missing_fields.append('preferred_date')
                
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"Validation error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse appointment date
            try:
                if isinstance(appointment_date, str):
                    # Convert to datetime if it's a string
                    parsed_date = parse_date(appointment_date)
                    if not parsed_date:
                        raise ValueError(f"Invalid date format: {appointment_date}")
                    appointment_date = parsed_date
                    print(f"Parsed preferred_date: {appointment_date}")
            except Exception as e:
                error_msg = f"Invalid date format: {str(e)}"
                print(f"Date parsing error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user's primary hospital if hospital_id is not provided
            if not hospital_id:
                print(f"No hospital provided, looking for hospitals for user {request.user.id}")
                
                # First try to get primary approved hospital
                hospital_registration = HospitalRegistration.objects.filter(
                    user=request.user, 
                    is_primary=True,
                    status='approved'
                ).first()
                
                if not hospital_registration:
                    # If no primary approved hospital, try to get any approved hospital
                    hospital_registration = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='approved'
                    ).first()
                
                if not hospital_registration:
                    # If no approved hospital, check if there are any pending registrations
                    pending_registration = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='pending'
                    ).exists()
                    
                    if pending_registration:
                        error_msg = 'You have pending hospital registrations. Please wait for approval or contact admin.'
                    else:
                        # Check if user has any hospital registrations at all
                        any_registration = HospitalRegistration.objects.filter(
                            user=request.user
                        ).exists()
                        
                        if any_registration:
                            error_msg = 'None of your hospital registrations are approved. Please contact admin.'
                        else:
                            error_msg = 'You are not registered with any hospital. Please register with a hospital first.'
                    
                    print(f"Hospital error: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                hospital_id = hospital_registration.hospital.id
                print(f"Using hospital: {hospital_id} ({hospital_registration.hospital.name})")
                
                # For debugging
                print(f"All hospital registrations for user {request.user.id}:")
                all_registrations = HospitalRegistration.objects.filter(user=request.user)
                for reg in all_registrations:
                    print(f"  - Hospital: {reg.hospital.name}, Primary: {reg.is_primary}, Status: {reg.status}")
            
            # Validate department exists in the hospital
            try:
                department = Department.objects.get(id=department_id)
                print(f"Found department: {department.name}")
            except Department.DoesNotExist:
                error_msg = f'Department not found with ID: {department_id}'
                print(f"Department error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate appointment type
            try:
                appointment_type_obj = AppointmentType.objects.get(id=appointment_type)
                print(f"Found appointment type: {appointment_type_obj.name}")
            except AppointmentType.DoesNotExist:
                # Try with lowercase ID or by name
                try:
                    # Try first by name match
                    appointment_type_obj = AppointmentType.objects.filter(
                        name__iexact=appointment_type
                    ).first()
                    
                    if not appointment_type_obj:
                        # Then try by ID case-insensitive
                        appointment_type_obj = AppointmentType.objects.filter(
                            id__iexact=appointment_type
                        ).first()
                        
                    if not appointment_type_obj:
                        raise AppointmentType.DoesNotExist()
                        
                    print(f"Found appointment type using alternative method: {appointment_type_obj.name}")
                except:
                    error_msg = f'Invalid appointment type: {appointment_type}'
                    print(f"Appointment type error: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Find available doctors in this department at this hospital
            doctors = Doctor.objects.filter(
                department_id=department_id,
                hospital_id=hospital_id,
                is_active=True,
                available_for_appointments=True
            )
            
            print(f"Found {doctors.count()} doctors in department {department_id} at hospital {hospital_id}")
            
            if not doctors.exists():
                error_msg = f'No doctors available in department {department.name}'
                print(f"Doctors error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find available time slots for the given date
            available_slots = []
            
            # Business hours (9am to 5pm)
            start_hour = 9
            end_hour = 17
            
            print(f"Generating time slots for date: {appointment_date}")
            
            # Generate all possible slots
            for hour in range(start_hour, end_hour):
                for minute in [0, 30]:  # 30-minute slots
                    slot_time = f"{hour:02d}:{minute:02d}"
                    
                    # Create a datetime for this slot
                    slot_datetime = datetime.combine(
                        appointment_date, 
                        datetime.strptime(slot_time, "%H:%M").time(),
                        tzinfo=timezone.get_current_timezone()
                    )
                    
                    # Skip slots in the past
                    if slot_datetime < timezone.now():
                        print(f"Skipping past time slot: {slot_time}")
                        continue
                    
                    # Check if any doctor is available at this time
                    slot_available = False
                    for doctor in doctors:
                        # Check if the doctor has consultation hours set
                        if doctor.consultation_hours_start is None or doctor.consultation_hours_end is None:
                            # If no consultation hours, assume standard working hours
                            is_working_hours = start_hour <= slot_datetime.hour < end_hour
                        else:
                            # Use the doctor's defined hours
                            doctor_time = slot_datetime.time()
                            is_working_hours = doctor.consultation_hours_start <= doctor_time <= doctor.consultation_hours_end
                        
                        # Check day of week
                        day_name = slot_datetime.strftime('%a')  # Get 3-letter day name
                        if doctor.consultation_days:
                            consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
                            # Make the day check more flexible
                            day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                                         any(day_name.lower() in day.lower() for day in consultation_days) or \
                                         day_name in consultation_days
                        else:
                            # If no consultation days specified, assume all days
                            day_matches = True
                        
                        if not (is_working_hours and day_matches):
                            # Skip this doctor if not working at this time
                            continue
                        
                        # Check if the doctor has an existing appointment at this time
                        conflicting_appointment = Appointment.objects.filter(
                            doctor=doctor,
                            appointment_date=slot_datetime,
                            status__in=['scheduled', 'confirmed', 'checking_in', 'pending', 'in_progress']
                        ).exists()
                        
                        if not conflicting_appointment:
                            # This doctor is available at this time slot
                            slot_available = True
                            print(f"Doctor {doctor.id} is available at {slot_time}")
                            break
                    
                    if slot_available:
                        available_slots.append({
                            'time': slot_time,
                            'datetime': slot_datetime.isoformat()
                        })
            
            print(f"Generated {len(available_slots)} available time slots")
            
            response_data = {
                'status': 'success',
                'department': {
                    'id': department.id,
                    'name': department.name
                },
                'appointment_type': {
                    'id': appointment_type_obj.id,
                    'name': appointment_type_obj.name
                },
                'preferred_date': appointment_date.isoformat() if hasattr(appointment_date, 'isoformat') else appointment_date,
                'available_slots': available_slots
            }
            
            print(f"Returning {len(available_slots)} available slots")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_msg = f"Error in doctor assignment: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            logger.error(error_msg)
            return Response({
                'status': 'error',
                'message': str(e),
                'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
