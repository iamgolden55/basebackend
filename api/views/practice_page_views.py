"""
Professional Practice Page Views

API endpoints for practice page CRUD operations.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from api.models.professional.professional_practice_page import (
    ProfessionalPracticePage,
    PhysicalLocation,
    VirtualServiceOffering,
)
from api.models.registry.professional_registry import PHBProfessionalRegistry
from api.models.registry.professional_application import ProfessionalApplication
from api.models.user.audit_log import AuditLog
from api.permissions import HasRegistryPermission
from api.practice_page_serializers import (
    ProfessionalPracticePageSerializer,
    ProfessionalPracticePageDetailSerializer,
    ProfessionalPracticePageCreateSerializer,
)
from api.utils.email import (
    send_practice_page_approved_email,
    send_practice_page_flagged_email,
    send_practice_page_suspended_email,
    send_practice_page_reactivated_email,
)


# ============================================================================
# ACCESS CONTROL HELPER
# ============================================================================

def check_can_create_practice_page(user):
    """
    Check if user meets all requirements to create a practice page.

    Requirements:
    1. Has approved ProfessionalApplication
    2. Has active PHB license in PHBProfessionalRegistry
    3. Doesn't already have a practice page

    Returns:
        dict: {'canCreate': bool, 'reason': str (if False)}
    """
    # Check 1: Approved application
    try:
        application = ProfessionalApplication.objects.get(
            user=user,
            status='approved',
            phb_license_number__isnull=False,
        )
    except ProfessionalApplication.DoesNotExist:
        return {
            'canCreate': False,
            'reason': 'You must have an approved professional application first. Please complete your registration.',
        }

    # Check 2: Active registry entry
    try:
        registry_entry = PHBProfessionalRegistry.objects.get(
            user=user,
            license_status='active',
            license_expiry_date__gt=timezone.now().date(),
        )
    except PHBProfessionalRegistry.DoesNotExist:
        return {
            'canCreate': False,
            'reason': 'Your PHB license is not active or has expired. Please renew your license.',
        }

    # Check 3: No existing practice page
    if ProfessionalPracticePage.objects.filter(owner=user).exists():
        return {
            'canCreate': False,
            'reason': 'You already have a practice page. You can edit your existing page from your dashboard.',
        }

    return {
        'canCreate': True,
        'registry_entry': registry_entry,
        'application': application,
    }


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@api_view(['GET'])
def public_practice_pages(request):
    """
    GET /api/practice-pages/

    Public directory of practice pages. Filterable by:
    - service_type: in_store, virtual, both
    - state: Nigerian state
    - city: City name
    - professional_type: doctor, pharmacist, nurse
    - search: Text search in practice_name, about, services
    """
    # Only show published and verified pages
    pages = ProfessionalPracticePage.objects.filter(
        is_published=True,
        verification_status='verified',
    )

    # Filters
    service_type = request.query_params.get('service_type')
    if service_type:
        pages = pages.filter(service_type=service_type)

    state = request.query_params.get('state')
    if state:
        pages = pages.filter(state__iexact=state)

    city = request.query_params.get('city')
    if city:
        pages = pages.filter(city__iexact=city)

    professional_type = request.query_params.get('professional_type')
    if professional_type:
        pages = pages.filter(linked_registry_entry__professional_type=professional_type)

    search = request.query_params.get('search')
    if search:
        pages = pages.filter(
            Q(practice_name__icontains=search) |
            Q(about__icontains=search) |
            Q(tagline__icontains=search)
        )

    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginated_pages = paginator.paginate_queryset(pages, request)

    serializer = ProfessionalPracticePageSerializer(paginated_pages, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def public_practice_page_detail(request, slug):
    """
    GET /api/practice-pages/{slug}/

    Public view of a single practice page.
    Increments view_count.
    """
    try:
        page = ProfessionalPracticePage.objects.get(
            slug=slug,
            is_published=True,
            verification_status='verified',
        )
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'Practice page not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Increment view count
    page.increment_view_count()

    serializer = ProfessionalPracticePageDetailSerializer(page)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nominatable_pharmacies(request):
    """
    GET /api/practice-pages/nominatable-pharmacies/

    Returns pharmacies that can be nominated by authenticated users.
    Combines:
    1. Professional practice pages (service_type=in-store, professional_type=pharmacist)
    2. Admin-created pharmacies (from Pharmacy model)

    Filters:
    - search: Text search
    - city: User's city
    - state: User's state
    """
    from api.models.medical.pharmacy import Pharmacy

    # Get user's location if available
    user_city = request.user.city if hasattr(request.user, 'city') else None
    user_state = request.user.state if hasattr(request.user, 'state') else None

    # Override with query params
    search = request.query_params.get('search', '').strip()
    city = request.query_params.get('city', user_city)
    state = request.query_params.get('state', user_state)

    results = []

    # 1. Get professional practice pages (pharmacies)
    practice_pages = ProfessionalPracticePage.objects.filter(
        is_published=True,
        verification_status='verified',
        service_type='in_store',  # Only physical pharmacies (note: underscore, not hyphen)
        linked_registry_entry__professional_type='pharmacist'
    )

    if city:
        practice_pages = practice_pages.filter(city__iexact=city)
    if state:
        practice_pages = practice_pages.filter(state__iexact=state)
    if search:
        practice_pages = practice_pages.filter(
            Q(practice_name__icontains=search) |
            Q(city__icontains=search) |
            Q(state__icontains=search)
        )

    # Convert practice pages to pharmacy format
    for page in practice_pages[:20]:  # Limit to 20
        results.append({
            'id': f'practice-{page.id}',  # Prefix to distinguish from admin pharmacies
            'source': 'practice_page',
            'practice_page_id': str(page.id),
            'name': page.practice_name,
            'phb_pharmacy_code': page.linked_registry_entry.phb_license_number if page.linked_registry_entry else 'N/A',
            'address_line_1': page.address_line_1,
            'address_line_2': page.address_line_2 or '',
            'city': page.city,
            'state': page.state,
            'postcode': page.postcode,
            'phone': page.phone or '',
            'email': page.email or '',
            'website': page.website or '',
            'slug': page.slug,
            'services_offered': page.services_offered or [],
            'payment_methods': page.payment_methods or [],
            'languages_spoken': page.languages_spoken or [],
            'opening_hours': {},  # Practice pages don't have structured opening hours yet
            'electronic_prescriptions_enabled': True,  # All practice pages support this
            'is_active': True,
            'verified': True,
        })

    # 2. Get admin-created pharmacies
    admin_pharmacies = Pharmacy.objects.filter(
        is_active=True,
        verified=True,
    )

    if city:
        admin_pharmacies = admin_pharmacies.filter(city__iexact=city)
    if state:
        admin_pharmacies = admin_pharmacies.filter(state__iexact=state)
    if search:
        admin_pharmacies = admin_pharmacies.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search) |
            Q(state__icontains=search)
        )

    # Convert admin pharmacies to same format
    for pharmacy in admin_pharmacies[:20]:  # Limit to 20
        results.append({
            'id': f'pharmacy-{pharmacy.id}',  # Prefix to distinguish
            'source': 'admin_pharmacy',
            'pharmacy_id': pharmacy.id,
            'name': pharmacy.name,
            'phb_pharmacy_code': pharmacy.phb_pharmacy_code,
            'address_line_1': pharmacy.address_line_1,
            'address_line_2': pharmacy.address_line_2 or '',
            'city': pharmacy.city,
            'state': pharmacy.state or '',
            'postcode': pharmacy.postcode,
            'phone': pharmacy.phone,
            'email': pharmacy.email or '',
            'website': pharmacy.website or '',
            'services_offered': pharmacy.services_offered or [],
            'opening_hours': pharmacy.opening_hours or {},
            'electronic_prescriptions_enabled': pharmacy.electronic_prescriptions_enabled,
            'is_active': pharmacy.is_active,
            'verified': pharmacy.verified,
        })

    return Response({
        'success': True,
        'count': len(results),
        'pharmacies': results,
        'user_location': {
            'city': city,
            'state': state
        }
    })


# ============================================================================
# PROFESSIONAL ENDPOINTS (Requires professional authentication)
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_eligibility(request):
    """
    GET /api/practice-pages/check-eligibility/

    Check if authenticated user can create a practice page.
    """
    result = check_can_create_practice_page(request.user)

    if result['canCreate']:
        registry_entry = result['registry_entry']
        application = result['application']

        return Response({
            'canCreate': True,
            'applicationStatus': application.status,
            'licenseNumber': registry_entry.phb_license_number,
            'licenseExpiry': registry_entry.license_expiry_date,
            'professionalType': registry_entry.professional_type,
            'specialization': registry_entry.specialization,
        })
    else:
        return Response({
            'canCreate': False,
            'reason': result['reason'],
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_practice_page(request):
    """
    POST /api/practice-pages/create/

    Create a new practice page for authenticated professional.
    """
    # Check eligibility
    eligibility = check_can_create_practice_page(request.user)
    if not eligibility['canCreate']:
        return Response(
            {'error': eligibility['reason']},
            status=status.HTTP_403_FORBIDDEN
        )

    registry_entry = eligibility['registry_entry']

    # Create page
    serializer = ProfessionalPracticePageCreateSerializer(data=request.data)
    if serializer.is_valid():
        page = serializer.save(
            owner=request.user,
            linked_registry_entry=registry_entry,
        )

        return Response({
            'success': True,
            'page': ProfessionalPracticePageDetailSerializer(page).data,
            'message': 'Practice page created successfully',
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_practice_page(request):
    """
    GET /api/practice-pages/my-page/

    Get authenticated user's practice page (if exists).
    """
    try:
        page = ProfessionalPracticePage.objects.get(owner=request.user)
        return Response({
            'hasPage': True,
            'page': ProfessionalPracticePageDetailSerializer(page).data,
        })
    except ProfessionalPracticePage.DoesNotExist:
        return Response({
            'hasPage': False,
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def preview_my_practice_page(request):
    """
    GET /api/practice-pages/my-page/preview/

    Preview your own practice page (regardless of verification status).
    Authenticated professionals can see their page even if pending verification.
    """
    try:
        page = ProfessionalPracticePage.objects.get(owner=request.user)

        # Return full page details using the detail serializer
        # This works regardless of is_published or verification_status
        serializer = ProfessionalPracticePageDetailSerializer(page)
        return Response(serializer.data)

    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'No practice page found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_practice_page(request):
    """
    PUT/PATCH /api/practice-pages/my-page/update/

    Update authenticated user's practice page.
    """
    try:
        page = ProfessionalPracticePage.objects.get(owner=request.user)
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'You do not have a practice page'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ProfessionalPracticePageCreateSerializer(
        page,
        data=request.data,
        partial=(request.method == 'PATCH')
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'page': ProfessionalPracticePageDetailSerializer(page).data,
            'message': 'Practice page updated successfully',
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_publish(request):
    """
    POST /api/practice-pages/my-page/publish/

    Publish or unpublish practice page.
    """
    try:
        page = ProfessionalPracticePage.objects.get(owner=request.user)
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'You do not have a practice page'},
            status=status.HTTP_404_NOT_FOUND
        )

    is_published = request.data.get('is_published')
    if is_published is None:
        return Response(
            {'error': 'is_published field is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    page.is_published = is_published
    page.save(update_fields=['is_published', 'updated_at'])

    message = 'Page published successfully' if is_published else 'Page unpublished successfully'

    return Response({
        'success': True,
        'is_published': page.is_published,
        'message': message,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def page_analytics(request):
    """
    GET /api/practice-pages/my-page/analytics/

    Get analytics for authenticated user's practice page.
    """
    try:
        page = ProfessionalPracticePage.objects.get(owner=request.user)
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'You do not have a practice page'},
            status=status.HTTP_404_NOT_FOUND
        )

    # For now, return basic stats
    return Response({
        'view_count': page.view_count,
        'nomination_count': page.nomination_count,
        'is_published': page.is_published,
        'verification_status': page.verification_status,
        'created_at': page.created_at,
        'updated_at': page.updated_at,
    })


# ============================================================================
# ADMIN ENDPOINTS (Requires admin authentication)
# ============================================================================

@api_view(['GET'])
@permission_classes([HasRegistryPermission])
def admin_list_pages(request):
    """
    GET /api/practice-pages/admin/pages/

    Admin view of all practice pages. Filterable by verification_status.
    Requires: view_practice_pages permission
    """
    # Set required permission
    admin_list_pages.permission_required = 'view_practice_pages'

    pages = ProfessionalPracticePage.objects.all().select_related(
        'owner', 'linked_registry_entry', 'verified_by'
    )

    verification_status = request.query_params.get('verification_status')
    if verification_status:
        pages = pages.filter(verification_status=verification_status)

    # Log audit
    AuditLog.objects.create(
        user=request.user,
        action_type='view',
        resource_type='ProfessionalPracticePage',
        resource_id='list',
        description=f"Viewed practice pages list (status: {verification_status or 'all'})",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginated_pages = paginator.paginate_queryset(pages, request)

    serializer = ProfessionalPracticePageDetailSerializer(paginated_pages, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([HasRegistryPermission])
def admin_page_detail(request, page_id):
    """
    GET /api/practice-pages/admin/pages/{page_id}/

    Get detailed information about a specific practice page.
    Requires: view_practice_pages permission
    """
    # Set required permission
    admin_page_detail.permission_required = 'view_practice_pages'

    try:
        page = ProfessionalPracticePage.objects.select_related(
            'owner', 'linked_registry_entry', 'verified_by'
        ).get(id=page_id)
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'Practice page not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Log audit
    AuditLog.objects.create(
        user=request.user,
        action_type='view',
        resource_type='ProfessionalPracticePage',
        resource_id=str(page.id),
        description=f"Viewed practice page details: '{page.practice_name}'",
        metadata={'page_slug': page.slug},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ProfessionalPracticePageDetailSerializer(page)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([HasRegistryPermission])
def admin_verify_page(request, page_id):
    """
    POST /api/practice-pages/admin/pages/{page_id}/verify/

    Admin verifies a practice page.
    Requires: verify_practice_pages, flag_practice_pages, or suspend_practice_pages permission
    """
    try:
        page = ProfessionalPracticePage.objects.get(id=page_id)
    except ProfessionalPracticePage.DoesNotExist:
        return Response(
            {'error': 'Practice page not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    verification_status = request.data.get('verification_status')
    verification_notes = request.data.get('verification_notes', '')

    if verification_status not in ['verified', 'rejected', 'flagged', 'suspended']:
        return Response(
            {'error': 'Invalid verification_status. Must be: verified, rejected, flagged, or suspended'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check permission based on action
    user_role = request.user.registry_role
    if request.user.is_superuser:
        # Superuser has all permissions
        pass
    elif not user_role or not user_role.is_active:
        return Response(
            {'error': 'You do not have permission to perform this action'},
            status=status.HTTP_403_FORBIDDEN
        )
    else:
        # Check specific permission based on verification status
        if verification_status in ['verified', 'rejected'] and 'verify_practice_pages' not in user_role.permissions:
            return Response(
                {'error': 'You do not have permission to verify practice pages'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif verification_status == 'flagged' and 'flag_practice_pages' not in user_role.permissions:
            return Response(
                {'error': 'You do not have permission to flag practice pages'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif verification_status == 'suspended' and 'suspend_practice_pages' not in user_role.permissions:
            return Response(
                {'error': 'You do not have permission to suspend practice pages'},
                status=status.HTTP_403_FORBIDDEN
            )

    # Store old status for audit log
    old_status = page.verification_status

    # Update page
    page.verification_status = verification_status
    page.verification_notes = verification_notes
    page.verified_by = request.user
    page.verified_date = timezone.now()
    page.save()

    # Log audit
    AuditLog.objects.create(
        user=request.user,
        action_type='verify' if verification_status == 'verified' else 'update',
        resource_type='ProfessionalPracticePage',
        resource_id=str(page.id),
        description=f"Changed practice page '{page.practice_name}' status from {old_status} to {verification_status}",
        metadata={
            'old_status': old_status,
            'new_status': verification_status,
            'verification_notes': verification_notes,
            'page_slug': page.slug,
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Send email notification to page owner based on verification status
    email_sent = False
    import logging
    logger = logging.getLogger(__name__)

    try:
        if verification_status == 'verified':
            # Check if this is a reactivation (was previously flagged or suspended)
            if old_status in ['flagged', 'suspended']:
                # This is a reactivation, send reactivation email with warning
                email_sent = send_practice_page_reactivated_email(
                    page,
                    reactivation_notes=verification_notes
                )
            else:
                # This is a normal approval (new page or from pending/rejected)
                email_sent = send_practice_page_approved_email(page)
        elif verification_status == 'flagged':
            # Extract penalty information from request
            has_penalty = request.data.get('has_penalty', False)
            penalty_amount = request.data.get('penalty_amount')
            email_sent = send_practice_page_flagged_email(
                page,
                flag_reason=verification_notes,
                has_penalty=has_penalty,
                penalty_amount=penalty_amount if has_penalty else None
            )
        elif verification_status == 'suspended':
            # Extract penalty information from request
            has_penalty = request.data.get('has_penalty', False)
            penalty_amount = request.data.get('penalty_amount')
            email_sent = send_practice_page_suspended_email(
                page,
                suspension_reason=verification_notes,
                has_penalty=has_penalty,
                penalty_amount=penalty_amount if has_penalty else None
            )
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to send {verification_status} email for page {page.id}: {str(e)}")

    return Response({
        'success': True,
        'page': ProfessionalPracticePageDetailSerializer(page).data,
        'message': f'Practice page {verification_status} successfully',
        'email_sent': email_sent,
    })
