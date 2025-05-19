# api/views/auth/hospital_admin_password.py

import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.models.medical.hospital_auth import HospitalAdmin

logger = logging.getLogger(__name__)

CustomUser = get_user_model()

class HospitalAdminPasswordChangeView(APIView):
    """
    Endpoint for hospital administrators to change their password.
    This is required after initial account creation and can be used later for routine password changes.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Ensure the user is a hospital admin
        if request.user.role != 'hospital_admin':
            return Response({
                "status": "error",
                "message": "Only hospital administrators can use this endpoint."
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Validate request data
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return Response({
                "status": "error",
                "message": "All password fields are required."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check that new passwords match
        if new_password != confirm_password:
            return Response({
                "status": "error",
                "message": "New passwords do not match."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Validate current password
        user = request.user
        if not user.check_password(current_password):
            return Response({
                "status": "error",
                "message": "Current password is incorrect."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Validate new password requirements
        if len(new_password) < 8:
            return Response({
                "status": "error",
                "message": "Password must be at least 8 characters long."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Basic password complexity requirements
        has_upper = any(c.isupper() for c in new_password)
        has_lower = any(c.islower() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)
        has_special = any(not c.isalnum() for c in new_password)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            return Response({
                "status": "error",
                "message": "Password must include uppercase, lowercase, digit, and special characters."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Perform the password change
        try:
            with transaction.atomic():
                # Update user password
                user.set_password(new_password)
                user.save()
                
                # Update hospital admin record
                try:
                    admin = HospitalAdmin.objects.get(user=user)
                    admin.password_change_required = False
                    admin.last_password_change = timezone.now()
                    admin.save()
                    
                    logger.info(f"Hospital admin password changed for {user.email}")
                    
                    return Response({
                        "status": "success",
                        "message": "Password changed successfully."
                    })
                    
                except HospitalAdmin.DoesNotExist:
                    logger.error(f"Hospital admin profile not found for user {user.email}")
                    return Response({
                        "status": "error",
                        "message": "Hospital admin profile not found."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred while changing your password."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
