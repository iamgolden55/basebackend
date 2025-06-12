from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from api.models.medical.hospital import Hospital
from api.models.medical.hospital_registration import HospitalRegistration
from api.serializers import StaffSerializer, StaffCreationSerializer

class StaffManagementView(APIView):
    """
    View for managing hospital staff members
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get all staff members in the user's hospital
        """
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
                'status': 'error',
                'message': 'You must be registered with a hospital to view staff'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all staff members in the hospital using the model method
        staff_members = hospital.get_all_staff()
        
        # Serialize the staff members
        serializer = StaffSerializer(staff_members, many=True)
        
        return Response({
            'status': 'success',
            'total_staff': len(serializer.data),
            'staff_members': serializer.data
        })

    def post(self, request):
        """
        Create a new staff member (only for hospital admins)
        """
        user = request.user
        print('request.data', request.data)
        # Only allow hospital admins to create new staff
        if not hasattr(user, 'hospital_admin_profile'):
            return Response({
                'status': 'error',
                'message': 'Only hospital admins can create staff members'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Use the StaffCreationSerializer to validate and create the staff member
        serializer = StaffCreationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            staff_member = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Staff member created successfully',
                'staff_member': StaffSerializer(staff_member).data
            }, status=status.HTTP_201_CREATED)
        print('serializer.errors', serializer.errors)
        print('Sum went wrong in the serializer')
        return Response({
            'status': 'error',
            'message': 'Failed to create staff member',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Update staff member availability
        """
        user = request.user
        
        # Only allow staff members to update their own availability
        if not hasattr(user, 'doctor_profile'):
            return Response({
                'status': 'error',
                'message': 'Only doctors can update their availability'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Update doctor's availability
        user.doctor_profile.available_for_appointments = request.data.get('is_available', False)
        user.doctor_profile.save()
        
        return Response({
            'status': 'success',
            'message': 'Availability status updated successfully'
        })
    def delete(self, request, pk):
        """
        Delete a staff member (only for hospital admins)
        """
        user = request.user
        
        # Only allow hospital admins to delete staff members
        if not hasattr(user, 'hospital_admin_profile'):
            return Response({
                'status': 'error',
                'message': 'Only hospital admins can delete staff members'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Get the staff member to delete
        staff_member = get_user_model().objects.filter(
            primary_hospital=user.hospital_admin_profile.hospital,
            id=pk
        ).first()
        
        if not staff_member:
            return Response({
                'status': 'error',
                'message': 'Staff member not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Delete the staff member
        staff_member.delete()
        
        return Response({
            'status': 'success',
            'message': 'Staff member deleted successfully'
        })
        
    
