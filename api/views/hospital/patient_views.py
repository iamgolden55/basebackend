# api/views/hospital/patient_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from api.models.user.custom_user import CustomUser
from api.models.medical.hospital_registration import HospitalRegistration

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_patients(request):
    """
    Search for patients by HPN number
    Only returns patients registered with the current user's hospital
    """
    hpn_query = request.GET.get('hpn', '').strip()
    
    if not hpn_query:
        return Response({
            'error': 'HPN parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Remove spaces from the query for searching
    hpn_query_clean = hpn_query.replace(' ', '')
    
    # Get the current user's hospital
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
    
    # Search for patients registered with this hospital
    # Using icontains for partial matching
    patients = CustomUser.objects.filter(
        hospital_registrations__hospital=hospital,
        hospital_registrations__status='approved',
        hpn__icontains=hpn_query_clean
    ).distinct()[:10]  # Limit to 10 results
    
    # Format the response
    results = []
    for patient in patients:
        # Calculate age if date_of_birth is available
        age = None
        if patient.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )
        
        results.append({
            'id': patient.id,
            'hpn': patient.hpn,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'email': patient.email,
            'gender': patient.gender,
            'age': age,
            'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'phone': patient.phone,
            'city': patient.city
        })
    
    return Response(results)
