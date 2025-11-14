"""
Stream Chat token generation for secure authentication
"""
import os
import jwt
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# TODO: Add this to your environment variables
STREAM_API_SECRET = os.getenv('STREAM_API_SECRET', 'your-stream-api-secret-here')
STREAM_API_KEY = os.getenv('STREAM_API_KEY', 'your-stream-api-key-here')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_stream_token(request):
    """
    Generate Stream Chat token for the authenticated user
    """
    try:
        user = request.user
        
        # Use HPN as the Stream Chat user ID
        user_id = user.hpn if hasattr(user, 'hpn') else str(user.id)
        
        # Create token payload
        payload = {
            'user_id': user_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,  # 1 hour expiration
        }
        
        # Generate JWT token using Stream's secret
        token = jwt.encode(payload, STREAM_API_SECRET, algorithm='HS256')
        
        # Return token and user info
        return Response({
            'token': token,
            'user_id': user_id,
            'api_key': STREAM_API_KEY,
            'user_data': {
                'id': user_id,
                'name': user.get_full_name() if hasattr(user, 'get_full_name') else f"{user.first_name} {user.last_name}",
                'email': user.email,
                'role': getattr(user, 'role', 'healthcare_staff'),
                'hospital_name': getattr(user, 'hospital_name', 'Unknown Hospital'),
                'department': getattr(user, 'department', 'General'),
                'hospital_id': getattr(user, 'hospital_id', None),
                'staff_id': getattr(user, 'staff_id', None),
                'specialization': getattr(user, 'specialization', None),
                'is_verified': getattr(user, 'is_verified', False),
                'profile_picture': getattr(user, 'profile_picture', None),
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to generate Stream Chat token',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hospital_users(request):
    """
    Get list of users in the same hospital for creating channels
    """
    try:
        user = request.user
        
        # Import your User model here
        from api.models import CustomUser
        
        # Get users in the same hospital (adjust query based on your model)
        hospital_users = CustomUser.objects.filter(
            hospital_id=getattr(user, 'hospital_id', None)
        ).exclude(id=user.id).values(
            'hpn', 'first_name', 'last_name', 'email', 'role', 
            'department', 'specialization', 'is_verified'
        )[:50]  # Limit results
        
        # Format for Stream Chat
        users_list = []
        for u in hospital_users:
            users_list.append({
                'id': u['hpn'],
                'name': f"{u['first_name']} {u['last_name']}",
                'email': u['email'],
                'role': u['role'] or 'healthcare_staff',
                'department': u['department'] or 'General',
                'specialization': u['specialization'],
                'is_verified': u['is_verified'],
            })
        
        return Response({
            'users': users_list,
            'total': len(users_list)
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to get hospital users',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_department_channel(request):
    """
    Create a department channel with specified members
    """
    try:
        data = request.data
        channel_name = data.get('name')
        members = data.get('members', [])  # List of user HPNs
        department = data.get('department')
        description = data.get('description', '')
        
        if not channel_name:
            return Response({
                'error': 'Channel name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add current user to members
        user_id = request.user.hpn if hasattr(request.user, 'hpn') else str(request.user.id)
        if user_id not in members:
            members.append(user_id)
        
        # Create channel ID (can be customized)
        channel_id = f"dept_{department}_{int(time.time())}" if department else f"channel_{int(time.time())}"
        
        return Response({
            'channel_id': channel_id,
            'name': channel_name,
            'members': members,
            'department': department,
            'description': description,
            'created_by': user_id,
            'created_at': int(time.time())
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to create channel',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)