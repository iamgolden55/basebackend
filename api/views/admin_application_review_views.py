"""
Admin Application Review Views

API endpoints for PHB admin to review and approve professional applications.
Nigerian healthcare professional credentialing and licensing.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
import uuid
import logging

from api.models import (
    ProfessionalApplication,
    ApplicationDocument,
    PHBProfessionalRegistry,
)
from api.professional_application_serializers import (
    ProfessionalApplicationListSerializer,
    ProfessionalApplicationDetailSerializer,
    ApplicationDocumentSerializer,
    PHBProfessionalRegistryPrivateSerializer,
    AdminApplicationReviewSerializer,
)
from api.permissions import HasRegistryPermission, CanReviewApplications, CanVerifyDocuments
from api.models.user.audit_log import AuditLog

logger = logging.getLogger(__name__)


# =============================================================================
# ADMIN APPLICATION MANAGEMENT
# =============================================================================

@api_view(['GET'])
@permission_classes([HasRegistryPermission])
def admin_list_applications(request):
    """
    List all professional applications with filters.
    Admin only.

    URL: /api/admin/applications/

    Filters:
    - status: Application status
    - professional_type: Type of professional
    - submitted_after: Date filter
    - reviewed_by: Reviewer
    """
    admin_list_applications.permission_required = 'view_applications'

    applications = ProfessionalApplication.objects.all().select_related(
        'user', 'reviewed_by'
    ).prefetch_related('documents')

    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    professional_type = request.query_params.get('professional_type')
    if professional_type:
        applications = applications.filter(professional_type=professional_type)

    submitted_after = request.query_params.get('submitted_after')
    if submitted_after:
        applications = applications.filter(submitted_date__gte=submitted_after)

    reviewed_by = request.query_params.get('reviewed_by')
    if reviewed_by:
        applications = applications.filter(reviewed_by_id=reviewed_by)

    search = request.query_params.get('search')
    if search:
        applications = applications.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(application_reference__icontains=search) |
            Q(email__icontains=search)
        )

    # Order by submission date (newest first)
    applications = applications.order_by('-submitted_date', '-created_at')

    # Pagination
    page = int(request.query_params.get('page', 1))
    per_page = int(request.query_params.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page

    total_count = applications.count()
    results = applications[start:end]

    serializer = ProfessionalApplicationListSerializer(
        results,
        many=True,
        context={'request': request}
    )

    # Get counts by status
    status_counts = ProfessionalApplication.objects.values('status').annotate(
        count=Count('id')
    )
    status_summary = {item['status']: item['count'] for item in status_counts}

    # Add audit log
    filters_info = {
        'status': status_filter,
        'professional_type': professional_type,
        'search': search,
        'page': page
    }
    AuditLog.objects.create(
        user=request.user,
        action_type='view',
        resource_type='ProfessionalApplication',
        resource_id='list',
        description=f"Viewed applications list (page {page}, {total_count} total)",
        metadata={'filters': filters_info},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return Response({
        'count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page,
        'status_summary': status_summary,
        'applications': serializer.data
    })


@api_view(['GET'])
@permission_classes([HasRegistryPermission])
def admin_application_detail(request, application_id):
    """
    Get full application details for admin review.

    URL: /api/admin/applications/<uuid:application_id>/
    """
    admin_application_detail.permission_required = 'view_applications'

    application = get_object_or_404(
        ProfessionalApplication.objects.select_related('user', 'reviewed_by').prefetch_related('documents'),
        id=application_id
    )

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='view',
        resource_type='ProfessionalApplication',
        resource_id=str(application.id),
        description=f"Viewed application details for {application.application_reference}",
        metadata={
            'application_reference': application.application_reference,
            'professional_type': application.professional_type,
            'status': application.status
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ProfessionalApplicationDetailSerializer(
        application,
        context={'request': request}
    )

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([CanReviewApplications])
def admin_start_review(request, application_id):
    """
    Start reviewing an application.
    Changes status from 'submitted' to 'under_review'.

    URL: /api/admin/applications/<uuid:application_id>/start-review/
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)

    if application.status != 'submitted':
        return Response(
            {'error': f'Cannot start review for application with status: {application.get_status_display()}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Start review
    application.start_review(reviewer=request.user)

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='update',
        resource_type='ProfessionalApplication',
        resource_id=str(application.id),
        description=f"Started review of application {application.application_reference}",
        metadata={
            'application_reference': application.application_reference,
            'professional_type': application.professional_type,
            'previous_status': 'submitted',
            'new_status': 'under_review'
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ProfessionalApplicationDetailSerializer(
        application,
        context={'request': request}
    )

    return Response({
        'message': f'Review started for application {application.application_reference}',
        'application': serializer.data
    })


@api_view(['POST'])
@permission_classes([CanVerifyDocuments])
def admin_verify_document(request, application_id, document_id):
    """
    Verify a document as authentic.

    URL: /api/admin/applications/<uuid:application_id>/documents/<uuid:document_id>/verify/

    Body:
    {
        "notes": "Document verified with issuing institution"
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)
    document = get_object_or_404(ApplicationDocument, id=document_id, application=application)

    notes = request.data.get('notes', '')

    # Verify document
    document.verify_document(verifier=request.user, notes=notes)

    # Check if all documents are now verified
    total_docs = application.documents.count()
    verified_docs = application.documents.filter(verification_status='verified').count()

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='verify',
        resource_type='ApplicationDocument',
        resource_id=str(document.id),
        description=f"Verified document {document.document_type} for application {application.application_reference}",
        metadata={
            'application_id': str(application.id),
            'application_reference': application.application_reference,
            'document_type': document.document_type,
            'verification_notes': notes,
            'verified_docs': verified_docs,
            'total_docs': total_docs,
            'all_verified': verified_docs == total_docs
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ApplicationDocumentSerializer(
        document,
        context={'request': request}
    )

    return Response({
        'message': f'Document verified successfully ({verified_docs}/{total_docs} documents verified)',
        'document': serializer.data,
        'all_verified': verified_docs == total_docs
    })


@api_view(['POST'])
@permission_classes([CanVerifyDocuments])
def admin_reject_document(request, application_id, document_id):
    """
    Reject a document as invalid.

    URL: /api/admin/applications/<uuid:application_id>/documents/<uuid:document_id>/reject/

    Body:
    {
        "reason": "Document appears to be altered"
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)
    document = get_object_or_404(ApplicationDocument, id=document_id, application=application)

    reason = request.data.get('reason', '')

    if not reason:
        return Response(
            {'error': 'Rejection reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Reject document (this also sets resubmission deadline and increments rejection_count)
    document.reject_document(verifier=request.user, reason=reason)

    # Set application flag to indicate rejected documents
    application.has_rejected_documents = True
    application.save(update_fields=['has_rejected_documents'])

    # Send email notification to applicant
    from api.utils.email import send_document_rejection_email
    try:
        send_document_rejection_email(application, document)
    except Exception as e:
        logger.warning(f"Failed to send document rejection email: {e}")
        # Continue even if email fails - rejection is still processed

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='reject',
        resource_type='ApplicationDocument',
        resource_id=str(document.id),
        description=f"Rejected document {document.document_type} for application {application.application_reference}",
        metadata={
            'application_id': str(application.id),
            'application_reference': application.application_reference,
            'document_type': document.document_type,
            'rejection_reason': reason,
            'rejection_count': document.rejection_count,
            'attempts_remaining': document.attempts_remaining,
            'resubmission_deadline': document.resubmission_deadline.isoformat() if document.resubmission_deadline else None,
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ApplicationDocumentSerializer(
        document,
        context={'request': request}
    )

    return Response({
        'message': f'Document rejected. Applicant has {document.attempts_remaining} attempts remaining.',
        'document': serializer.data,
        'rejection_count': document.rejection_count,
        'attempts_remaining': document.attempts_remaining,
        'max_attempts': document.max_rejection_attempts,
        'resubmission_deadline': document.resubmission_deadline.isoformat() if document.resubmission_deadline else None,
    })


@api_view(['POST'])
@permission_classes([CanVerifyDocuments])
def admin_request_clarification(request, application_id, document_id):
    """
    Request clarification on a document.

    URL: /api/admin/applications/<uuid:application_id>/documents/<uuid:document_id>/clarify/

    Body:
    {
        "clarification_needed": "Please provide a clearer copy of the certificate"
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)
    document = get_object_or_404(ApplicationDocument, id=document_id, application=application)

    clarification = request.data.get('clarification_needed', '')

    if not clarification:
        return Response(
            {'error': 'Clarification message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Request clarification
    document.request_clarification(verifier=request.user, clarification_needed=clarification)

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='update',
        resource_type='ApplicationDocument',
        resource_id=str(document.id),
        description=f"Requested clarification for document {document.document_type} in application {application.application_reference}",
        metadata={
            'application_id': str(application.id),
            'application_reference': application.application_reference,
            'document_type': document.document_type,
            'clarification_needed': clarification
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = ApplicationDocumentSerializer(
        document,
        context={'request': request}
    )

    return Response({
        'message': 'Clarification requested',
        'document': serializer.data
    })


@api_view(['POST'])
@permission_classes([CanReviewApplications])
def admin_request_additional_documents(request, application_id):
    """
    Request additional documents from applicant.

    URL: /api/admin/applications/<uuid:application_id>/request-documents/

    Body:
    {
        "notes": "Please upload the following additional documents: ...",
        "documents_needed": ["good_standing_certificate", "character_reference"]
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)

    notes = request.data.get('notes', '')
    documents_needed = request.data.get('documents_needed', [])

    if not notes or not documents_needed:
        return Response(
            {'error': 'Both notes and documents_needed are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Request additional documents
    application.request_additional_documents(reviewer=request.user, notes=notes)

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='update',
        resource_type='ProfessionalApplication',
        resource_id=str(application.id),
        description=f"Requested additional documents for application {application.application_reference}",
        metadata={
            'application_reference': application.application_reference,
            'professional_type': application.professional_type,
            'documents_needed': documents_needed,
            'notes': notes
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # TODO: Send email to applicant with list of needed documents
    # send_application_documents_requested_email(application, documents_needed)

    serializer = ProfessionalApplicationDetailSerializer(
        application,
        context={'request': request}
    )

    return Response({
        'message': f'Additional documents requested for {application.application_reference}',
        'application': serializer.data
    })


@api_view(['POST'])
@permission_classes([CanReviewApplications])
def admin_approve_application(request, application_id):
    """
    Approve application and issue PHB professional license.

    URL: /api/admin/applications/<uuid:application_id>/approve/

    Body:
    {
        "review_notes": "All credentials verified. Approved for PHB license.",
        "practice_type": "hospital",  // or "private" or "both"
        "public_email": "doctor@example.com",  // optional
        "public_phone": "+234...",  // optional
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)

    if application.status == 'approved':
        return Response(
            {'error': 'Application has already been approved'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify all documents are verified
    total_docs = application.documents.count()
    verified_docs = application.documents.filter(verification_status='verified').count()

    if verified_docs < total_docs:
        return Response(
            {
                'error': f'Not all documents have been verified. {verified_docs}/{total_docs} documents verified.',
                'unverified_count': total_docs - verified_docs
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    review_notes = request.data.get('review_notes', '')

    # Generate PHB license number using UUID for global uniqueness
    professional_type = application.professional_type

    # Professional type code mapping
    type_codes = {
        'doctor': 'DOC',
        'pharmacist': 'PHARM',
        'nurse': 'NURSE',
        'physiotherapist': 'PHYSIO',
        'lab_technician': 'LAB',
        'radiographer': 'RAD',
        'midwife': 'MID',
        'dentist': 'DENT',
        'optometrist': 'OPT',
    }
    type_code = type_codes.get(professional_type, 'PROF')

    # Generate unique identifier using UUID4
    # Format: PHB-{TYPE}-{FIRST_8_CHARS}-{LAST_4_CHARS}
    # Example: PHB-DOC-A3F2B9C1-E4D7
    unique_id = uuid.uuid4().hex.upper()
    id_part_1 = unique_id[:8]   # First 8 hex characters
    id_part_2 = unique_id[-4:]  # Last 4 hex characters

    license_number = f"PHB-{type_code}-{id_part_1}-{id_part_2}"

    # Collision check (extremely unlikely with UUID4, but good practice)
    max_attempts = 5
    attempts = 0
    while PHBProfessionalRegistry.objects.filter(phb_license_number=license_number).exists():
        if attempts >= max_attempts:
            # This should never happen in practice (UUID4 collision probability: ~5.3 × 10^36)
            logger.error(f"UUID collision detected after {max_attempts} attempts for application {application.id}")
            return Response(
                {'error': 'Failed to generate unique license number. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        unique_id = uuid.uuid4().hex.upper()
        id_part_1 = unique_id[:8]
        id_part_2 = unique_id[-4:]
        license_number = f"PHB-{type_code}-{id_part_1}-{id_part_2}"
        attempts += 1

    logger.info(f"Generated PHB license number: {license_number} for application {application.id}")

    # Approve application and issue license
    application.approve_application(
        license_number=license_number,
        reviewer=request.user,
        review_notes=review_notes
    )

    # Mark all verification flags as true
    application.documents_verified = True
    application.identity_verified = True
    application.qualifications_verified = True
    application.registration_verified = True
    application.save(update_fields=[
        'documents_verified', 'identity_verified',
        'qualifications_verified', 'registration_verified'
    ])

    # Create PHB Professional Registry entry
    practice_type = request.data.get('practice_type', 'hospital')
    public_email = request.data.get('public_email', '')
    public_phone = request.data.get('public_phone', '')
    biography = request.data.get('biography', '')

    registry_entry = PHBProfessionalRegistry.objects.create(
        user=application.user,
        application=application,
        phb_license_number=license_number,
        professional_type=application.professional_type,
        title=application.title,
        first_name=application.first_name,
        last_name=application.last_name,
        primary_qualification=application.primary_qualification,
        qualification_year=application.qualification_year,
        specialization=application.specialization,
        license_status='active',
        license_issue_date=application.license_issue_date,
        license_expiry_date=application.license_expiry_date,
        home_registration_body=application.home_registration_body,
        home_registration_number=application.home_registration_number,
        practice_type=practice_type,
        city=application.city,
        state=application.state,
        country=application.country,
        languages_spoken=application.languages_spoken,
        public_email=public_email,
        public_phone=public_phone,
        biography=biography,
        identity_verified=True,
        qualifications_verified=True,
        is_searchable=True,
    )

    # Send approval email with license certificate
    from api.utils.email import send_application_approved_email
    try:
        send_application_approved_email(application, registry_entry)
    except Exception as e:
        logger.warning(f"Failed to send approval email: {e}")

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='approve',
        resource_type='ProfessionalApplication',
        resource_id=str(application.id),
        description=f"Approved application {application.application_reference} and issued license {license_number}",
        metadata={
            'application_reference': application.application_reference,
            'professional_type': application.professional_type,
            'license_number': license_number,
            'applicant_name': application.get_full_name(),
            'practice_type': practice_type,
            'review_notes': review_notes
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    serializer = PHBProfessionalRegistryPrivateSerializer(
        registry_entry,
        context={'request': request}
    )

    return Response({
        'message': f'Application approved! PHB license {license_number} issued to {application.get_full_name()}.',
        'registry_entry': serializer.data
    })


@api_view(['POST'])
@permission_classes([CanReviewApplications])
def admin_reject_application(request, application_id):
    """
    Reject an application.

    URL: /api/admin/applications/<uuid:application_id>/reject/

    Body:
    {
        "rejection_reason": "Qualification certificates could not be verified with issuing institution"
    }
    """
    application = get_object_or_404(ProfessionalApplication, id=application_id)

    if application.status in ['approved', 'rejected']:
        return Response(
            {'error': f'Cannot reject application with status: {application.get_status_display()}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    rejection_reason = request.data.get('rejection_reason', '')

    if not rejection_reason:
        return Response(
            {'error': 'Rejection reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Reject application
    application.reject_application(reviewer=request.user, rejection_reason=rejection_reason)

    # Add audit log
    AuditLog.objects.create(
        user=request.user,
        action_type='reject',
        resource_type='ProfessionalApplication',
        resource_id=str(application.id),
        description=f"Rejected application {application.application_reference}",
        metadata={
            'application_reference': application.application_reference,
            'professional_type': application.professional_type,
            'applicant_name': application.get_full_name(),
            'rejection_reason': rejection_reason
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # TODO: Send rejection email
    # send_application_rejected_email(application)

    serializer = ProfessionalApplicationDetailSerializer(
        application,
        context={'request': request}
    )

    return Response({
        'message': f'Application {application.application_reference} rejected',
        'application': serializer.data
    })


# =============================================================================
# ADMIN REGISTRY MANAGEMENT
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_list_registry(request):
    """
    List all registry entries with admin view (private data).

    URL: /api/admin/registry/
    """
    registry = PHBProfessionalRegistry.objects.all().select_related('user', 'application')

    # Apply filters
    license_status = request.query_params.get('license_status')
    if license_status:
        registry = registry.filter(license_status=license_status)

    professional_type = request.query_params.get('professional_type')
    if professional_type:
        registry = registry.filter(professional_type=professional_type)

    state = request.query_params.get('state')
    if state:
        registry = registry.filter(state__iexact=state)

    search = request.query_params.get('search')
    if search:
        registry = registry.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phb_license_number__icontains=search)
        )

    # Order by registration date
    registry = registry.order_by('-first_registered_date')

    # Pagination
    page = int(request.query_params.get('page', 1))
    per_page = int(request.query_params.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page

    total_count = registry.count()
    results = registry[start:end]

    serializer = PHBProfessionalRegistryPrivateSerializer(
        results,
        many=True,
        context={'request': request}
    )

    return Response({
        'count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page,
        'registry_entries': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_suspend_license(request, license_number):
    """
    Suspend a professional's license.

    URL: /api/admin/registry/<license_number>/suspend/

    Body:
    {
        "reason": "Pending investigation into malpractice complaint"
    }
    """
    registry_entry = get_object_or_404(
        PHBProfessionalRegistry,
        phb_license_number__iexact=license_number
    )

    reason = request.data.get('reason', '')

    if not reason:
        return Response(
            {'error': 'Suspension reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Suspend license
    registry_entry.suspend_license(reason=reason, admin_user=request.user)

    serializer = PHBProfessionalRegistryPrivateSerializer(
        registry_entry,
        context={'request': request}
    )

    return Response({
        'message': f'License {license_number} suspended',
        'registry_entry': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_reactivate_license(request, license_number):
    """
    Reactivate a suspended license.

    URL: /api/admin/registry/<license_number>/reactivate/
    """
    registry_entry = get_object_or_404(
        PHBProfessionalRegistry,
        phb_license_number__iexact=license_number
    )

    if registry_entry.license_status != 'suspended':
        return Response(
            {'error': 'Only suspended licenses can be reactivated'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Reactivate license
    registry_entry.reactivate_license(admin_user=request.user)

    serializer = PHBProfessionalRegistryPrivateSerializer(
        registry_entry,
        context={'request': request}
    )

    return Response({
        'message': f'License {license_number} reactivated',
        'registry_entry': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_revoke_license(request, license_number):
    """
    Permanently revoke a professional's license.

    URL: /api/admin/registry/<license_number>/revoke/

    Body:
    {
        "reason": "Convicted of professional misconduct"
    }
    """
    registry_entry = get_object_or_404(
        PHBProfessionalRegistry,
        phb_license_number__iexact=license_number
    )

    reason = request.data.get('reason', '')

    if not reason:
        return Response(
            {'error': 'Revocation reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Revoke license
    registry_entry.revoke_license(reason=reason, admin_user=request.user)

    serializer = PHBProfessionalRegistryPrivateSerializer(
        registry_entry,
        context={'request': request}
    )

    return Response({
        'message': f'License {license_number} revoked permanently',
        'registry_entry': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_add_disciplinary_record(request, license_number):
    """
    Add a disciplinary record to professional's public registry entry.

    URL: /api/admin/registry/<license_number>/disciplinary/

    Body:
    {
        "notes": "Suspended for 3 months for failure to maintain proper patient records. Suspension lifted after compliance training."
    }
    """
    registry_entry = get_object_or_404(
        PHBProfessionalRegistry,
        phb_license_number__iexact=license_number
    )

    notes = request.data.get('notes', '')

    if not notes:
        return Response(
            {'error': 'Disciplinary notes are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Add disciplinary record
    registry_entry.add_disciplinary_record(notes=notes, admin_user=request.user)

    serializer = PHBProfessionalRegistryPrivateSerializer(
        registry_entry,
        context={'request': request}
    )

    return Response({
        'message': 'Disciplinary record added to public registry',
        'registry_entry': serializer.data
    })
