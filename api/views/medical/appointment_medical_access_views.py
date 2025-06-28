"""
🛡️ APPOINTMENT MEDICAL ACCESS VIEWS
API endpoints for time-limited medical record sharing during appointments
"""

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import logging

from api.models.medical.appointment import Appointment
from api.models.medical.appointment_medical_access import AppointmentMedicalAccess, MedicalAccessAuditLog
from api.models.medical.medical_record import MedicalRecord
from api.serializers import AppointmentSerializer, PatientMedicalRecordSerializer

logger = logging.getLogger(__name__)


class DoctorMedicalAccessRequestView(APIView):
    """
    🩺 Doctor requests access to patient medical records during appointment
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, appointment_id):
        """Request access to patient medical records"""
        try:
            # Get appointment and validate doctor access
            appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
            
            # Verify the requesting user is the assigned doctor or has medical staff permissions
            if not self._can_request_access(request.user, appointment):
                return Response({
                    'error': 'You do not have permission to request access to this patient\'s records'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get request parameters
            access_type = request.data.get('access_type', 'full_access')
            reason = request.data.get('reason', f'Medical consultation for appointment {appointment_id}')
            
            # Validate access type
            if access_type not in ['medical_records', 'documents', 'full_access']:
                return Response({
                    'error': 'Invalid access type. Must be: medical_records, documents, or full_access'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update access request
            with transaction.atomic():
                access_request = AppointmentMedicalAccess.request_access(
                    appointment=appointment,
                    doctor=request.user,
                    access_type=access_type,
                    reason=reason
                )
            
            # Log the request
            logger.info(
                f"Medical access requested - Appointment: {appointment_id}, "
                f"Doctor: {request.user.email}, Patient: {appointment.patient.email}, "
                f"Access Type: {access_type}"
            )
            
            return Response({
                'message': 'Medical record access request sent to patient',
                'access_request_id': access_request.id,
                'appointment_id': appointment_id,
                'access_type': access_type,
                'status': access_request.status,
                'requested_at': access_request.requested_at
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error requesting medical access: {str(e)}")
            return Response({
                'error': 'Failed to request medical access'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _can_request_access(self, user, appointment):
        """Check if user can request access to appointment medical records"""
        # Check if user is the assigned doctor
        if appointment.doctor and appointment.doctor.user == user:
            return True
        
        # Check if user has medical staff permissions
        if user.has_perm('api.can_view_patient_records'):
            return True
        
        # Check if user is a doctor in the same department
        if hasattr(user, 'doctor_profile'):
            doctor_profile = user.doctor_profile
            if doctor_profile.department == appointment.department:
                return True
        
        return False


class PatientMedicalAccessControlView(APIView):
    """
    👤 Patient controls medical record access during appointments
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all pending medical access requests for the patient"""
        try:
            # Get all pending access requests for this patient
            pending_requests = AppointmentMedicalAccess.objects.filter(
                patient=request.user,
                status='requested'
            ).select_related('appointment', 'doctor').order_by('-requested_at')
            
            requests_data = []
            for access_request in pending_requests:
                appointment = access_request.appointment
                doctor = access_request.doctor
                
                requests_data.append({
                    'access_request_id': access_request.id,
                    'appointment': {
                        'appointment_id': appointment.appointment_id,
                        'appointment_date': appointment.appointment_date,
                        'hospital': appointment.hospital.name,
                        'department': appointment.department.name,
                        'status': appointment.status
                    },
                    'doctor': {
                        'name': doctor.get_full_name(),
                        'email': doctor.email,
                    },
                    'access_type': access_request.access_type,
                    'request_reason': access_request.request_reason,
                    'requested_at': access_request.requested_at
                })
            
            return Response({
                'pending_requests': requests_data,
                'count': len(requests_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching medical access requests: {str(e)}")
            return Response({
                'error': 'Failed to fetch access requests'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, access_request_id):
        """Grant or deny medical record access"""
        try:
            # Get access request
            access_request = get_object_or_404(
                AppointmentMedicalAccess,
                id=access_request_id,
                patient=request.user,
                status='requested'
            )
            
            # Get action and parameters
            action = request.data.get('action')  # 'grant' or 'deny'
            duration_hours = int(request.data.get('duration_hours', 2))
            patient_notes = request.data.get('notes', '')
            
            if action not in ['grant', 'deny']:
                return Response({
                    'error': 'Action must be "grant" or "deny"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if duration_hours < 1 or duration_hours > 24:
                return Response({
                    'error': 'Duration must be between 1 and 24 hours'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                if action == 'grant':
                    access_request.grant_access(
                        duration_hours=duration_hours,
                        patient_notes=patient_notes
                    )
                    message = f'Medical record access granted for {duration_hours} hours'
                else:
                    access_request.deny_access(reason=patient_notes)
                    message = 'Medical record access denied'
            
            # Log the action
            logger.info(
                f"Medical access {action} - Request: {access_request_id}, "
                f"Patient: {request.user.email}, "
                f"Doctor: {access_request.doctor.email}"
            )
            
            return Response({
                'message': message,
                'access_request_id': access_request_id,
                'status': access_request.status,
                'expires_at': access_request.expires_at,
                'action': action
            })
            
        except Exception as e:
            logger.error(f"Error processing medical access control: {str(e)}")
            return Response({
                'error': 'Failed to process access control'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, access_request_id):
        """Revoke previously granted access"""
        try:
            access_request = get_object_or_404(
                AppointmentMedicalAccess,
                id=access_request_id,
                patient=request.user,
                status='granted'
            )
            
            reason = request.data.get('reason', 'Access revoked by patient')
            
            with transaction.atomic():
                success = access_request.revoke_access(reason=reason)
            
            if success:
                logger.info(
                    f"Medical access revoked - Request: {access_request_id}, "
                    f"Patient: {request.user.email}"
                )
                
                return Response({
                    'message': 'Medical record access revoked successfully',
                    'access_request_id': access_request_id,
                    'revoked_at': access_request.revoked_at
                })
            else:
                return Response({
                    'error': 'Failed to revoke access'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error revoking medical access: {str(e)}")
            return Response({
                'error': 'Failed to revoke access'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorMedicalRecordAccessView(APIView):
    """
    🩺 Doctor accesses patient medical records during appointments
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, appointment_id):
        """Access patient medical records during appointment"""
        try:
            # Get appointment and validate access
            appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
            
            # Check if doctor has active access
            access_request = AppointmentMedicalAccess.get_active_access(
                appointment=appointment,
                doctor=request.user
            )
            
            if not access_request:
                return Response({
                    'error': 'No active access to patient medical records',
                    'message': 'Please request access from the patient first'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Track the access
            access_request.mark_accessed()
            
            response_data = {
                'appointment': {
                    'appointment_id': appointment.appointment_id,
                    'patient_name': appointment.patient.get_full_name(),
                    'appointment_date': appointment.appointment_date,
                    'status': appointment.status
                },
                'access_info': {
                    'access_type': access_request.access_type,
                    'granted_at': access_request.granted_at,
                    'expires_at': access_request.expires_at,
                    'time_remaining': access_request.time_remaining,
                    'access_count': access_request.access_count
                }
            }
            
            # Add medical records if permitted
            if access_request.can_access_medical_records:
                try:
                    medical_record = MedicalRecord.objects.get(user=appointment.patient)
                    response_data['medical_record'] = {
                        'hpn': medical_record.hpn,
                        'blood_type': medical_record.blood_type,
                        'allergies': medical_record.allergies,
                        'chronic_conditions': medical_record.chronic_conditions,
                        'emergency_contact_name': medical_record.emergency_contact_name,
                        'emergency_contact_phone': medical_record.emergency_contact_phone,
                        'is_high_risk': medical_record.is_high_risk,
                        'last_visit_date': medical_record.last_visit_date,
                        'comorbidity_count': medical_record.comorbidity_count,
                        'medication_count': medical_record.medication_count,
                        'care_plan_complexity': medical_record.care_plan_complexity
                    }
                except MedicalRecord.DoesNotExist:
                    response_data['medical_record'] = None
            
            # Add document access info if permitted
            if access_request.can_access_documents:
                from api.models.secure_documents import SecureDocument
                
                patient_documents = SecureDocument.objects.filter(
                    user=appointment.patient,
                    is_active=True
                ).values('file_id', 'original_filename', 'file_type', 'file_size', 'created_at')
                
                response_data['documents'] = list(patient_documents)
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error accessing medical records: {str(e)}")
            return Response({
                'error': 'Failed to access medical records'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appointment_access_status(request, appointment_id):
    """
    Get the current medical access status for an appointment
    """
    try:
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Check if user is patient or doctor for this appointment
        is_patient = appointment.patient == request.user
        is_doctor = (appointment.doctor and appointment.doctor.user == request.user) or \
                   hasattr(request.user, 'doctor_profile')
        
        if not (is_patient or is_doctor):
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            access_request = AppointmentMedicalAccess.objects.get(appointment=appointment)
            
            response_data = {
                'has_access_request': True,
                'status': access_request.status,
                'access_type': access_request.access_type,
                'requested_at': access_request.requested_at,
                'granted_at': access_request.granted_at,
                'expires_at': access_request.expires_at,
                'is_active': access_request.is_active,
                'time_remaining': access_request.time_remaining,
                'access_count': access_request.access_count
            }
            
            if is_patient:
                response_data['request_reason'] = access_request.request_reason
                response_data['doctor_name'] = access_request.doctor.get_full_name()
            
        except AppointmentMedicalAccess.DoesNotExist:
            response_data = {
                'has_access_request': False,
                'can_request_access': is_doctor and appointment.status in ['confirmed', 'in_progress']
            }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting access status: {str(e)}")
        return Response({
            'error': 'Failed to get access status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_active_accesses(request):
    """
    Get all active medical accesses for a patient
    """
    try:
        active_accesses = AppointmentMedicalAccess.objects.filter(
            patient=request.user,
            status='granted'
        ).select_related('appointment', 'doctor')
        
        accesses_data = []
        for access in active_accesses:
            if access.is_active:  # This will auto-expire if needed
                appointment = access.appointment
                
                accesses_data.append({
                    'access_id': access.id,
                    'appointment': {
                        'appointment_id': appointment.appointment_id,
                        'appointment_date': appointment.appointment_date,
                        'hospital': appointment.hospital.name,
                        'department': appointment.department.name,
                        'status': appointment.status
                    },
                    'doctor': {
                        'name': access.doctor.get_full_name(),
                        'email': access.doctor.email
                    },
                    'access_type': access.access_type,
                    'granted_at': access.granted_at,
                    'expires_at': access.expires_at,
                    'time_remaining': access.time_remaining,
                    'access_count': access.access_count,
                    'last_accessed_at': access.last_accessed_at
                })
        
        return Response({
            'active_accesses': accesses_data,
            'count': len(accesses_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting patient active accesses: {str(e)}")
        return Response({
            'error': 'Failed to get active accesses'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)