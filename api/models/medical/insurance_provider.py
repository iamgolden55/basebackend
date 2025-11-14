from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import json

class InsuranceProvider(models.Model):
    """
    Model representing insurance companies and their integration capabilities
    """
    INTEGRATION_TYPE_CHOICES = [
        ('api', 'API Integration'),
        ('portal', 'Web Portal Integration'),
        ('manual', 'Manual Verification'),
        ('edi', 'Electronic Data Interchange'),
        ('hybrid', 'Multiple Methods')
    ]
    
    NETWORK_TIER_CHOICES = [
        ('tier_1', 'Tier 1 (Premium)'),
        ('tier_2', 'Tier 2 (Standard)'),
        ('tier_3', 'Tier 3 (Basic)'),
        ('government', 'Government Insurance'),
        ('private', 'Private Insurance')
    ]
    
    COVERAGE_AREA_CHOICES = [
        ('national', 'National Coverage'),
        ('regional', 'Regional Coverage'),
        ('state', 'State/Province Coverage'),
        ('local', 'Local Coverage'),
        ('international', 'International Coverage')
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Official name of the insurance provider"
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Common abbreviation or short name"
    )
    provider_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique identifier code for the provider"
    )
    
    # Contact Information
    headquarters_address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    customer_service_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Customer service hotline"
    )
    provider_portal_url = models.URLField(
        blank=True,
        help_text="URL for provider portal if available"
    )
    
    # Coverage and Network Information
    coverage_area = models.CharField(
        max_length=20,
        choices=COVERAGE_AREA_CHOICES,
        default='national'
    )
    network_tier = models.CharField(
        max_length=20,
        choices=NETWORK_TIER_CHOICES,
        default='private'
    )
    countries_served = models.JSONField(
        default=list,
        help_text="List of countries where coverage is available"
    )
    regions_served = models.JSONField(
        default=list,
        help_text="List of regions/states served"
    )
    
    # Integration Configuration
    integration_type = models.CharField(
        max_length=20,
        choices=INTEGRATION_TYPE_CHOICES,
        default='manual'
    )
    api_base_url = models.URLField(
        blank=True,
        help_text="Base URL for API integration"
    )
    api_version = models.CharField(
        max_length=10,
        blank=True,
        help_text="API version (e.g., v1, v2)"
    )
    api_documentation_url = models.URLField(
        blank=True,
        help_text="URL to API documentation"
    )
    
    # Authentication and Security
    requires_authentication = models.BooleanField(
        default=True,
        help_text="Whether API requires authentication"
    )
    authentication_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of authentication (Bearer, API Key, OAuth, etc.)"
    )
    test_credentials_available = models.BooleanField(
        default=False,
        help_text="Whether test/sandbox credentials are available"
    )
    
    # Response and Performance Metrics
    average_response_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average API response time in milliseconds"
    )
    uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="API uptime percentage"
    )
    rate_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="API rate limit per minute"
    )
    
    # Business Information
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the provider is currently active"
    )
    accepts_new_providers = models.BooleanField(
        default=True,
        help_text="Whether they accept new healthcare providers"
    )
    minimum_volume_requirement = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum monthly claims volume required"
    )
    contract_terms = models.TextField(
        blank=True,
        help_text="General contract terms and requirements"
    )
    
    # Financial Information
    typical_reimbursement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Typical reimbursement percentage"
    )
    payment_terms_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical payment terms in days"
    )
    processing_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Processing fee percentage"
    )
    
    # Integration Configuration (Encrypted)
    _encrypted_api_credentials = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
        help_text="Encrypted API credentials"
    )
    integration_notes = models.TextField(
        blank=True,
        help_text="Notes about integration setup and requirements"
    )
    
    # Verification and Quality Assurance
    last_verified = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time provider information was verified"
    )
    verification_frequency_days = models.PositiveIntegerField(
        default=30,
        help_text="How often to verify provider information"
    )
    data_quality_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Data quality score based on accuracy and completeness"
    )
    
    # Compliance and Certifications
    hipaa_compliant = models.BooleanField(
        default=False,
        help_text="Whether provider is HIPAA compliant"
    )
    soc2_certified = models.BooleanField(
        default=False,
        help_text="Whether provider has SOC 2 certification"
    )
    iso27001_certified = models.BooleanField(
        default=False,
        help_text="Whether provider has ISO 27001 certification"
    )
    compliance_notes = models.TextField(
        blank=True,
        help_text="Additional compliance information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_insurance_providers',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_insurance_providers',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['provider_code']),
            models.Index(fields=['coverage_area']),
            models.Index(fields=['network_tier']),
            models.Index(fields=['integration_type']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("can_view_api_credentials", "Can view API credentials"),
            ("can_modify_integration_settings", "Can modify integration settings"),
            ("can_verify_provider_data", "Can verify provider data"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"

    def clean(self):
        """Validate insurance provider data"""
        super().clean()
        
        if self.integration_type == 'api' and not self.api_base_url:
            raise ValidationError(
                "API base URL is required for API integration type"
            )
        
        if self.typical_reimbursement_rate and self.typical_reimbursement_rate > 100:
            raise ValidationError(
                "Reimbursement rate cannot exceed 100%"
            )
        
        # Generate provider code if not provided
        if not self.provider_code:
            self.provider_code = self.generate_provider_code()

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    @property
    def api_credentials(self):
        """Decrypt and return API credentials"""
        if self._encrypted_api_credentials:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='insurance_provider_credentials')
                return json.loads(signer.unsign(self._encrypted_api_credentials.decode()))
            except Exception:
                return {}
        return {}

    @api_credentials.setter
    def api_credentials(self, credentials):
        """Encrypt and store API credentials"""
        if credentials:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='insurance_provider_credentials')
                self._encrypted_api_credentials = signer.sign(json.dumps(credentials)).encode()
            except Exception:
                pass

    def generate_provider_code(self):
        """Generate a unique provider code"""
        # Create code from name (first 3 letters + random number)
        import re
        import random
        
        # Remove non-alphabetic characters and take first 3 letters
        clean_name = re.sub(r'[^A-Za-z]', '', self.name)
        prefix = clean_name[:3].upper()
        
        # Add random number
        suffix = str(random.randint(100, 999))
        code = f"{prefix}{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while InsuranceProvider.objects.filter(provider_code=code).exists():
            code = f"{original_code}{counter}"
            counter += 1
            
        return code

    def is_verification_due(self):
        """Check if provider information verification is due"""
        if not self.last_verified:
            return True
            
        from datetime import timedelta
        due_date = self.last_verified + timedelta(days=self.verification_frequency_days)
        return timezone.now() > due_date

    def can_integrate_via_api(self):
        """Check if provider supports API integration"""
        return self.integration_type in ['api', 'hybrid'] and bool(self.api_base_url)

    def supports_real_time_verification(self):
        """Check if provider supports real-time verification"""
        return self.integration_type in ['api', 'hybrid'] and self.can_integrate_via_api()

    def get_integration_priority(self):
        """Get integration priority based on capabilities"""
        priority_map = {
            'api': 1,
            'hybrid': 2,
            'edi': 3,
            'portal': 4,
            'manual': 5
        }
        return priority_map.get(self.integration_type, 5)

    def update_performance_metrics(self, response_time=None, success=True):
        """Update performance metrics based on API calls"""
        if response_time:
            if self.average_response_time:
                # Simple moving average
                self.average_response_time = (self.average_response_time + response_time) // 2
            else:
                self.average_response_time = response_time
        
        # Update last verified timestamp on successful calls
        if success:
            self.last_verified = timezone.now()
            
        self.save()

    def get_verification_methods(self):
        """Get list of available verification methods"""
        methods = []
        
        if self.can_integrate_via_api():
            methods.append('api')
        if self.provider_portal_url:
            methods.append('portal')
        if self.customer_service_phone:
            methods.append('phone')
            
        methods.append('manual')  # Always available as fallback
        return methods

    def estimate_verification_time(self):
        """Estimate verification time in minutes"""
        time_estimates = {
            'api': 1,
            'portal': 5,
            'edi': 15,
            'manual': 30
        }
        return time_estimates.get(self.integration_type, 30)

    def get_service_areas(self):
        """Get formatted service areas"""
        areas = []
        if self.countries_served:
            areas.extend(self.countries_served)
        if self.regions_served:
            areas.extend(self.regions_served)
        return areas

    @classmethod
    def get_active_providers_by_area(cls, country=None, region=None):
        """Get active providers serving a specific area"""
        queryset = cls.objects.filter(is_active=True)
        
        if country:
            queryset = queryset.filter(countries_served__contains=[country])
        if region:
            queryset = queryset.filter(regions_served__contains=[region])
            
        return queryset.order_by('name')

    @classmethod
    def get_api_enabled_providers(cls):
        """Get providers with API integration capability"""
        return cls.objects.filter(
            is_active=True,
            integration_type__in=['api', 'hybrid']
        ).exclude(api_base_url='')