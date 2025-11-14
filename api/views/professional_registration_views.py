"""
Professional Registration Views

API endpoints for professional registration to PHB National Registry.
Nigerian-focused professional licensing system (doctors, pharmacists, nurses, etc.).

Based on NHS GMC model adapted for Nigerian healthcare context.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone

from api.models import (
    ProfessionalApplication,
    ApplicationDocument,
    PHBProfessionalRegistry,
)
from api.professional_application_serializers import (
    ProfessionalApplicationListSerializer,
    ProfessionalApplicationDetailSerializer,
    ProfessionalApplicationCreateSerializer,
    ProfessionalApplicationUpdateSerializer,
    ProfessionalApplicationSubmitSerializer,
    ApplicationDocumentSerializer,
    PHBProfessionalRegistryPublicSerializer,
)
from django.contrib.auth import get_user_model
from django.db import transaction
import secrets
import uuid
import os
from api.utils.email import (
    send_professional_application_confirmation_email,
    send_new_application_alert_to_admins,
    send_welcome_email,
    send_verification_email,
)

User = get_user_model()


# =============================================================================
# PUBLIC APPLICATION ENDPOINT (No authentication required)
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def submit_new_professional_application(request):
    """
    Submit a new professional application without requiring authentication.
    This endpoint creates both a user account and an application in a single transaction.

    URL: /api/registry/public/applications/
    Method: POST
    Authentication: None (public endpoint)

    This allows new healthcare professionals to apply for PHB licensing without
    needing to create an account first. The system will create an account for them
    and send login credentials via email.

    Required fields:
    - professional_type, first_name, last_name, email, phone_number
    - date_of_birth, gender, nationality
    - residential_address, residential_city, residential_state
    - regulatory_body, registration_number
    - highest_degree, university, graduation_year
    - years_experience, specialization
    - current_practice_address, current_practice_city, current_practice_state

    Optional:
    - password (if not provided, a random password will be generated)
    """
    try:
        data = request.data
        email = data.get('email')

        # Validate required fields (matching frontend form and backend model)
        required_fields = [
            'professional_type', 'first_name', 'last_name', 'email',
            'phone_number', 'date_of_birth', 'gender',
            'residential_address', 'residential_city', 'residential_state',
            'regulatory_body', 'registration_number',
            'highest_degree', 'university', 'graduation_year',
            'years_experience', 'specialization'
        ]

        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({
                'error': 'Missing required fields',
                'missing_fields': missing_fields,
                'message': f'Please provide: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already registered',
                'message': 'A user with this email already exists. Please login to submit your application.',
                'details': {
                    'email': ['A user with this email already exists']
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if home registration number already exists
        if ProfessionalApplication.objects.filter(
            home_registration_number=data.get('registration_number')
        ).exists():
            return Response({
                'error': 'Registration number already in use',
                'message': 'This registration number is already in our system. Please contact support if you believe this is an error.',
                'details': {
                    'registration_number': ['This registration number is already registered']
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # 1. Create user account
            password = data.get('password') or secrets.token_urlsafe(12)

            # First create the user object WITHOUT saving to set all fields before HPN generation
            user = User(
                username=email,
                email=email,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                date_of_birth=data.get('date_of_birth'),
                phone=data.get('phone_number'),  # Field is 'phone' not 'phone_number'
                # Set address fields BEFORE first save for proper HPN generation
                city=data.get('residential_city', ''),
                state=data.get('residential_state', ''),
                country=data.get('residential_country', 'Nigeria'),
            )
            # Set password and save (HPN will be generated with correct city)
            user.set_password(password)
            user.save()

            # 2. Create application with user (map frontend fields to model fields)
            application_data = {
                'user': user,
                'professional_type': data.get('professional_type'),
                'title': data.get('title', ''),
                'first_name': data.get('first_name'),
                'middle_name': data.get('middle_name', ''),
                'last_name': data.get('last_name'),
                'email': email,
                'phone': data.get('phone_number'),
                'alternate_phone': data.get('alternate_phone_number', ''),
                'date_of_birth': data.get('date_of_birth'),
                'gender': data.get('gender'),
                'nationality': data.get('nationality', 'Nigerian'),

                # Contact address (model uses address_line_1, city, state, country, postcode)
                'address_line_1': data.get('residential_address'),
                'address_line_2': data.get('residential_address_line_2', ''),
                'city': data.get('residential_city'),
                'state': data.get('residential_state'),
                'country': data.get('residential_country', 'Nigeria'),
                'postcode': data.get('postcode', ''),

                # Regulatory information (model uses home_registration_*)
                'home_registration_body': data.get('regulatory_body'),
                'home_registration_number': data.get('registration_number'),
                'home_registration_date': data.get('registration_date'),

                # Educational background (model uses primary_qualification, qualification_*)
                'primary_qualification': data.get('highest_degree'),
                'qualification_institution': data.get('university'),
                'qualification_year': data.get('graduation_year'),
                'qualification_country': data.get('qualification_country', 'Nigeria'),
                'additional_qualifications': data.get('additional_qualifications', []),

                # Professional details
                'years_of_experience': data.get('years_experience'),
                'specialization': data.get('specialization'),
                'subspecialization': data.get('other_specialization', ''),
                'employment_history': data.get('employment_history', []),
                'languages_spoken': data.get('languages_spoken', []),

                # Agreements
                'agreed_to_terms': True,
                'agreed_to_code_of_conduct': True,
                'declaration_truthful': True,

                # Set status to draft (user must upload documents before submission)
                'status': 'draft',
                'submitted_date': None,  # Will be set when user explicitly submits
            }

            application = ProfessionalApplication.objects.create(**application_data)

            # Generate application reference
            application.application_reference = f"PHB-APP-{application.created_at.year}-{str(application.id)[:8].upper()}"
            application.save()

            # Generate email verification token
            user.email_verification_token = uuid.uuid4()
            user.save()

            # 3. Send emails
            # FIRST: Send verification email (user must verify before accessing platform)
            verification_link = f"{os.environ.get('SERVER_API_URL', '').rstrip('/')}/api/email/verify/{user.email_verification_token}/"
            verification_email_sent = send_verification_email(user, verification_link)

            # NOTE: Welcome email will be sent automatically AFTER email verification
            # (sent by VerifyEmailToken view in authentication.py:801)

            # Send professional application confirmation (includes login credentials)
            # User can read this after verifying email
            email_sent_to_user = send_professional_application_confirmation_email(
                user=user,
                application=application,
                password=password  # Include password for new users
            )

            # Alert admins about new application (internal notification)
            email_sent_to_admins = send_new_application_alert_to_admins(
                application=application
            )

            # 4. Return response
            detail_serializer = ProfessionalApplicationDetailSerializer(
                application,
                context={'request': request}
            )

            return Response({
                'application': detail_serializer.data,
                'message': f'Application created successfully! Please verify your email and login to upload required documents.',
                'email_sent': email_sent_to_user,
                'admin_notified': False,  # Don't notify admins until application is submitted
                'user_created': True,
                'next_steps': [
                    '1. Verify your email by clicking the link sent to your inbox',
                    '2. Login using the credentials below',
                    '3. Upload all required verification documents',
                    '4. Review and submit your application for admin review'
                ],
                'login_credentials': {
                    'username': email,
                    'password': password if not data.get('password') else '(as provided)',
                    'note': 'Please save these credentials. You will need them to login and complete your application.'
                },
                'status': 'draft',
                'requires_documents': True
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create application',
            'message': str(e),
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# AUTHENTICATED APPLICATION SUBMISSION (For existing PHB users)
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_authenticated_professional_application(request):
    """
    Submit a professional application as an authenticated user.
    This endpoint is for existing PHB users who want to become professionals.

    URL: /api/registry/applications/submit/
    Method: POST
    Authentication: Required (JWT Cookie or Authorization header)

    Unlike the public endpoint, this does NOT create a user account.
    It creates only the application, linked to the authenticated user.

    Benefits for existing users:
    - No need to create duplicate accounts
    - Application linked to existing PHB profile
    - Access to full dashboard features immediately
    - HPN number already exists (patient ID)

    Required fields: Same as public endpoint except email/password
    """
    try:
        user = request.user
        data = request.data

        # Check if user already has a pending/approved application
        existing_application = ProfessionalApplication.objects.filter(
            user=user
        ).exclude(status__in=['rejected', 'withdrawn']).first()

        if existing_application:
            return Response({
                'error': 'Application already exists',
                'message': f'You already have a {existing_application.status} application.',
                'details': {
                    'status': existing_application.status,
                    'application_id': str(existing_application.id),
                    'application_reference': existing_application.application_reference,
                    'submitted_date': existing_application.submitted_date
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate required fields
        required_fields = [
            'professional_type', 'phone_number', 'date_of_birth', 'gender',
            'residential_address', 'residential_city', 'residential_state',
            'regulatory_body', 'registration_number',
            'highest_degree', 'university', 'graduation_year',
            'years_experience', 'specialization'
        ]

        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({
                'error': 'Missing required fields',
                'missing_fields': missing_fields,
                'message': f'Please provide: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if home registration number already exists
        if ProfessionalApplication.objects.filter(
            home_registration_number=data.get('registration_number')
        ).exists():
            return Response({
                'error': 'Registration number already in use',
                'message': 'This registration number is already in our system. Please contact support if you believe this is an error.',
                'details': {
                    'registration_number': ['This registration number is already registered']
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Create application with authenticated user
            application_data = {
                'user': user,
                'professional_type': data.get('professional_type'),
                'title': data.get('title', ''),
                'first_name': data.get('first_name', user.first_name),
                'middle_name': data.get('middle_name', ''),
                'last_name': data.get('last_name', user.last_name),
                'email': user.email,
                'phone': data.get('phone_number'),
                'alternate_phone': data.get('alternate_phone_number', ''),
                'date_of_birth': data.get('date_of_birth'),
                'gender': data.get('gender'),
                'nationality': data.get('nationality', 'Nigerian'),

                # Contact address
                'address_line_1': data.get('residential_address'),
                'address_line_2': data.get('residential_address_line_2', ''),
                'city': data.get('residential_city'),
                'state': data.get('residential_state'),
                'country': data.get('residential_country', 'Nigeria'),
                'postcode': data.get('postcode', ''),

                # Regulatory information
                'home_registration_body': data.get('regulatory_body'),
                'home_registration_number': data.get('registration_number'),
                'home_registration_date': data.get('registration_date'),

                # Educational background
                'primary_qualification': data.get('highest_degree'),
                'qualification_institution': data.get('university'),
                'qualification_year': data.get('graduation_year'),
                'qualification_country': data.get('qualification_country', 'Nigeria'),
                'additional_qualifications': data.get('additional_qualifications', []),

                # Professional details
                'years_of_experience': data.get('years_experience'),
                'specialization': data.get('specialization'),
                'subspecialization': data.get('other_specialization', ''),
                'employment_history': data.get('employment_history', []),
                'languages_spoken': data.get('languages_spoken', []),

                # Agreements
                'agreed_to_terms': True,
                'agreed_to_code_of_conduct': True,
                'declaration_truthful': True,

                # Set status to draft (user must upload documents before submission)
                'status': 'draft',
                'submitted_date': None,  # Will be set when user explicitly submits
            }

            application = ProfessionalApplication.objects.create(**application_data)

            # Generate application reference
            application.application_reference = f"PHB-APP-{application.created_at.year}-{str(application.id)[:8].upper()}"
            application.save()

            # Send confirmation emails
            email_sent_to_user = send_professional_application_confirmation_email(
                user=user,
                application=application,
                password=None  # No password for existing users
            )

            email_sent_to_admins = send_new_application_alert_to_admins(
                application=application
            )

            # Return response
            detail_serializer = ProfessionalApplicationDetailSerializer(
                application,
                context={'request': request}
            )

            return Response({
                'application': detail_serializer.data,
                'message': f'Application created successfully! Please upload required documents before submission.',
                'email_sent': email_sent_to_user,
                'admin_notified': False,  # Don't notify admins until application is submitted
                'user_created': False,
                'next_steps': [
                    '1. Upload all required verification documents',
                    '2. Review your application details',
                    '3. Submit your application for admin review'
                ],
                'status': 'draft',
                'requires_documents': True,
                'note': 'Your application is in draft status. Complete document uploads and submit for review from your dashboard.'
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create application',
            'message': str(e),
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PROFESSIONAL APPLICATION ENDPOINTS (Authenticated)
# =============================================================================

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def professional_applications_list_create(request):
    """
    GET: List all applications for the authenticated user
    POST: Create a new professional application (draft)

    URL: /api/registry/applications/
    """
    if request.method == 'GET':
        # List user's applications
        applications = ProfessionalApplication.objects.filter(
            user=request.user
        ).select_related('reviewed_by').prefetch_related('documents')

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)

        serializer = ProfessionalApplicationListSerializer(
            applications,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': applications.count(),
            'applications': serializer.data
        })

    elif request.method == 'POST':
        # Create new application
        serializer = ProfessionalApplicationCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            application = serializer.save()

            # Return detailed view
            detail_serializer = ProfessionalApplicationDetailSerializer(
                application,
                context={'request': request}
            )

            return Response(
                {
                    'message': 'Professional application created successfully. Please complete all required fields and upload documents before submission.',
                    'application': detail_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def professional_application_detail(request, application_id):
    """
    GET: Get application details
    PUT: Update draft application
    DELETE: Delete draft application

    URL: /api/registry/applications/<uuid:application_id>/
    """
    # Get application and verify ownership
    application = get_object_or_404(
        ProfessionalApplication,
        id=application_id,
        user=request.user
    )

    if request.method == 'GET':
        serializer = ProfessionalApplicationDetailSerializer(
            application,
            context={'request': request}
        )
        return Response(serializer.data)

    elif request.method == 'PUT':
        # Only allow updates to draft applications
        if application.status != 'draft':
            return Response(
                {'error': 'Only draft applications can be updated'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProfessionalApplicationUpdateSerializer(
            application,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()

            # Return updated details
            detail_serializer = ProfessionalApplicationDetailSerializer(
                application,
                context={'request': request}
            )

            return Response({
                'message': 'Application updated successfully',
                'application': detail_serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Allow deletion of draft and rejected applications only
        deletable_statuses = ['draft', 'rejected']

        if application.status not in deletable_statuses:
            # Provide specific error message based on status
            status_messages = {
                'submitted': 'Your application has been submitted for review and cannot be deleted. Contact support if you need to withdraw it.',
                'under_review': 'Your application is currently under review and cannot be deleted. Contact support if you need to withdraw it.',
                'approved': 'Your application has been approved and license issued. This cannot be deleted.',
                'documents_requested': 'Your application is awaiting additional documents and cannot be deleted. Contact support if you need to withdraw it.',
            }

            error_message = status_messages.get(
                application.status,
                f'Applications with status "{application.status}" cannot be deleted. Only draft and rejected applications can be deleted.'
            )

            return Response(
                {
                    'error': 'Application cannot be deleted',
                    'message': error_message,
                    'current_status': application.status,
                    'deletable_statuses': deletable_statuses
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store application reference for response message
        app_ref = application.application_reference

        # Delete the application and all related documents
        application.delete()

        return Response(
            {
                'message': 'Application deleted successfully',
                'deleted_application': app_ref,
                'note': 'All uploaded documents have been permanently removed.'
            },
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_professional_application(request, application_id):
    """
    Submit application for review.
    Validates that all required fields and documents are present.

    URL: /api/registry/applications/<uuid:application_id>/submit/
    """
    # Get application and verify ownership
    application = get_object_or_404(
        ProfessionalApplication,
        id=application_id,
        user=request.user
    )

    # Validate submission
    serializer = ProfessionalApplicationSubmitSerializer(
        data={},
        context={'application': application, 'request': request}
    )

    if serializer.is_valid():
        # Submit application
        application.submit_application()

        # Send confirmation email to user
        email_sent_to_user = send_professional_application_confirmation_email(
            user=request.user,
            application=application,
            password=None  # User already has credentials
        )

        # Notify admins about new submission
        email_sent_to_admins = send_new_application_alert_to_admins(
            application=application
        )

        # Return updated details
        detail_serializer = ProfessionalApplicationDetailSerializer(
            application,
            context={'request': request}
        )

        return Response({
            'message': f'Application {application.application_reference} submitted successfully! Our team will review your application and documents.',
            'application': detail_serializer.data,
            'email_sent': email_sent_to_user,
            'admin_notified': email_sent_to_admins,
            'next_steps': [
                'Our verification team will review your application within 3-5 business days',
                'You will receive an email notification about your application status',
                'You can track the review progress from your dashboard'
            ]
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# DOCUMENT UPLOAD ENDPOINTS
# =============================================================================

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def application_documents_list_create(request, application_id):
    """
    GET: List all documents for an application
    POST: Upload a new document

    URL: /api/registry/applications/<uuid:application_id>/documents/
    """
    # Get application and verify ownership
    application = get_object_or_404(
        ProfessionalApplication,
        id=application_id,
        user=request.user
    )

    if request.method == 'GET':
        documents = application.documents.all()

        # Filter by document type if provided
        doc_type = request.query_params.get('document_type')
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        # Filter by verification status if provided
        verification_status = request.query_params.get('verification_status')
        if verification_status:
            documents = documents.filter(verification_status=verification_status)

        serializer = ApplicationDocumentSerializer(
            documents,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': documents.count(),
            'documents': serializer.data
        })

    elif request.method == 'POST':
        # Only allow uploads to draft, clarification_requested, documents_requested, or under_review (for re-upload)
        if application.status not in ['draft', 'clarification_requested', 'documents_requested', 'under_review']:
            return Response(
                {'error': 'Documents can only be uploaded to draft applications or when additional documents/clarification are requested'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if document of same type already exists
        document_type = request.data.get('document_type')
        existing_document = None
        if document_type:
            existing_document = application.documents.filter(document_type=document_type).first()

        # If document exists and is rejected, check if it can be replaced
        if existing_document and existing_document.verification_status == 'rejected':
            # Check if document can be replaced
            if not existing_document.can_be_replaced:
                # Build detailed error message
                error_msg = 'This document cannot be replaced. '

                if existing_document.rejection_count >= existing_document.max_rejection_attempts:
                    error_msg += f'Maximum rejection attempts ({existing_document.max_rejection_attempts}) reached. Please contact support.'
                elif existing_document.resubmission_deadline and timezone.now() > existing_document.resubmission_deadline:
                    error_msg += f'Resubmission deadline ({existing_document.resubmission_deadline.strftime("%Y-%m-%d %H:%M")}) has passed. Please contact support.'
                elif existing_document.locked_after_verification:
                    error_msg += 'Document is locked and cannot be modified.'
                else:
                    error_msg += 'Please contact support for assistance.'

                return Response(
                    {
                        'error': error_msg,
                        'rejection_count': existing_document.rejection_count,
                        'max_attempts': existing_document.max_rejection_attempts,
                        'resubmission_deadline': existing_document.resubmission_deadline.isoformat() if existing_document.resubmission_deadline else None,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Replace the rejected document
            serializer = ApplicationDocumentSerializer(
                existing_document,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                # Reset verification status to pending for re-review
                document = serializer.save(
                    verification_status='pending',
                    verified_by=None,
                    verified_date=None,
                    verification_notes=''
                )

                return Response(
                    {
                        'message': f'Document replaced successfully. You have {document.attempts_remaining} attempts remaining.',
                        'replaced': True,
                        'document': ApplicationDocumentSerializer(
                            document,
                            context={'request': request}
                        ).data
                    },
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If document exists but not rejected, check if it's locked
        elif existing_document and existing_document.locked_after_verification:
            return Response(
                {'error': 'This document has been verified and is locked. It cannot be modified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new document (for draft or when document doesn't exist)
        serializer = ApplicationDocumentSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Set application and uploader
            document = serializer.save(
                application=application,
                uploaded_by=request.user
            )

            return Response(
                {
                    'message': 'Document uploaded successfully',
                    'document': ApplicationDocumentSerializer(
                        document,
                        context={'request': request}
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def application_document_detail(request, application_id, document_id):
    """
    GET: Get document details
    DELETE: Delete a document (only for draft applications)

    URL: /api/registry/applications/<uuid:application_id>/documents/<uuid:document_id>/
    """
    # Get application and verify ownership
    application = get_object_or_404(
        ProfessionalApplication,
        id=application_id,
        user=request.user
    )

    # Get document
    document = get_object_or_404(
        ApplicationDocument,
        id=document_id,
        application=application
    )

    if request.method == 'GET':
        serializer = ApplicationDocumentSerializer(
            document,
            context={'request': request}
        )
        return Response(serializer.data)

    elif request.method == 'DELETE':
        # Only allow deletion for draft applications
        if application.status != 'draft':
            return Response(
                {'error': 'Documents can only be deleted from draft applications'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent deletion of verified/locked documents
        if document.locked_after_verification:
            return Response(
                {'error': 'This document has been verified and is locked. It cannot be deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document.delete()
        return Response(
            {'message': 'Document deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_required_documents(request):
    """
    Get list of required documents for a specific professional type.

    URL: /api/registry/required-documents/?professional_type=doctor
    """
    professional_type = request.query_params.get('professional_type')

    if not professional_type:
        return Response(
            {'error': 'professional_type parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from api.models.registry.application_document import get_required_documents_for_profession

    required_docs = get_required_documents_for_profession(professional_type)

    # Get document type display names
    doc_types = dict(ApplicationDocument.DOCUMENT_TYPE)
    required_doc_details = [
        {
            'document_type': doc_type,
            'display_name': doc_types.get(doc_type, doc_type.replace('_', ' ').title())
        }
        for doc_type in required_docs
    ]

    return Response({
        'professional_type': professional_type,
        'required_documents': required_doc_details
    })


# =============================================================================
# PUBLIC REGISTRY SEARCH ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_professional_registry(request):
    """
    Public search of PHB Professional Registry.
    Allows patients and hospitals to verify professional credentials.

    Search parameters:
    - name: Professional's name (first or last name)
    - license_number: PHB license number
    - professional_type: doctor, pharmacist, nurse, etc.
    - specialization: Specific specialization
    - city: City location
    - state: Nigerian state
    - license_status: active, suspended, etc.

    URL: /api/registry/search/
    """
    # Get search parameters
    name = request.query_params.get('name', '').strip()
    license_number = request.query_params.get('license_number', '').strip()
    professional_type = request.query_params.get('professional_type', '').strip()
    specialization = request.query_params.get('specialization', '').strip()
    city = request.query_params.get('city', '').strip()
    state = request.query_params.get('state', '').strip()
    license_status = request.query_params.get('license_status', 'active').strip()

    # Start with searchable entries only
    queryset = PHBProfessionalRegistry.objects.filter(is_searchable=True)

    # Apply filters
    if name:
        queryset = queryset.filter(
            Q(first_name__icontains=name) | Q(last_name__icontains=name)
        )

    if license_number:
        queryset = queryset.filter(phb_license_number__iexact=license_number)

    if professional_type:
        queryset = queryset.filter(professional_type=professional_type)

    if specialization:
        queryset = queryset.filter(specialization__icontains=specialization)

    if city:
        queryset = queryset.filter(city__icontains=city)

    if state:
        queryset = queryset.filter(state__iexact=state)

    if license_status:
        queryset = queryset.filter(license_status=license_status)

    # Order by name
    queryset = queryset.order_by('last_name', 'first_name')

    # Pagination
    page = int(request.query_params.get('page', 1))
    per_page = int(request.query_params.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page

    total_count = queryset.count()
    results = queryset[start:end]

    serializer = PHBProfessionalRegistryPublicSerializer(
        results,
        many=True,
        context={'request': request}
    )

    return Response({
        'count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page,
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_professional_license(request, license_number):
    """
    Verify a professional's license by PHB license number.
    Public endpoint for patients/hospitals to verify credentials.

    URL: /api/registry/verify/<license_number>/
    """
    try:
        professional = PHBProfessionalRegistry.objects.get(
            phb_license_number__iexact=license_number,
            is_searchable=True
        )

        serializer = PHBProfessionalRegistryPublicSerializer(
            professional,
            context={'request': request}
        )

        # Add verification status message
        if professional.is_active:
            verification_message = f"✓ {professional.get_full_name()} is a licensed {professional.get_professional_type_display()} with PHB. License is valid until {professional.license_expiry_date}."
        elif professional.license_status == 'expired':
            verification_message = f"⚠ {professional.get_full_name()}'s license has expired. License expired on {professional.license_expiry_date}."
        elif professional.license_status == 'suspended':
            verification_message = f"⚠ {professional.get_full_name()}'s license is currently suspended."
        elif professional.license_status == 'revoked':
            verification_message = f"✗ {professional.get_full_name()}'s license has been revoked."
        else:
            verification_message = f"ℹ {professional.get_full_name()} - License status: {professional.get_license_status_display()}"

        return Response({
            'verified': True,
            'message': verification_message,
            'professional': serializer.data
        })

    except PHBProfessionalRegistry.DoesNotExist:
        return Response(
            {
                'verified': False,
                'message': f'No professional found with license number {license_number}. Please verify the license number and try again.'
            },
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_nigerian_states(request):
    """
    Get list of Nigerian states for location filtering.

    URL: /api/registry/nigerian-states/
    """
    # 36 states + FCT
    nigerian_states = [
        'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa',
        'Benue', 'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo',
        'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo', 'Jigawa', 'Kaduna',
        'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos', 'Nasarawa',
        'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers',
        'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
    ]

    return Response({
        'count': len(nigerian_states),
        'states': sorted(nigerian_states)
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_professional_types(request):
    """
    Get list of professional types supported by PHB.

    URL: /api/registry/professional-types/
    """
    professional_types = [
        {'value': choice[0], 'display': choice[1]}
        for choice in ProfessionalApplication.PROFESSIONAL_TYPE
    ]

    return Response({
        'count': len(professional_types),
        'professional_types': professional_types
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_specializations(request):
    """
    Get list of specializations.

    URL: /api/registry/specializations/
    """
    specializations = [
        {'value': choice[0], 'display': choice[1]}
        for choice in ProfessionalApplication.SPECIALIZATION_CHOICES
    ]

    # Filter by professional type if provided
    professional_type = request.query_params.get('professional_type')

    # Group specializations by professional category
    if professional_type == 'doctor':
        specializations = [s for s in specializations if s['value'] in [
            'general_practice', 'internal_medicine', 'surgery', 'pediatrics',
            'obstetrics_gynecology', 'cardiology', 'neurology', 'psychiatry',
            'oncology', 'emergency_medicine', 'radiology', 'anesthesiology'
        ]]
    elif professional_type == 'pharmacist':
        specializations = [s for s in specializations if s['value'] in [
            'community_pharmacy', 'hospital_pharmacy', 'clinical_pharmacy',
            'oncology_pharmacy', 'pediatric_pharmacy'
        ]]
    elif professional_type == 'nurse':
        specializations = [s for s in specializations if s['value'] in [
            'general_nursing', 'critical_care_nursing', 'pediatric_nursing',
            'psychiatric_nursing', 'oncology_nursing'
        ]]

    return Response({
        'count': len(specializations),
        'specializations': specializations
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def registry_statistics(request):
    """
    Get public statistics about PHB registry.

    URL: /api/registry/statistics/
    """
    # Count professionals by type
    by_type = PHBProfessionalRegistry.objects.filter(
        license_status='active',
        is_searchable=True
    ).values('professional_type').annotate(count=Count('id'))

    type_counts = {
        item['professional_type']: item['count']
        for item in by_type
    }

    # Count by state (top 10)
    by_state = PHBProfessionalRegistry.objects.filter(
        license_status='active',
        is_searchable=True
    ).values('state').annotate(count=Count('id')).order_by('-count')[:10]

    state_counts = [
        {'state': item['state'], 'count': item['count']}
        for item in by_state
    ]

    # Total counts
    total_active = PHBProfessionalRegistry.objects.filter(
        license_status='active',
        is_searchable=True
    ).count()

    total_registered = PHBProfessionalRegistry.objects.filter(
        is_searchable=True
    ).count()

    return Response({
        'total_active_professionals': total_active,
        'total_registered_professionals': total_registered,
        'professionals_by_type': type_counts,
        'top_states_by_professionals': state_counts,
        'last_updated': timezone.now().isoformat()
    })
