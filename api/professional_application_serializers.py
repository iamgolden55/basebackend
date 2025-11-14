"""
Professional Application Serializers

Serializers for professional registration application workflow.
Based on NHS GMC registration model.
"""

from rest_framework import serializers
from api.models import (
    ProfessionalApplication,
    ApplicationDocument,
    PHBProfessionalRegistry,
    CustomUser,
)
from django.utils import timezone
import uuid
from django.utils.html import escape


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for application documents (uploads).
    """
    uploaded_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()
    # Make document_title optional - will be auto-generated from document_type if not provided
    document_title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # Rejection workflow fields
    attempts_remaining = serializers.SerializerMethodField()
    can_be_replaced = serializers.ReadOnlyField()
    is_deadline_approaching = serializers.ReadOnlyField()

    class Meta:
        model = ApplicationDocument
        fields = [
            'id',
            'application',
            'document_type',
            'document_title',
            'description',
            'file',
            'file_url',
            'file_size',
            'file_type',
            'original_filename',
            'verification_status',
            'verified_by',
            'verified_by_name',
            'verified_date',
            'verification_notes',
            'issue_date',
            'expiry_date',
            'issuing_authority',
            'document_number',
            'is_required',
            'uploaded_by',
            'uploaded_by_name',
            'is_expired',
            # Rejection workflow fields
            'rejection_count',
            'max_rejection_attempts',
            'attempts_remaining',
            'resubmission_deadline',
            'can_be_replaced',
            'locked_after_verification',
            'is_deadline_approaching',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'application',  # Set from URL parameter, not request data
            'verification_status',
            'verified_by',
            'verified_date',
            'verification_notes',
            'uploaded_by',
            'rejection_count',
            'resubmission_deadline',
            'locked_after_verification',
            'created_at',
            'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        """Get uploader's name"""
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name()
        return None

    def get_verified_by_name(self, obj):
        """Get verifier's name"""
        if obj.verified_by:
            return obj.verified_by.get_full_name()
        return None

    def get_file_url(self, obj):
        """Get file URL"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_attempts_remaining(self, obj):
        """Get number of rejection attempts remaining"""
        return obj.attempts_remaining

    def validate(self, data):
        """Auto-generate document_title from document_type if not provided"""
        if not data.get('document_title') and data.get('document_type'):
            # Get human-readable label from document_type choices
            document_type = data['document_type']
            for code, label in ApplicationDocument.DOCUMENT_TYPE:
                if code == document_type:
                    data['document_title'] = label
                    break
        return data


class ProfessionalApplicationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing applications.
    """
    applicant_name = serializers.SerializerMethodField()
    professional_type_display = serializers.CharField(source='get_professional_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_draft = serializers.ReadOnlyField()
    is_submitted = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    is_pending_review = serializers.ReadOnlyField()

    class Meta:
        model = ProfessionalApplication
        fields = [
            'id',
            'application_reference',
            'applicant_name',
            'professional_type',
            'professional_type_display',
            'specialization',
            'status',
            'status_display',
            'submitted_date',
            'decision_date',
            'is_draft',
            'is_submitted',
            'is_approved',
            'is_pending_review',
            'has_rejected_documents',
            'created_at',
        ]

    def get_applicant_name(self, obj):
        """Get applicant's full name"""
        return obj.get_full_name()


class ProfessionalApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Complete serializer with all application details.
    """
    applicant_name = serializers.SerializerMethodField()
    professional_type_display = serializers.CharField(source='get_professional_type_display', read_only=True)
    specialization_display = serializers.CharField(source='get_specialization_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    document_count = serializers.SerializerMethodField()
    verified_document_count = serializers.SerializerMethodField()
    is_draft = serializers.ReadOnlyField()
    is_submitted = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    is_pending_review = serializers.ReadOnlyField()
    requires_payment = serializers.ReadOnlyField()
    all_documents_verified = serializers.ReadOnlyField()

    class Meta:
        model = ProfessionalApplication
        fields = '__all__'
        read_only_fields = [
            'id',
            'application_reference',
            'user',
            'submitted_date',
            'under_review_date',
            'decision_date',
            'reviewed_by',
            'review_notes',
            'rejection_reason',
            'phb_license_number',
            'license_issue_date',
            'license_expiry_date',
            'documents_verified',
            'identity_verified',
            'qualifications_verified',
            'registration_verified',
            'created_at',
            'updated_at',
        ]

    def get_applicant_name(self, obj):
        """Get applicant's full name"""
        return obj.get_full_name()

    def get_reviewed_by_name(self, obj):
        """Get reviewer's name"""
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name()
        return None

    def get_document_count(self, obj):
        """Get total document count"""
        return obj.documents.count()

    def get_verified_document_count(self, obj):
        """Get verified document count"""
        return obj.documents.filter(verification_status='verified').count()


class ProfessionalApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new professional applications.
    """

    class Meta:
        model = ProfessionalApplication
        fields = [
            'professional_type',
            'title',
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'gender',
            'nationality',
            'email',
            'phone',
            'alternate_phone',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postcode',
            'country',
            'primary_qualification',
            'qualification_institution',
            'qualification_year',
            'qualification_country',
            'additional_qualifications',
            'specialization',
            'subspecialization',
            'home_registration_body',
            'home_registration_number',
            'home_registration_date',
            'employment_history',
            'years_of_experience',
            'reason_for_application',
            'practice_intentions',
            'languages_spoken',
        ]

    def validate_qualification_year(self, value):
        """Validate qualification year is not in the future"""
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError('Qualification year cannot be in the future')
        if value < 1950:
            raise serializers.ValidationError('Qualification year seems too old. Please verify.')
        return value

    def validate_date_of_birth(self, value):
        """Validate applicant is at least 21 years old (minimum age for professional qualification)"""
        from datetime import date
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 21:
            raise serializers.ValidationError('Applicant must be at least 21 years old')
        if age > 80:
            raise serializers.ValidationError('Date of birth seems incorrect. Please verify.')
        return value

    def create(self, validated_data):
        """
        Create new professional application with auto-generated reference number.
        """
        # Generate unique application reference
        year = timezone.now().year
        professional_type = validated_data['professional_type']

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

        # Generate sequential number (5 digits)
        # In production, use database sequence or atomic counter
        import random
        seq_number = str(random.randint(10000, 99999))

        application_reference = f"PHB-APP-{type_code}-{year}-{seq_number}"

        # Create application
        application = ProfessionalApplication.objects.create(
            application_reference=application_reference,
            user=self.context['request'].user,
            status='draft',
            **validated_data
        )

        return application


class ProfessionalApplicationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating draft applications.
    Only allows updates to draft applications.
    """

    class Meta:
        model = ProfessionalApplication
        fields = [
            'professional_type',
            'title',
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'gender',
            'nationality',
            'email',
            'phone',
            'alternate_phone',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postcode',
            'country',
            'primary_qualification',
            'qualification_institution',
            'qualification_year',
            'qualification_country',
            'additional_qualifications',
            'specialization',
            'subspecialization',
            'home_registration_body',
            'home_registration_number',
            'home_registration_date',
            'employment_history',
            'years_of_experience',
            'reason_for_application',
            'practice_intentions',
            'languages_spoken',
            'agreed_to_terms',
            'agreed_to_code_of_conduct',
            'declaration_truthful',
        ]

    def validate(self, data):
        """Only allow updates to draft applications"""
        if self.instance and self.instance.status != 'draft':
            raise serializers.ValidationError(
                'Only draft applications can be updated. This application has already been submitted.'
            )
        return data


class ProfessionalApplicationSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting an application.
    Validates that all required fields and documents are present.
    """

    def validate(self, data):
        """Validate application is ready for submission"""
        application = self.context['application']

        # Check if already submitted
        if application.status != 'draft':
            raise serializers.ValidationError('Application has already been submitted')

        # Check required fields
        required_fields = [
            'professional_type', 'title', 'first_name', 'last_name',
            'date_of_birth', 'gender', 'nationality',
            'email', 'phone',
            'address_line_1', 'city', 'state', 'postcode', 'country',
            'primary_qualification', 'qualification_institution',
            'qualification_year', 'qualification_country',
            'specialization', 'years_of_experience',
        ]

        missing_fields = []
        for field in required_fields:
            if not getattr(application, field):
                missing_fields.append(field)

        if missing_fields:
            raise serializers.ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Check terms and conditions
        if not application.agreed_to_terms:
            raise serializers.ValidationError('You must agree to terms and conditions')
        if not application.agreed_to_code_of_conduct:
            raise serializers.ValidationError('You must agree to the professional code of conduct')
        if not application.declaration_truthful:
            raise serializers.ValidationError('You must declare that all information is truthful')

        # Check required documents
        from api.models.registry.application_document import get_required_documents_for_profession
        required_doc_types = get_required_documents_for_profession(application.professional_type)

        uploaded_doc_types = list(
            application.documents.values_list('document_type', flat=True).distinct()
        )

        missing_docs = []
        for doc_type in required_doc_types:
            if doc_type not in uploaded_doc_types:
                missing_docs.append(doc_type.replace('_', ' ').title())

        if missing_docs:
            raise serializers.ValidationError(
                f"Missing required documents: {', '.join(missing_docs)}"
            )

        return data


class PHBProfessionalRegistryPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for registry search (limited information).
    This is what patients and hospitals see when searching the registry.
    """
    full_name = serializers.SerializerMethodField()
    professional_type_display = serializers.CharField(source='get_professional_type_display', read_only=True)
    license_status_display = serializers.CharField(source='get_license_status_display', read_only=True)
    practice_type_display = serializers.CharField(source='get_practice_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()

    class Meta:
        model = PHBProfessionalRegistry
        fields = [
            'id',
            'phb_license_number',
            'professional_type',
            'professional_type_display',
            'full_name',
            'title',
            'first_name',
            'last_name',
            'primary_qualification',
            'qualification_year',
            'specialization',
            'license_status',
            'license_status_display',
            'license_issue_date',
            'license_expiry_date',
            'home_registration_body',
            'home_registration_number',
            'practice_type',
            'practice_type_display',
            'city',
            'state',
            'country',
            'languages_spoken',
            'public_email',
            'public_phone',
            'website',
            'identity_verified',
            'qualifications_verified',
            'has_disciplinary_record',
            'disciplinary_notes',
            'biography',
            'areas_of_interest',
            'first_registered_date',
            'is_active',
            'days_until_expiry',
        ]

    def get_full_name(self, obj):
        """Get professional's full name"""
        return obj.get_full_name()


class PHBProfessionalRegistryPrivateSerializer(serializers.ModelSerializer):
    """
    Private serializer for admin/professional view (full information).
    """
    full_name = serializers.SerializerMethodField()
    professional_type_display = serializers.CharField(source='get_professional_type_display', read_only=True)
    license_status_display = serializers.CharField(source='get_license_status_display', read_only=True)
    practice_type_display = serializers.CharField(source='get_practice_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    requires_renewal = serializers.ReadOnlyField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = PHBProfessionalRegistry
        fields = '__all__'

    def get_full_name(self, obj):
        """Get professional's full name"""
        return obj.get_full_name()


class AdminApplicationReviewSerializer(serializers.Serializer):
    """
    Serializer for admin review actions (approve, reject, request documents).
    """
    action = serializers.ChoiceField(
        choices=['start_review', 'approve', 'reject', 'request_documents'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    documents_needed = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate(self, data):
        """Validate action-specific requirements"""
        action = data.get('action')

        if action == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError('Rejection reason is required when rejecting an application')

        if action == 'request_documents' and not data.get('documents_needed'):
            raise serializers.ValidationError('List of needed documents is required')

        return data


class PHBProfessionalRegistryPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for registry search (limited fields only).

    SECURITY: Only exposes non-sensitive professional information.
    Does not include: personal contact info, addresses, user details, sensitive notes.
    """
    full_name = serializers.SerializerMethodField()
    professional_type_display = serializers.CharField(source='get_professional_type_display', read_only=True)
    license_status_display = serializers.CharField(source='get_license_status_display', read_only=True)
    practice_type_display = serializers.CharField(source='get_practice_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    years_in_practice = serializers.SerializerMethodField()

    # Sanitized fields (HTML escaped for XSS protection)
    specialization_safe = serializers.SerializerMethodField()
    areas_of_interest_safe = serializers.SerializerMethodField()
    languages_spoken = serializers.SerializerMethodField()

    class Meta:
        model = PHBProfessionalRegistry
        fields = [
            # Identity
            'id',
            'phb_license_number',
            'professional_type',
            'professional_type_display',
            'full_name',
            'title',

            # License Status
            'license_status',
            'license_status_display',
            'is_active',
            'license_issue_date',
            'license_expiry_date',

            # Professional Details
            'home_registration_body',
            'home_registration_number',
            'primary_qualification',
            'qualification_year',
            'specialization_safe',
            'areas_of_interest_safe',
            'years_in_practice',
            'practice_type',
            'practice_type_display',

            # Location (General)
            'city',
            'state',

            # Additional
            'languages_spoken',

            # Verification Status
            'identity_verified',
            'qualifications_verified',
        ]

    def get_full_name(self, obj):
        """Get professional's full name"""
        return escape(obj.get_full_name())

    def get_years_in_practice(self, obj):
        """Calculate years in practice"""
        if obj.qualification_year:
            from datetime import datetime
            return datetime.now().year - obj.qualification_year
        return None

    def get_specialization_safe(self, obj):
        """Return HTML-escaped specialization"""
        return escape(obj.specialization) if obj.specialization else None

    def get_areas_of_interest_safe(self, obj):
        """Return HTML-escaped areas of interest"""
        if obj.areas_of_interest:
            # If it's a list, escape each item
            if isinstance(obj.areas_of_interest, list):
                return [escape(item) for item in obj.areas_of_interest]
            # If it's a string, escape it
            return escape(str(obj.areas_of_interest))
        return None

    def get_languages_spoken(self, obj):
        """Parse languages_spoken from JSON string to array"""
        import json
        if obj.languages_spoken:
            # If it's already a list, return it
            if isinstance(obj.languages_spoken, list):
                return obj.languages_spoken
            # If it's a string, try to parse it as JSON
            if isinstance(obj.languages_spoken, str):
                try:
                    parsed = json.loads(obj.languages_spoken)
                    return parsed if isinstance(parsed, list) else []
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, return as single-item array
                    return [obj.languages_spoken] if obj.languages_spoken.strip() else []
        return []
