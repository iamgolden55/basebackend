"""
Professional Registry Search Views

Public API for searching and verifying registered healthcare professionals.

SECURITY FEATURES:
- Rate limiting to prevent scraping/abuse
- SQL injection protection via Django ORM Q objects
- XSS protection via HTML escaping in serializer
- Input validation and sanitization
- No authentication required (public endpoint)
- Limited fields exposed (via PublicSerializer)
"""

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re

from api.models import PHBProfessionalRegistry
from api.professional_application_serializers import PHBProfessionalRegistryPublicSerializer


# Custom throttle classes for rate limiting
class SearchRateThrottle(AnonRateThrottle):
    """
    Rate limit: 20 searches per minute for anonymous users.
    Prevents scraping and abuse.
    """
    rate = '20/min'


class BurstSearchRateThrottle(AnonRateThrottle):
    """
    Burst rate limit: 100 searches per hour.
    Allows legitimate usage while preventing mass scraping.
    """
    rate = '100/hour'


# Input validation functions
def sanitize_search_query(query):
    """
    Sanitize search query to prevent injection attacks.

    - Strips leading/trailing whitespace
    - Removes special SQL characters
    - Limits length to 100 characters
    - HTML escapes the input
    """
    if not query:
        return ''

    # Strip whitespace
    query = query.strip()

    # Limit length
    if len(query) > 100:
        query = query[:100]

    # Remove potentially dangerous SQL characters
    # Allow: letters, numbers, spaces, hyphens, apostrophes (for names like O'Brien)
    query = re.sub(r"[^a-zA-Z0-9\s\-'.]", '', query)

    # HTML escape for XSS protection
    query = escape(query)

    return query


def validate_professional_type(professional_type):
    """
    Validate professional type against allowed choices.

    Returns None if invalid (fail-safe).
    """
    valid_types = [
        'pharmacist',
        'doctor',
        'nurse',
        'midwife',
        'dentist',
        'physiotherapist',
        'lab_technician',
        'radiographer',
        'optometrist',
        'psychologist',
    ]

    if professional_type and professional_type.lower() in valid_types:
        return professional_type.lower()

    return None


def validate_state(state):
    """
    Validate state against Nigerian states.

    Returns None if invalid (fail-safe).
    """
    nigerian_states = [
        'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue',
        'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu',
        'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi',
        'Kwara', 'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo',
        'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'Abuja', 'FCT'
    ]

    if state and state in nigerian_states:
        return state

    return None


