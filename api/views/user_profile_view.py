"""
User Profile API View
Returns current user information including registry_role for RBAC
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.models.user.role import Role


class UserProfileView(APIView):
    """
    Get current user profile information.
    Includes registry_role and permissions for RBAC in admin dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user profile with registry_role"""
        user = request.user

        # Serialize registry_role if it exists
        registry_role_data = None
        if user.registry_role:
            registry_role_data = {
                'id': user.registry_role.id,
                'name': user.registry_role.name,
                'role_type': user.registry_role.role_type,
                'permissions': user.registry_role.permissions,
                'description': user.registry_role.description,
            }

        profile_data = {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip(),  # Frontend expects full_name
            'first_name': user.first_name,  # Keep for backwards compatibility
            'last_name': user.last_name,  # Keep for backwards compatibility
            'hpn': user.hpn,  # Health Plan Number
            'role': user.role,  # Old CharField role
            'registry_role': registry_role_data,  # New ForeignKey RBAC role
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'has_completed_onboarding': user.has_completed_onboarding,  # Required for onboarding check
            'gender': user.gender,
            'date_of_birth': user.date_of_birth,
            'phone': user.phone,
            'country': user.country,
            'state': user.state,
            'city': user.city,
            'is_verified': user.is_verified,
            'otp_required_for_login': user.otp_required_for_login,  # Include OTP status
        }

        return Response(profile_data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update user profile with partial data"""
        user = request.user

        # Get the update data from request
        update_data = request.data

        # List of allowed fields that can be updated
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'gender',
            'date_of_birth', 'country', 'state', 'city',
            'otp_required_for_login',  # Allow OTP toggle
            'secondary_languages', 'custom_language',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'blood_group',
            'primary_language', 'communication_preference_email',
            'communication_preference_sms', 'communication_preference_phone',
            'marketing_emails_enabled'
        ]

        # Update only allowed fields
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)

        # Save the user
        user.save()

        # Return updated profile data (reuse the same serialization logic)
        registry_role_data = None
        if user.registry_role:
            registry_role_data = {
                'id': user.registry_role.id,
                'name': user.registry_role.name,
                'role_type': user.registry_role.role_type,
                'permissions': user.registry_role.permissions,
                'description': user.registry_role.description,
            }

        profile_data = {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'hpn': user.hpn,
            'role': user.role,
            'registry_role': registry_role_data,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'has_completed_onboarding': user.has_completed_onboarding,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth,
            'phone': user.phone,
            'country': user.country,
            'state': user.state,
            'city': user.city,
            'is_verified': user.is_verified,
            'otp_required_for_login': user.otp_required_for_login,  # Include OTP status in response
        }

        return Response(profile_data, status=status.HTTP_200_OK)
