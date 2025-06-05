# api/views/medical_staff/doctor_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from api.models.medical_staff.doctor import Doctor
from api.models.medical.hospital_registration import HospitalRegistration
from api.serializers import DoctorSerializer

class DoctorListView(APIView):
    """
    List all doctors in the current user's hospital
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        hospital = None
        
        # Check if user is a hospital admin
        if hasattr(user, 'hospital_admin_profile'):
            hospital = user.hospital_admin_profile.hospital
        # Check if user is staff at a hospital
        elif user.role in ['doctor', 'nurse', 'staff', 'hospital_admin']:
            # Get the hospital from hospital registrations
            registration = HospitalRegistration.objects.filter(
                user=user,
                status='approved'
            ).first()
            if registration:
                hospital = registration.hospital
        
        if not hospital:
            return Response({
                'error': 'User is not associated with any hospital'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all doctors in this hospital
        doctors = Doctor.objects.filter(
            hospital=hospital,
            is_active=True
        ).select_related('user')
        
        # Format the response
        results = []
        for doctor in doctors:
            results.append({
                'id': doctor.id,
                'user': {
                    'first_name': doctor.user.first_name,
                    'last_name': doctor.user.last_name,
                    'email': doctor.user.email
                },
                'specialization': doctor.specialization,
                'license_number': doctor.medical_license_number,
                'is_available': doctor.available_for_appointments
            })
        
        return Response(results)
