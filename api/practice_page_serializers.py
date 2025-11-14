"""
Professional Practice Page Serializers

Serializers for practice page CRUD operations.
"""

from rest_framework import serializers
from api.models.professional.professional_practice_page import (
    ProfessionalPracticePage,
    PhysicalLocation,
    VirtualServiceOffering,
)
from api.models.registry.professional_registry import PHBProfessionalRegistry


class ProfessionalPracticePageSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    professional_type = serializers.CharField(source='linked_registry_entry.professional_type', read_only=True)
    license_number = serializers.CharField(source='linked_registry_entry.phb_license_number', read_only=True)
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionalPracticePage
        fields = [
            'id', 'practice_name', 'slug', 'tagline', 'service_type',
            'city', 'state', 'is_published', 'verification_status',
            'owner_name', 'professional_type', 'license_number',
            'is_open_now', 'view_count', 'created_at', 'latitude', 'longitude',
        ]

    def get_is_open_now(self, obj):
        return obj.is_open_now()


class ProfessionalPracticePageDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views"""

    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    # Professional credentials from registry
    professional_credentials = serializers.SerializerMethodField()

    # Convenience fields for quick access
    license_number = serializers.CharField(source='linked_registry_entry.phb_license_number', read_only=True)
    professional_type = serializers.CharField(source='linked_registry_entry.professional_type', read_only=True)

    # Computed fields
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionalPracticePage
        fields = '__all__'

    def get_professional_credentials(self, obj):
        registry = obj.linked_registry_entry
        return {
            'phb_license_number': registry.phb_license_number,
            'professional_type': registry.professional_type,
            'specialization': registry.specialization,
            'qualification_year': registry.qualification_year,
            'primary_qualification': registry.primary_qualification,
            'license_status': registry.license_status,
            'license_expiry_date': registry.license_expiry_date,
        }

    def get_is_open_now(self, obj):
        return obj.is_open_now()


class ProfessionalPracticePageCreateSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations"""

    class Meta:
        model = ProfessionalPracticePage
        fields = [
            'practice_name', 'slug', 'tagline', 'about', 'service_type',
            'address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country',
            'latitude', 'longitude', 'phone', 'email', 'website', 'whatsapp_number',
            'opening_hours', 'virtual_consultation_hours', 'online_booking_url', 'video_platform',
            'services_offered', 'payment_methods', 'additional_certifications', 'languages_spoken',
            'is_published', 'meta_keywords',
        ]
        extra_kwargs = {
            'slug': {'required': False},  # Auto-generated if not provided
        }

    def validate(self, data):
        service_type = data.get('service_type')

        # If in_store, require physical location
        if service_type in ['in_store', 'both']:
            if not (data.get('address_line_1') and data.get('city') and data.get('state')):
                raise serializers.ValidationError(
                    "Physical location (address, city, state) required for in-store services"
                )

        # If virtual, require contact method
        if service_type in ['virtual', 'both']:
            if not (data.get('online_booking_url') or data.get('phone') or data.get('email')):
                raise serializers.ValidationError(
                    "Contact method (booking URL, phone, or email) required for virtual services"
                )

        return data


class PhysicalLocationSerializer(serializers.ModelSerializer):
    """Serializer for physical locations"""

    class Meta:
        model = PhysicalLocation
        fields = '__all__'


class VirtualServiceOfferingSerializer(serializers.ModelSerializer):
    """Serializer for virtual service offerings"""

    class Meta:
        model = VirtualServiceOffering
        fields = '__all__'
