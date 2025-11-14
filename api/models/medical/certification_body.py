from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class CertificationBody(models.Model):
    """
    Model representing quality certification and accreditation organizations
    """
    ORGANIZATION_TYPE_CHOICES = [
        ('international', 'International Organization'),
        ('national', 'National Accreditation Body'),
        ('regional', 'Regional Certification Body'),
        ('professional', 'Professional Association'),
        ('government', 'Government Agency'),
        ('industry', 'Industry Association'),
        ('third_party', 'Third-Party Certifier')
    ]
    
    CERTIFICATION_SCOPE_CHOICES = [
        ('healthcare_general', 'General Healthcare'),
        ('hospital_accreditation', 'Hospital Accreditation'),
        ('quality_management', 'Quality Management Systems'),
        ('patient_safety', 'Patient Safety'),
        ('laboratory', 'Laboratory Services'),
        ('medical_devices', 'Medical Devices'),
        ('information_security', 'Information Security'),
        ('environmental', 'Environmental Management'),
        ('specialty_care', 'Specialty Care'),
        ('emergency_services', 'Emergency Services'),
        ('surgical_services', 'Surgical Services'),
        ('nursing_care', 'Nursing Care'),
        ('pharmacy', 'Pharmacy Services'),
        ('imaging', 'Medical Imaging'),
        ('other', 'Other Certification Scope')
    ]
    
    RECOGNITION_LEVEL_CHOICES = [
        ('international', 'Internationally Recognized'),
        ('national', 'Nationally Recognized'),
        ('regional', 'Regionally Recognized'),
        ('industry', 'Industry Recognized'),
        ('local', 'Locally Recognized')
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Official name of the certification body"
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Abbreviated name or acronym"
    )
    organization_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique identifier code"
    )
    
    # Organization Details
    organization_type = models.CharField(
        max_length=20,
        choices=ORGANIZATION_TYPE_CHOICES,
        default='professional'
    )
    certification_scope = models.CharField(
        max_length=30,
        choices=CERTIFICATION_SCOPE_CHOICES,
        default='healthcare_general'
    )
    recognition_level = models.CharField(
        max_length=20,
        choices=RECOGNITION_LEVEL_CHOICES,
        default='national'
    )
    
    # Geographic Information
    headquarters_country = models.CharField(
        max_length=100,
        help_text="Country where organization is headquartered"
    )
    operating_countries = models.JSONField(
        default=list,
        help_text="List of countries where certifications are offered"
    )
    regional_offices = models.JSONField(
        default=list,
        help_text="List of regional office locations"
    )
    
    # Contact Information
    headquarters_address = models.TextField(
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
    
    # Certification Programs
    certification_programs = models.JSONField(
        default=list,
        help_text="List of certification programs offered"
    )
    accreditation_standards = models.JSONField(
        default=list,
        help_text="List of standards used for accreditation"
    )
    assessment_methodologies = models.TextField(
        blank=True,
        help_text="Description of assessment methodologies"
    )
    
    # Application and Assessment Process
    application_portal_url = models.URLField(
        blank=True,
        help_text="URL for certification applications"
    )
    application_processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average days to process applications"
    )
    assessment_duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical duration of assessment process"
    )
    on_site_assessment_required = models.BooleanField(
        default=True,
        help_text="Whether on-site assessment is required"
    )
    
    # Certification Validity and Renewal
    certification_validity_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of years certification is valid"
    )
    renewal_assessment_required = models.BooleanField(
        default=True,
        help_text="Whether renewal requires reassessment"
    )
    surveillance_assessments = models.BooleanField(
        default=False,
        help_text="Whether regular surveillance assessments are conducted"
    )
    surveillance_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Frequency of surveillance assessments in months"
    )
    
    # Fees and Costs
    application_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Application fee amount"
    )
    assessment_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Assessment fee amount"
    )
    annual_maintenance_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual maintenance fee"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for fees"
    )
    
    # Quality and Performance Metrics
    pass_rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of applicants who pass assessment"
    )
    average_assessment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average assessment score"
    )
    customer_satisfaction_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Customer satisfaction rating (1-10)"
    )
    
    # Reputation and Recognition
    industry_reputation_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Industry reputation score (1-10)"
    )
    years_in_operation = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of years in operation"
    )
    total_organizations_certified = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of organizations certified"
    )
    
    # Digital Capabilities
    has_online_portal = models.BooleanField(
        default=False,
        help_text="Whether online application portal is available"
    )
    supports_digital_assessment = models.BooleanField(
        default=False,
        help_text="Whether digital/remote assessments are supported"
    )
    provides_digital_certificates = models.BooleanField(
        default=False,
        help_text="Whether digital certificates are provided"
    )
    has_api_integration = models.BooleanField(
        default=False,
        help_text="Whether API integration is available"
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
    primary_contact_email = models.EmailField(
        blank=True
    )
    primary_contact_phone = models.CharField(
        max_length=20,
        blank=True
    )
    
    # Assessment Team Information
    lead_assessor_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Lead assessor or director"
    )
    assessor_qualifications = models.TextField(
        blank=True,
        help_text="Required qualifications for assessors"
    )
    number_of_assessors = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of qualified assessors"
    )
    
    # Operating Information
    business_hours = models.TextField(
        blank=True,
        help_text="Business hours and time zones"
    )
    languages_supported = models.JSONField(
        default=list,
        help_text="Languages supported for assessments"
    )
    emergency_contact_available = models.BooleanField(
        default=False,
        help_text="Whether emergency contact is available"
    )
    
    # Compliance and Accreditation
    is_accredited_by = models.TextField(
        blank=True,
        help_text="Organizations that accredit this certification body"
    )
    iso_17021_compliant = models.BooleanField(
        default=False,
        help_text="Whether compliant with ISO/IEC 17021"
    )
    government_recognized = models.BooleanField(
        default=False,
        help_text="Whether recognized by government authorities"
    )
    mutual_recognition_agreements = models.JSONField(
        default=list,
        help_text="List of mutual recognition agreements"
    )
    
    # Performance and Reliability
    response_time_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical response time for inquiries in hours"
    )
    assessment_completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of assessments completed on time"
    )
    last_performance_review = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last performance review"
    )
    
    # Status and Verification
    is_active = models.BooleanField(
        default=True,
        help_text="Whether certification body is currently active"
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
    special_requirements = models.TextField(
        blank=True,
        help_text="Special requirements or prerequisites"
    )
    notable_achievements = models.TextField(
        blank=True,
        help_text="Notable achievements or recognitions"
    )
    recent_changes = models.TextField(
        blank=True,
        help_text="Recent changes to standards or processes"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the certification body"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_certification_bodies',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_certification_bodies',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Certification Bodies"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['organization_code']),
            models.Index(fields=['headquarters_country']),
            models.Index(fields=['organization_type']),
            models.Index(fields=['certification_scope']),
            models.Index(fields=['recognition_level']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("can_manage_certification_bodies", "Can manage certification bodies"),
            ("can_verify_certification_data", "Can verify certification information"),
            ("can_view_performance_data", "Can view performance metrics"),
        ]

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} ({self.headquarters_country})"
        return f"{self.name} ({self.headquarters_country})"

    def clean(self):
        """Validate certification body data"""
        super().clean()
        
        # Generate organization code if not provided
        if not self.organization_code:
            self.organization_code = self.generate_organization_code()
        
        # Validate ratings are within range
        rating_fields = [
            ('customer_satisfaction_rating', 1, 10),
            ('industry_reputation_score', 1, 10)
        ]
        
        for field_name, min_val, max_val in rating_fields:
            value = getattr(self, field_name)
            if value is not None and (value < min_val or value > max_val):
                raise ValidationError(
                    f"{field_name} must be between {min_val} and {max_val}"
                )
        
        # Validate percentages
        percentage_fields = [
            'pass_rate_percentage',
            'assessment_completion_rate'
        ]
        
        for field_name in percentage_fields:
            value = getattr(self, field_name)
            if value is not None and (value < 0 or value > 100):
                raise ValidationError(
                    f"{field_name} must be between 0 and 100"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    def generate_organization_code(self):
        """Generate unique organization code"""
        import re
        import random
        
        # Create code from country and name
        country_code = self.headquarters_country[:2].upper()
        
        # Remove non-alphabetic characters and take first 3 letters of name
        clean_name = re.sub(r'[^A-Za-z]', '', self.name)
        name_code = clean_name[:3].upper()
        
        # Add random number
        suffix = str(random.randint(10, 99))
        code = f"{country_code}{name_code}{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while CertificationBody.objects.filter(organization_code=code).exists():
            code = f"{original_code}{counter}"
            counter += 1
            
        return code

    @property
    def is_verification_due(self):
        """Check if certification body information verification is due"""
        if not self.last_verified:
            return True
            
        from datetime import timedelta
        # Verify annually
        due_date = self.last_verified + timedelta(days=365)
        return timezone.now().date() > due_date

    @property
    def total_certification_cost(self):
        """Calculate total cost for initial certification"""
        costs = []
        
        if self.application_fee:
            costs.append(self.application_fee)
        if self.assessment_fee:
            costs.append(self.assessment_fee)
        
        return sum(costs) if costs else None

    @property
    def annual_cost(self):
        """Calculate annual maintenance cost"""
        return self.annual_maintenance_fee or 0

    def get_certification_programs(self):
        """Get formatted list of certification programs"""
        return self.certification_programs if self.certification_programs else []

    def get_operating_countries(self):
        """Get formatted list of operating countries"""
        return self.operating_countries if self.operating_countries else [self.headquarters_country]

    def get_supported_languages(self):
        """Get formatted list of supported languages"""
        return self.languages_supported if self.languages_supported else ['English']

    def get_digital_capabilities(self):
        """Get summary of digital capabilities"""
        capabilities = []
        
        if self.has_online_portal:
            capabilities.append('Online Portal')
        if self.supports_digital_assessment:
            capabilities.append('Digital Assessment')
        if self.provides_digital_certificates:
            capabilities.append('Digital Certificates')
        if self.has_api_integration:
            capabilities.append('API Integration')
        
        return capabilities

    def estimate_certification_timeline(self):
        """Estimate total certification timeline in days"""
        timeline_days = 0
        
        if self.application_processing_days:
            timeline_days += self.application_processing_days
        
        if self.assessment_duration_days:
            timeline_days += self.assessment_duration_days
        
        # Add buffer for preparation time
        timeline_days += 30  # 30 days preparation
        
        return timeline_days

    def get_assessment_requirements(self):
        """Get assessment requirements summary"""
        requirements = {
            'on_site_required': self.on_site_assessment_required,
            'duration_days': self.assessment_duration_days,
            'preparation_time': '30 days recommended',
            'assessor_qualifications': self.assessor_qualifications
        }
        
        if self.special_requirements:
            requirements['special_requirements'] = self.special_requirements
        
        return requirements

    def get_renewal_requirements(self):
        """Get renewal requirements summary"""
        renewal_info = {
            'validity_years': self.certification_validity_years,
            'renewal_assessment_required': self.renewal_assessment_required,
            'surveillance_required': self.surveillance_assessments
        }
        
        if self.surveillance_assessments and self.surveillance_frequency_months:
            renewal_info['surveillance_frequency'] = f"Every {self.surveillance_frequency_months} months"
        
        return renewal_info

    def get_cost_summary(self):
        """Get cost structure summary"""
        costs = {
            'application_fee': f"{self.application_fee} {self.currency}" if self.application_fee else "Not specified",
            'assessment_fee': f"{self.assessment_fee} {self.currency}" if self.assessment_fee else "Not specified",
            'annual_maintenance': f"{self.annual_maintenance_fee} {self.currency}" if self.annual_maintenance_fee else "Not specified",
            'total_initial_cost': f"{self.total_certification_cost} {self.currency}" if self.total_certification_cost else "Not specified",
            'currency': self.currency
        }
        
        return costs

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
        
        if self.lead_assessor_name:
            contacts['lead_assessor'] = {
                'name': self.lead_assessor_name,
                'qualifications': self.assessor_qualifications
            }
        
        contacts['general'] = {
            'phone': self.phone_number,
            'email': self.email,
            'website': self.website
        }
        
        return contacts

    def update_performance_metrics(self, pass_rate=None, satisfaction_rating=None, 
                                 completion_rate=None):
        """Update performance metrics"""
        if pass_rate:
            self.pass_rate_percentage = pass_rate
        
        if satisfaction_rating:
            self.customer_satisfaction_rating = satisfaction_rating
        
        if completion_rate:
            self.assessment_completion_rate = completion_rate
        
        self.last_performance_review = timezone.now().date()
        self.save()

    def mark_as_verified(self, verification_source, user=None):
        """Mark certification body information as verified"""
        self.last_verified = timezone.now().date()
        self.verification_source = verification_source
        if user:
            self.last_modified_by = user
        self.save()

    def is_suitable_for_organization(self, organization_type, location=None, scope=None):
        """Check if certification body is suitable for an organization"""
        # Check geographic coverage
        if location and location not in self.get_operating_countries():
            return False, "Geographic coverage not available"
        
        # Check certification scope
        if scope and scope != self.certification_scope and self.certification_scope != 'healthcare_general':
            return False, "Certification scope mismatch"
        
        # Check if active
        if not self.is_active:
            return False, "Certification body is not active"
        
        return True, "Suitable for certification"

    @classmethod
    def get_by_country(cls, country):
        """Get certification bodies by country"""
        return cls.objects.filter(
            models.Q(headquarters_country__iexact=country) |
            models.Q(operating_countries__contains=[country]),
            is_active=True
        ).order_by('recognition_level', 'name')

    @classmethod
    def get_by_scope(cls, scope):
        """Get certification bodies by scope"""
        return cls.objects.filter(
            models.Q(certification_scope=scope) |
            models.Q(certification_scope='healthcare_general'),
            is_active=True
        ).order_by('recognition_level', 'industry_reputation_score')

    @classmethod
    def get_by_recognition_level(cls, level):
        """Get certification bodies by recognition level"""
        return cls.objects.filter(
            recognition_level=level,
            is_active=True
        ).order_by('industry_reputation_score', 'name')

    @classmethod
    def get_verification_due(cls):
        """Get certification bodies that need verification"""
        from datetime import timedelta
        one_year_ago = timezone.now().date() - timedelta(days=365)
        
        return cls.objects.filter(
            models.Q(last_verified__lt=one_year_ago) |
            models.Q(last_verified__isnull=True),
            is_active=True
        ).order_by('last_verified')

    @classmethod
    def get_top_rated(cls, country=None, scope=None, limit=10):
        """Get top-rated certification bodies"""
        queryset = cls.objects.filter(is_active=True)
        
        if country:
            queryset = queryset.filter(
                models.Q(headquarters_country__iexact=country) |
                models.Q(operating_countries__contains=[country])
            )
        
        if scope:
            queryset = queryset.filter(
                models.Q(certification_scope=scope) |
                models.Q(certification_scope='healthcare_general')
            )
        
        return queryset.order_by(
            '-industry_reputation_score',
            '-customer_satisfaction_rating',
            'name'
        )[:limit]

    @classmethod
    def get_performance_summary(cls, country=None):
        """Get performance summary statistics"""
        queryset = cls.objects.filter(is_active=True)
        
        if country:
            queryset = queryset.filter(
                models.Q(headquarters_country__iexact=country) |
                models.Q(operating_countries__contains=[country])
            )
        
        from django.db.models import Avg, Count
        
        return queryset.aggregate(
            total_bodies=Count('id'),
            avg_reputation_score=Avg('industry_reputation_score'),
            avg_satisfaction=Avg('customer_satisfaction_rating'),
            avg_pass_rate=Avg('pass_rate_percentage'),
            digital_enabled=Count('id', filter=models.Q(has_online_portal=True))
        )