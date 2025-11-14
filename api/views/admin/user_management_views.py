from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.db import transaction
from api.permissions import IsPlatformAdmin
from api.models.user.role import Role
from api.models.user.audit_log import AuditLog
import secrets
import string

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def list_admin_users(request):
    """
    List all admin users with their roles.
    GET /api/admin/users/
    """
    users = User.objects.filter(
        is_staff=True
    ).select_related('registry_role').order_by('-date_joined')

    data = [{
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': {
            'id': user.registry_role.id if user.registry_role else None,
            'name': user.registry_role.name if user.registry_role else None,
            'role_type': user.registry_role.role_type if user.registry_role else None,
        } if user.registry_role else None,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    } for user in users]

    return Response({'users': data})


@api_view(['POST'])
@permission_classes([IsPlatformAdmin])
def create_admin_user(request):
    """
    Create a new admin user and assign role.
    POST /api/admin/users/create/

    Body:
    {
        "email": "admin@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role_id": 1
    }
    """
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    role_id = request.data.get('role_id')

    # Validation
    if not all([email, first_name, last_name, role_id]):
        return Response(
            {'error': 'email, first_name, last_name, and role_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'User with this email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        role = Role.objects.get(id=role_id, is_active=True)
    except Role.DoesNotExist:
        return Response(
            {'error': 'Invalid role_id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate temporary password
    temp_password = ''.join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(12)
    )

    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                email=email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                registry_role=role
            )

            # Log action
            AuditLog.objects.create(
                user=request.user,
                action_type='create',
                resource_type='User',
                resource_id=str(user.id),
                description=f"Created admin user {email} with role {role.name}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # TODO: Send invitation email with temp password
            # send_admin_invitation_email(user, temp_password)

        return Response({
            'message': 'Admin user created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': {
                    'id': role.id,
                    'name': role.name,
                    'role_type': role.role_type,
                }
            },
            'temporary_password': temp_password  # Remove in production, send via email
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Failed to create user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsPlatformAdmin])
def update_user_role(request, user_id):
    """
    Update user's role.
    PATCH /api/admin/users/<user_id>/role/

    Body: {"role_id": 2}
    """
    try:
        user = User.objects.get(id=user_id, is_staff=True)
    except User.DoesNotExist:
        return Response(
            {'error': 'Admin user not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Prevent self-modification
    if user.id == request.user.id:
        return Response(
            {'error': 'Cannot change your own role'},
            status=status.HTTP_403_FORBIDDEN
        )

    role_id = request.data.get('role_id')
    if not role_id:
        return Response(
            {'error': 'role_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        new_role = Role.objects.get(id=role_id, is_active=True)
    except Role.DoesNotExist:
        return Response(
            {'error': 'Invalid role_id'},
            status=status.HTTP_404_NOT_FOUND
        )

    old_role = user.registry_role

    with transaction.atomic():
        user.registry_role = new_role
        user.save()

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action_type='update',
            resource_type='User',
            resource_id=str(user.id),
            description=f"Changed role from {old_role.name if old_role else 'None'} to {new_role.name}",
            metadata={
                'old_role_id': old_role.id if old_role else None,
                'new_role_id': new_role.id,
            },
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    return Response({
        'message': 'User role updated successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'role': {
                'id': new_role.id,
                'name': new_role.name,
                'role_type': new_role.role_type,
            }
        }
    })


@api_view(['POST'])
@permission_classes([IsPlatformAdmin])
def deactivate_user(request, user_id):
    """
    Deactivate an admin user.
    POST /api/admin/users/<user_id>/deactivate/
    """
    try:
        user = User.objects.get(id=user_id, is_staff=True)
    except User.DoesNotExist:
        return Response(
            {'error': 'Admin user not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Prevent self-deactivation
    if user.id == request.user.id:
        return Response(
            {'error': 'Cannot deactivate yourself'},
            status=status.HTTP_403_FORBIDDEN
        )

    with transaction.atomic():
        user.is_active = False
        user.save()

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action_type='update',
            resource_type='User',
            resource_id=str(user.id),
            description=f"Deactivated admin user {user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    return Response({'message': 'User deactivated successfully'})


@api_view(['POST'])
@permission_classes([IsPlatformAdmin])
def reactivate_user(request, user_id):
    """
    Reactivate a deactivated admin user.
    POST /api/admin/users/<user_id>/reactivate/
    """
    try:
        user = User.objects.get(id=user_id, is_staff=True)
    except User.DoesNotExist:
        return Response(
            {'error': 'Admin user not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    with transaction.atomic():
        user.is_active = True
        user.save()

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action_type='update',
            resource_type='User',
            resource_id=str(user.id),
            description=f"Reactivated admin user {user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    return Response({'message': 'User reactivated successfully'})


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def list_roles(request):
    """
    List all available roles.
    GET /api/admin/roles/
    """
    roles = Role.objects.filter(is_active=True).order_by('name')

    data = [{
        'id': role.id,
        'name': role.name,
        'role_type': role.role_type,
        'description': role.description,
        'permissions': role.permissions,
    } for role in roles]

    return Response({'roles': data})