class SearchResultsPagination(PageNumberPagination):
    """
    Custom pagination for search results.

    - 20 results per page (reasonable for search)
    - Max 100 per page (prevent abuse)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle, BurstSearchRateThrottle])
def search_professionals(request):
    """
    Public API endpoint for searching verified healthcare professionals.

    Query Parameters:
    - query (string): Search by name or PHB license number
    - professional_type (string): Filter by professional type
    - specialization (string): Filter by specialization
    - state (string): Filter by state/location
    - page (int): Page number for pagination (default: 1)
    - page_size (int): Results per page (default: 20, max: 100)

    Security:
    - Rate limited: 20/min, 100/hour
    - All inputs sanitized and validated
    - Django ORM prevents SQL injection
    - HTML escaped output (XSS protection)
    - No authentication required (public)

    Returns:
    {
        "count": 150,
        "next": "http://api.phb.ng/registry/search/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "phb_license_number": "PHB-PHARM-2024-12345",
                "full_name": "Dr. John Doe",
                "professional_type": "pharmacist",
                "specialization_safe": "Clinical Pharmacy",
                "license_status": "active",
                "city": "Lagos",
                "state": "Lagos",
                ...
            }
        ]
    }
    """
    try:
        # Extract and sanitize query parameters
        query = sanitize_search_query(request.GET.get('query', ''))
        professional_type = validate_professional_type(request.GET.get('professional_type', ''))
        specialization = sanitize_search_query(request.GET.get('specialization', ''))
        state = validate_state(request.GET.get('state', ''))

        # Start with active licenses only (public should only see active professionals)
        professionals = PHBProfessionalRegistry.objects.filter(
            license_status='active'
        ).select_related('user')  # Optimize query

        # Apply search query (name OR license number)
        if query:
            # Check if query looks like a license number (starts with PHB-)
            if query.upper().startswith('PHB-'):
                # Exact license number search
                professionals = professionals.filter(
                    phb_license_number__iexact=query
                )
            else:
                # Name search (first name OR last name OR middle name)
                # Using Q objects for complex queries (safe from SQL injection)
                professionals = professionals.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(middle_name__icontains=query)
                )

        # Apply professional type filter
        if professional_type:
            professionals = professionals.filter(
                professional_type=professional_type
            )

        # Apply specialization filter
        if specialization:
            professionals = professionals.filter(
                specialization__icontains=specialization
            )

        # Apply state filter
        if state:
            professionals = professionals.filter(
                state=state
            )

        # Order by most recently licensed first
        professionals = professionals.order_by('-license_issue_date', 'last_name', 'first_name')

        # Apply pagination
        paginator = SearchResultsPagination()
        result_page = paginator.paginate_queryset(professionals, request)

        # Serialize with public serializer (limited fields only)
        serializer = PHBProfessionalRegistryPublicSerializer(
            result_page,
            many=True,
            context={'request': request}
        )

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

    except ValidationError as e:
        return Response(
            {
                'error': 'Invalid input parameters',
                'details': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Search error: {str(e)}")

        return Response(
            {
                'error': 'An error occurred during search',
                'message': 'Please try again or contact support if the problem persists'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def verify_license(request, license_number):
    """
    Quick verification endpoint for a specific PHB license number.

    URL: /api/registry/verify/{license_number}/

    Returns single professional or 404.

    Security:
    - Rate limited: 20/min
    - Input sanitized
    - Public endpoint

    Example: /api/registry/verify/PHB-PHARM-2024-12345/
    """
    try:
        # Sanitize license number
        license_number = sanitize_search_query(license_number)

        if not license_number:
            return Response(
                {'error': 'License number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look up professional (active licenses only)
        professional = PHBProfessionalRegistry.objects.filter(
            phb_license_number__iexact=license_number,
            license_status='active'
        ).select_related('user').first()

        if not professional:
            return Response(
                {
                    'verified': False,
                    'message': 'No active professional found with this license number',
                    'license_number': license_number
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialize professional data
        serializer = PHBProfessionalRegistryPublicSerializer(
            professional,
            context={'request': request}
        )

        return Response({
            'verified': True,
            'professional': serializer.data
        })

    except Exception as e:
        print(f"Verification error: {str(e)}")

        return Response(
            {
                'error': 'An error occurred during verification',
                'message': 'Please try again or contact support'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_stats(request):
    """
    Get public statistics about the registry (no rate limit needed).

    URL: /api/registry/stats/

    Returns:
    {
        "total_active_professionals": 1250,
        "by_type": {
            "pharmacist": 450,
            "doctor": 320,
            "nurse": 280,
            ...
        },
        "by_state": {
            "Lagos": 420,
            "Abuja": 180,
            ...
        }
    }
    """
    try:
        # Count active professionals only
        active_professionals = PHBProfessionalRegistry.objects.filter(
            license_status='active'
        )

        total = active_professionals.count()

        # Count by professional type
        by_type = {}
        for prof_type in ['pharmacist', 'doctor', 'nurse', 'midwife', 'dentist',
                          'physiotherapist', 'lab_technician', 'radiographer']:
            count = active_professionals.filter(professional_type=prof_type).count()
            if count > 0:
                by_type[prof_type] = count

        # Count by state (top 10 states only)
        by_state = {}
        from django.db.models import Count
        top_states = active_professionals.values('state').annotate(
            count=Count('state')
        ).order_by('-count')[:10]

        for state_data in top_states:
            if state_data['state']:
                by_state[state_data['state']] = state_data['count']

        return Response({
            'total_active_professionals': total,
            'by_type': by_type,
            'by_state': by_state,
            'last_updated': 'real-time'
        })

    except Exception as e:
        print(f"Stats error: {str(e)}")

        return Response(
            {'error': 'Unable to retrieve statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def get_application_status(request, application_id):
    """
    Get the status of a professional application by ID.

    URL: /api/registry/application-status/{application_id}/

    Returns:
    {
        "status": "approved|pending|rejected",
        "license_number": "PHB-PHARM-2024-12345"  // If approved
        "reason": "..."  // If rejected
    }

    Security:
    - Rate limited: 20/min
    - Public endpoint (allows applicants to check status)
    - Only returns minimal info (status and license number)
    """
    try:
        # Sanitize application ID (should be a UUID)
        application_id = sanitize_search_query(application_id)

        if not application_id:
            return Response(
                {'error': 'Application ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look up the professional registry entry by application ID
        # The application_id in the URL is actually the PHBProfessionalApplication.id
        # which is linked to PHBProfessionalRegistry via the application ForeignKey
        professional = PHBProfessionalRegistry.objects.filter(
            application__id=application_id
        ).first()

        # If not found by application relationship, try direct ID lookup
        if not professional:
            professional = PHBProfessionalRegistry.objects.filter(
                id=application_id
            ).first()

        if not professional:
            # Application doesn't exist - return pending status
            return Response(
                {
                    'status': 'pending',
                    'message': 'Application not found or still under review'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Check status and return appropriate response
        if professional.license_status == 'active' and professional.phb_license_number:
            return Response({
                'status': 'approved',
                'license_number': professional.phb_license_number,
                'message': 'Your license is active'
            })
        elif professional.license_status == 'rejected':
            return Response({
                'status': 'rejected',
                'reason': 'Application was not approved. Please contact support for details.',
                'message': 'Application rejected'
            })
        else:
            # pending, suspended, or other statuses
            return Response({
                'status': 'pending',
                'message': 'Application is under review'
            })

    except Exception as e:
        print(f"Application status error: {str(e)}")

        return Response(
            {
                'error': 'An error occurred while checking application status',
                'message': 'Please try again or contact support'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_professional_info(request):
    """
    GET /api/registry/my-info/

    Get the authenticated user's professional registry information.
    Returns professional_type, license_number, specialization, and other credentials.

    This is used by the frontend to determine what navigation menu to show
    based on professional type (doctor, pharmacist, nurse, etc.)
    """
    try:
        # Get professional registry entry for authenticated user
        professional = PHBProfessionalRegistry.objects.filter(
            user=request.user,
            license_status='active'
        ).first()

        if not professional:
            return Response(
                {
                    'error': 'No active professional license found',
                    'message': 'You do not have an active professional license in our registry'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Return professional information
        return Response({
            'professional_type': professional.professional_type,
            'license_number': professional.phb_license_number,
            'full_name': professional.get_full_name(),
            'email': professional.public_email or professional.user.email,
            'specialization': professional.specialization,
            'license_status': professional.license_status,
            'license_expiry_date': professional.license_expiry_date,
            'verified': professional.license_status == 'active',
        })

    except Exception as e:
        print(f"Error fetching professional info: {str(e)}")
        return Response(
            {
                'error': 'Failed to retrieve professional information',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
