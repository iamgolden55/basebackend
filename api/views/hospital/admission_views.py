# api/views/hospital/admission_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models

from api.models.medical.patient_admission import PatientAdmission
from api.models.medical.department import Department
from api.serializers import (
    PatientAdmissionSerializer, 
    PatientAdmissionListSerializer,
    PatientTransferSerializer,
    PatientDischargeSerializer
)

class PatientAdmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient admissions
    
    Provides endpoints for:
    - Standard CRUD operations
    - Admitting patients
    - Discharging patients
    - Transferring patients between departments
    - Emergency admission for unregistered patients
    - Converting temporary patients to registered users
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = PatientAdmission.objects.all()
    serializer_class = PatientAdmissionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'doctor':
            # Doctors see admissions they're attending or consulting on
            return PatientAdmission.objects.filter(
                models.Q(attending_doctor__user=user) | 
                models.Q(consulting_doctors__user=user)
            ).distinct()
        elif user.role in ['hospital_admin', 'nurse', 'staff']:
            # Hospital staff see admissions in their hospital
            return PatientAdmission.objects.filter(hospital__user=user)
        elif user.is_staff:
            # Admin users see all admissions
            return PatientAdmission.objects.all()
        else:
            # Regular users see their own admissions
            return PatientAdmission.objects.filter(patient=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PatientAdmissionListSerializer
        return PatientAdmissionSerializer
    
    @action(detail=True, methods=['post'])
    def admit(self, request, pk=None):
        """Admit a pending patient"""
        admission = self.get_object()
        
        try:
            admission.admit_patient()
            return Response({
                'message': 'Patient admitted successfully',
                'admission': PatientAdmissionSerializer(admission).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def discharge(self, request, pk=None):
        """Discharge a patient"""
        admission = self.get_object()
        serializer = PatientDischargeSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                admission.discharge_patient(
                    destination=serializer.validated_data.get('discharge_destination', ''),
                    summary=serializer.validated_data.get('discharge_summary', ''),
                    followup=serializer.validated_data.get('followup_instructions', '')
                )
                return Response({
                    'message': 'Patient discharged successfully',
                    'admission': PatientAdmissionSerializer(admission).data
                })
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Transfer a patient to another department"""
        admission = self.get_object()
        serializer = PatientTransferSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                department_id = serializer.validated_data.get('department_id')
                department = Department.objects.get(id=department_id)
                
                doctor_id = serializer.validated_data.get('doctor_id')
                doctor = None
                if doctor_id:
                    from api.models.medical_staff.doctor import Doctor
                    doctor = Doctor.objects.get(id=doctor_id)
                
                admission.transfer_patient(
                    new_department=department,
                    new_doctor=doctor,
                    is_icu=serializer.validated_data.get('is_icu_bed'),
                    reason=serializer.validated_data.get('reason', '')
                )
                
                return Response({
                    'message': 'Patient transferred successfully',
                    'admission': PatientAdmissionSerializer(admission).data
                })
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def emergency_admission(self, request):
        """
        Create an emergency admission for an unregistered patient
        """
        from api.utils.id_generators import generate_admission_id, generate_temp_patient_id
        
        # Get temporary patient details from request
        temp_patient_details = request.data.get('temp_patient_details', {})
        
        # Define required fields for emergency admission
        required_personal_fields = [
            'first_name', 'last_name', 'gender', 'phone_number', 'city',
            'emergency_contact', 'emergency_contact_name'
        ]
        required_medical_fields = [
            'chief_complaint', 'allergies'
        ]
        
        # Validate required personal information
        missing_personal_fields = [field for field in required_personal_fields 
                               if not temp_patient_details.get(field)]
        if missing_personal_fields:
            return Response({
                'error': f'Missing required personal information: {", ".join(missing_personal_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Validate required medical information
        missing_medical_fields = [field for field in required_medical_fields 
                              if not temp_patient_details.get(field)]
        if missing_medical_fields:
            return Response({
                'error': f'Missing required medical information: {", ".join(missing_medical_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check for either age or date_of_birth
        if not temp_patient_details.get('age') and not temp_patient_details.get('date_of_birth'):
            return Response({
                'error': 'Either age or date_of_birth must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate temporary ID
        temp_id = generate_temp_patient_id()
    
        # Create admission data
        admission_data = {
            'admission_id': generate_admission_id(),
            'hospital': request.data.get('hospital_id'),  # Use hospital instead of hospital_id
            'department': request.data.get('department_id'),  # Use department instead of department_id
            'status': 'pending',
            'admission_type': request.data.get('admission_type', 'emergency'),
            'priority': request.data.get('priority', 'urgent'),
            'reason_for_admission': request.data.get('reason_for_admission'),
            'attending_doctor_id': request.data.get('attending_doctor_id'),
            'is_registered_patient': False,
            'temp_patient_id': temp_id,
            'temp_patient_details': temp_patient_details,
            'registration_status': 'pending'
        }
    
        serializer = self.get_serializer(data=admission_data)
        serializer.is_valid(raise_exception=True)
        admission = serializer.save()
        
        # If bed assignment is needed immediately
        if request.data.get('assign_bed', False):
            try:
                admission.admit_patient()
            except Exception as e:
                # Continue without bed assignment if it fails
                pass
        
        return Response({
            'message': 'Emergency admission created successfully',
            'admission': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete_registration(self, request, pk=None):
        """
        Complete the registration for a temporary patient
        """
        admission = self.get_object()
        
        # Ensure this is a temporary patient
        if admission.is_registered_patient:
            return Response({
                'error': 'Patient is already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required fields
        required_fields = ['email', 'password', 'date_of_birth']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'error': f'Field {field} is required to complete registration'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user account
        try:
            user = admission.convert_to_registered_patient(request.data)
            serializer = self.get_serializer(admission)
            return Response({
                'message': 'Patient registration completed successfully',
                'admission': serializer.data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
