from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class HealthcareAuthority(models.Model):
    """
    Model representing government healthcare regulatory authorities
    """
    AUTHORITY_TYPE_CHOICES = [
        ('federal', 'Federal Government'),
        ('state', 'State/Provincial Government'),
        ('regional', 'Regional Authority'),
        ('local', 'Local Government'),
        ('international', 'International Organization'),
        ('professional', 'Professional Association')
    ]
    
    JURISDICTION_LEVEL_CHOICES = [
        ('national', 'National'),
        ('state', 'State/Province'),
        ('county', 'County/District'),
        ('city', 'City/Municipal'),
        ('regional', 'Regional'),
        ('international', 'International')
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Official name of the healthcare authority"
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Abbreviated name or acronym"
    )
    authority_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique identifier code"
    )
    
    # Classification
    authority_type = models.CharField(
        max_length=20,
        choices=AUTHORITY_TYPE_CHOICES,
        default='federal'
    )
    jurisdiction_level = models.CharField(
        max_length=20,
        choices=JURISDICTION_LEVEL_CHOICES,
        default='national'
    )
    
    # Geographic Information
    country = models.CharField(
        max_length=100,
        help_text="Country where authority has jurisdiction"
    )
    state_province = models.CharField(
        max_length=100,
        blank=True,
        help_text="State or province (if applicable)"
    )
    regions_covered = models.JSONField(
        default=list,
        help_text="List of regions/areas under jurisdiction"
    )
    
    # Contact Information
    official_address = models.TextField(
        help_text="Official headquarters address"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True
    )
    email = models.EmailField(
        blank=True,
        help_text="Official contact email"
    )
    website = models.URLField(
        blank=True,
        help_text="Official website URL"
    )
    
    # Licensing and Registration Information
    licensing_portal_url = models.URLField(
        blank=True,
        help_text="URL for healthcare provider licensing portal"
    )
    renewal_portal_url = models.URLField(
        blank=True,
        help_text="URL for license renewal"
    )
    verification_portal_url = models.URLField(
        blank=True,
        help_text="URL for verifying licenses"
    )
    
    # Regulatory Information
    regulatory_framework = models.TextField(
        blank=True,
        help_text="Description of regulatory framework"
    )
    license_types_issued = models.JSONField(
        default=list,
        help_text="Types of licenses this authority issues"
    )
    inspection_frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text="How often inspections are conducted"
    )
    compliance_requirements = models.TextField(
        blank=True,
        help_text="Key compliance requirements"
    )
    
    # Submission and Processing Information
    application_processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average days to process applications"
    )
    renewal_processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average days to process renewals"
    )
    inspection_scheduling_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Days advance notice for inspections"
    )
    
    # Fee Information
    standard_license_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Standard licensing fee"
    )
    renewal_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="License renewal fee"
    )
    inspection_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Inspection fee (if applicable)"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for fees"
    )
    
    # Contact Personnel
    primary_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary contact person"
    )
    primary_contact_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Title of primary contact"
    )
    primary_contact_phone = models.CharField(
        max_length=20,
        blank=True
    )
    primary_contact_email = models.EmailField(
        blank=True
    )
    
    # Licensing Officer Information
    licensing_officer_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Chief licensing officer"
    )
    licensing_officer_email = models.EmailField(
        blank=True
    )
    licensing_officer_phone = models.CharField(
        max_length=20,
        blank=True
    )
    
    # Operating Information
    business_hours = models.TextField(
        blank=True,
        help_text="Official business hours"
    )
    languages_supported = models.JSONField(
        default=list,
        help_text="Languages supported for applications"
    )
    emergency_contact_available = models.BooleanField(
        default=False,
        help_text="Whether emergency contact is available"
    )
    
    # Digital Integration
    has_api_integration = models.BooleanField(
        default=False,
        help_text="Whether authority provides API access"
    )
    api_documentation_url = models.URLField(
        blank=True,
        help_text="URL to API documentation"
    )
    supports_electronic_submission = models.BooleanField(
        default=False,
        help_text="Whether electronic submissions are accepted"
    )
    digital_signature_accepted = models.BooleanField(
        default=False,
        help_text="Whether digital signatures are accepted"
    )
    
    # Performance and Reliability
    response_time_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical response time for inquiries in hours"
    )
    system_uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="System uptime percentage"
    )
    last_system_outage = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last reported system outage"
    )
    
    # Quality and Reputation
    transparency_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Transparency score (1-10)"
    )
    efficiency_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Efficiency rating (1-10)"
    )
    customer_satisfaction_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Customer satisfaction score (1-10)"
    )
    
    # Status and Verification
    is_active = models.BooleanField(
        default=True,
        help_text="Whether authority is currently active"
    )
    last_verified = models.DateField(
        null=True,
        blank=True,
        help_text="Last time information was verified"
    )
    verification_source = models.CharField(
        max_length=200,
        blank=True,
        help_text="Source of last verification"
    )
    
    # Additional Information
    special_programs = models.TextField(
        blank=True,
        help_text="Special licensing programs or initiatives"
    )
    enforcement_actions = models.TextField(
        blank=True,
        help_text="Recent enforcement actions or policy changes"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the authority"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_healthcare_authorities',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_healthcare_authorities',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['country', 'name']
        verbose_name_plural = "Healthcare Authorities"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['authority_code']),
            models.Index(fields=['country']),
            models.Index(fields=['authority_type']),
            models.Index(fields=['jurisdiction_level']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("can_manage_authorities", "Can manage healthcare authorities"),
            ("can_verify_authority_data", "Can verify authority information"),
            ("can_view_performance_metrics", "Can view authority performance metrics"),
        ]

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} ({self.country})"
        return f"{self.name} ({self.country})"

    def clean(self):
        """Validate healthcare authority data"""
        super().clean()
        
        # Generate authority code if not provided
        if not self.authority_code:
            self.authority_code = self.generate_authority_code()
        
        # Validate scores are within range
        score_fields = [
            ('transparency_score', 1, 10),
            ('efficiency_rating', 1, 10),
            ('customer_satisfaction_score', 1, 10)
        ]
        
        for field_name, min_val, max_val in score_fields:
            value = getattr(self, field_name)
            if value is not None and (value < min_val or value > max_val):
                raise ValidationError(
                    f"{field_name} must be between {min_val} and {max_val}"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    def generate_authority_code(self):
        """Generate unique authority code"""
        import re
        import random
        
        # Create code from country and name
        country_code = self.country[:2].upper()
        
        # Remove non-alphabetic characters and take first 3 letters of name
        clean_name = re.sub(r'[^A-Za-z]', '', self.name)
        name_code = clean_name[:3].upper()
        
        # Add random number
        suffix = str(random.randint(10, 99))
        code = f"{country_code}{name_code}{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while HealthcareAuthority.objects.filter(authority_code=code).exists():
            code = f"{original_code}{counter}"
            counter += 1
            
        return code

    @property
    def is_verification_due(self):
        """Check if authority information verification is due"""
        if not self.last_verified:
            return True
            
        from datetime import timedelta
        # Verify annually
        due_date = self.last_verified + timedelta(days=365)
        return timezone.now().date() > due_date

    @property
    def processing_efficiency_score(self):
        """Calculate processing efficiency score based on processing times"""
        scores = []
        
        # Score based on application processing days (lower is better)
        if self.application_processing_days:
            if self.application_processing_days <= 7:
                scores.append(10)
            elif self.application_processing_days <= 14:
                scores.append(8)
            elif self.application_processing_days <= 30:
                scores.append(6)
            elif self.application_processing_days <= 60:
                scores.append(4)
            else:
                scores.append(2)
        
        # Score based on response time (lower is better)
        if self.response_time_hours:
            if self.response_time_hours <= 24:
                scores.append(10)
            elif self.response_time_hours <= 48:
                scores.append(8)
            elif self.response_time_hours <= 72:
                scores.append(6)
            else:
                scores.append(4)
        
        return sum(scores) / len(scores) if scores else None

    def get_license_types(self):
        """Get formatted list of license types"""
        return self.license_types_issued if self.license_types_issued else []

    def get_supported_languages(self):
        """Get formatted list of supported languages"""
        return self.languages_supported if self.languages_supported else ['English']

    def get_digital_capabilities(self):
        """Get summary of digital capabilities"""
        capabilities = []
        
        if self.has_api_integration:
            capabilities.append('API Integration')
        if self.supports_electronic_submission:
            capabilities.append('Electronic Submission')
        if self.digital_signature_accepted:
            capabilities.append('Digital Signatures')
        if self.licensing_portal_url:
            capabilities.append('Online Portal')
        
        return capabilities

    def estimate_license_processing_time(self, license_type='standard'):
        """Estimate processing time for license application"""
        base_days = self.application_processing_days or 30
        
        # Adjust based on digital capabilities
        if self.supports_electronic_submission:
            base_days = int(base_days * 0.8)  # 20% faster with electronic submission
        
        if self.has_api_integration:
            base_days = int(base_days * 0.7)  # 30% faster with API integration
        
        return max(base_days, 1)  # Minimum 1 day

    def get_contact_summary(self):
        """Get contact information summary"""
        contacts = {}
        
        if self.primary_contact_name:
            contacts['primary'] = {
                'name': self.primary_contact_name,
                'title': self.primary_contact_title,
                'phone': self.primary_contact_phone,
                'email': self.primary_contact_email
            }
        
        if self.licensing_officer_name:
            contacts['licensing'] = {
                'name': self.licensing_officer_name,
                'phone': self.licensing_officer_phone,
                'email': self.licensing_officer_email
            }
        
        contacts['general'] = {
            'phone': self.phone_number,
            'email': self.email,
            'website': self.website
        }
        
        return contacts

    def get_fee_summary(self):
        """Get fee structure summary"""
        return {
            'standard_license': f"{self.standard_license_fee} {self.currency}" if self.standard_license_fee else "Not specified",
            'renewal': f"{self.renewal_fee} {self.currency}" if self.renewal_fee else "Not specified",
            'inspection': f"{self.inspection_fee} {self.currency}" if self.inspection_fee else "Not specified",
            'currency': self.currency
        }

    def update_performance_metrics(self, processing_days=None, response_hours=None, 
                                 satisfaction_score=None):
        """Update performance metrics"""
        if processing_days:
            self.application_processing_days = processing_days
        
        if response_hours:
            self.response_time_hours = response_hours
        
        if satisfaction_score:
            self.customer_satisfaction_score = satisfaction_score
        
        self.last_verified = timezone.now().date()
        self.save()

    def mark_as_verified(self, verification_source, user=None):
        """Mark authority information as verified"""
        self.last_verified = timezone.now().date()
        self.verification_source = verification_source
        if user:
            self.last_modified_by = user
        self.save()

    @classmethod
    def get_by_country(cls, country):
        """Get authorities by country"""
        return cls.objects.filter(
            country__iexact=country,
            is_active=True
        ).order_by('authority_type', 'name')

    @classmethod
    def get_by_jurisdiction_level(cls, level):
        """Get authorities by jurisdiction level"""
        return cls.objects.filter(
            jurisdiction_level=level,
            is_active=True
        ).order_by('country', 'name')

    @classmethod
    def get_verification_due(cls):
        """Get authorities that need verification"""
        from datetime import timedelta
        one_year_ago = timezone.now().date() - timedelta(days=365)
        
        return cls.objects.filter(
            models.Q(last_verified__lt=one_year_ago) |
            models.Q(last_verified__isnull=True),
            is_active=True
        ).order_by('last_verified')

    @classmethod
    def get_digital_enabled(cls):
        """Get authorities with digital capabilities"""
        return cls.objects.filter(
            models.Q(has_api_integration=True) |
            models.Q(supports_electronic_submission=True) |
            models.Q(digital_signature_accepted=True),
            is_active=True
        ).order_by('country', 'name')

    @classmethod
    def get_performance_summary(cls, country=None):
        """Get performance summary statistics"""
        queryset = cls.objects.filter(is_active=True)
        
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        from django.db.models import Avg, Count
        
        return queryset.aggregate(
            total_authorities=Count('id'),
            avg_processing_days=Avg('application_processing_days'),
            avg_response_hours=Avg('response_time_hours'),
            avg_satisfaction=Avg('customer_satisfaction_score'),
            digital_enabled=Count('id', filter=models.Q(has_api_integration=True))
        )