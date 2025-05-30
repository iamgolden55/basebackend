# api/views/hospital/emergency_admission.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

# Emergency admission endpoints to add to PatientAdmissionViewSet

@action(detail=False, methods=['post'])
def emergency_admission(self, request):
    """
    Create an emergency admission for an unregistered patient
    """
    from api.utils.id_generators import generate_admission_id, generate_temp_patient_id
    
    # Get temporary patient details from request
    temp_patient_details = request.data.get('temp_patient_details', {})
    
    if not temp_patient_details.get('first_name') or not temp_patient_details.get('last_name'):
        return Response({
            'error': 'First name and last name are required for emergency admission'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate temporary ID
    temp_id = generate_temp_patient_id()
    
    # Create admission data
    admission_data = {
        'admission_id': generate_admission_id(),
        'hospital_id': request.data.get('hospital_id'),
        'department_id': request.data.get('department_id'),
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
