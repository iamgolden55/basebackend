from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class BillingSystem(models.Model):
    """
    Model representing third-party billing systems and platforms
    """
    SYSTEM_TYPE_CHOICES = [
        ('comprehensive', 'Comprehensive Healthcare Billing'),
        ('insurance_focused', 'Insurance Claims Focused'),
        ('patient_billing', 'Patient Billing Focused'),
        ('revenue_cycle', 'Revenue Cycle Management'),
        ('clearinghouse', 'Claims Clearinghouse'),
        ('payment_processor', 'Payment Processor'),
        ('analytics', 'Billing Analytics Platform'),
        ('integration', 'Integration Platform'),
        ('specialty', 'Specialty Billing System'),
        ('government', 'Government Billing System'),
        ('other', 'Other System Type')
    ]
    
    DEPLOYMENT_TYPE_CHOICES = [
        ('cloud', 'Cloud-Based (SaaS)'),
        ('on_premise', 'On-Premise'),
        ('hybrid', 'Hybrid Deployment'),
        ('hosted', 'Hosted Solution'),
        ('api_only', 'API-Only Service')
    ]
    
    INTEGRATION_COMPLEXITY_CHOICES = [
        ('simple', 'Simple Integration'),
        ('moderate', 'Moderate Complexity'),
        ('complex', 'Complex Integration'),
        ('enterprise', 'Enterprise Level'),
        ('custom', 'Custom Integration Required')
    ]
    
    CERTIFICATION_STATUS_CHOICES = [
        ('certified', 'Certified'),
        ('pending', 'Certification Pending'),
        ('not_certified', 'Not Certified'),
        ('expired', 'Certification Expired'),
        ('revoked', 'Certification Revoked')
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Name of the billing system"
    )
    vendor_name = models.CharField(
        max_length=200,
        help_text="Name of the vendor/company"
    )
    system_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique identifier code"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Current version of the system"
    )
    
    # System Classification
    system_type = models.CharField(
        max_length=20,
        choices=SYSTEM_TYPE_CHOICES,
        default='comprehensive'
    )
    deployment_type = models.CharField(
        max_length=20,
        choices=DEPLOYMENT_TYPE_CHOICES,
        default='cloud'
    )
    integration_complexity = models.CharField(
        max_length=20,
        choices=INTEGRATION_COMPLEXITY_CHOICES,
        default='moderate'
    )
    
    # Vendor Information
    vendor_website = models.URLField(
        blank=True,
        help_text="Vendor's official website"
    )
    vendor_headquarters = models.CharField(
        max_length=200,
        blank=True,
        help_text="Vendor headquarters location"
    )
    vendor_founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year vendor was founded"
    )
    vendor_size = models.CharField(
        max_length=20,
        choices=[
            ('startup', 'Startup (< 50 employees)'),
            ('small', 'Small (50-200 employees)'),
            ('medium', 'Medium (200-1000 employees)'),
            ('large', 'Large (1000-5000 employees)'),
            ('enterprise', 'Enterprise (> 5000 employees)')
        ],
        blank=True,
        help_text="Size of vendor company"
    )
    
    # Geographic Coverage
    supported_countries = models.JSONField(
        default=list,
        help_text="List of countries where system is supported"
    )
    supported_regions = models.JSONField(
        default=list,
        help_text="Specific regions or states supported"
    )
    primary_market = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary geographic market"
    )
    
    # Functionality and Features
    core_features = models.JSONField(
        default=list,
        help_text="Core features of the billing system"
    )
    supported_billing_types = models.JSONField(
        default=list,
        help_text="Types of billing supported (e.g., insurance, patient, government)"
    )
    supported_payment_methods = models.JSONField(
        default=list,
        help_text="Payment methods supported"
    )
    revenue_cycle_features = models.JSONField(
        default=list,
        help_text="Revenue cycle management features"
    )
    
    # Insurance and Claims
    insurance_claim_processing = models.BooleanField(
        default=True,
        help_text="Whether system processes insurance claims"
    )
    supported_insurance_types = models.JSONField(
        default=list,
        help_text="Types of insurance supported"
    )
    claims_clearinghouse_partners = models.JSONField(
        default=list,
        help_text="Clearinghouse partners for claims submission"
    )
    electronic_claims_submission = models.BooleanField(
        default=True,
        help_text="Whether electronic claims submission is supported"
    )
    real_time_eligibility_verification = models.BooleanField(
        default=False,
        help_text="Whether real-time eligibility verification is available"
    )
    
    # Technical Specifications
    api_available = models.BooleanField(
        default=False,
        help_text="Whether API is available for integration"
    )
    api_documentation_url = models.URLField(
        blank=True,
        help_text="URL to API documentation"
    )
    api_version = models.CharField(
        max_length=20,
        blank=True,
        help_text="Current API version"
    )
    webhook_support = models.BooleanField(
        default=False,
        help_text="Whether webhooks are supported"
    )
    
    # Integration Details
    integration_methods = models.JSONField(
        default=list,
        help_text="Available integration methods (API, HL7, file transfer, etc.)"
    )
    data_formats_supported = models.JSONField(
        default=list,
        help_text="Supported data formats (JSON, XML, CSV, HL7, etc.)"
    )
    hl7_support = models.BooleanField(
        default=False,
        help_text="Whether HL7 messaging is supported"
    )
    fhir_support = models.BooleanField(
        default=False,
        help_text="Whether FHIR standard is supported"
    )
    
    # Security and Compliance
    hipaa_compliant = models.BooleanField(
        default=False,
        help_text="Whether system is HIPAA compliant"
    )
    sox_compliant = models.BooleanField(
        default=False,
        help_text="Whether system is SOX compliant"
    )
    pci_dss_compliant = models.BooleanField(
        default=False,
        help_text="Whether system is PCI DSS compliant"
    )
    gdpr_compliant = models.BooleanField(
        default=False,
        help_text="Whether system is GDPR compliant"
    )
    security_certifications = models.JSONField(
        default=list,
        help_text="List of security certifications"
    )
    data_encryption = models.BooleanField(
        default=True,
        help_text="Whether data encryption is implemented"
    )
    
    # Performance Metrics
    uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="System uptime percentage"
    )
    average_response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average API response time in milliseconds"
    )
    transaction_volume_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Daily transaction volume capacity"
    )
    concurrent_user_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum concurrent users supported"
    )
    
    # Pricing Structure
    pricing_model = models.CharField(
        max_length=50,
        choices=[
            ('subscription', 'Monthly/Annual Subscription'),
            ('per_transaction', 'Per Transaction'),
            ('per_user', 'Per User'),
            ('percentage', 'Percentage of Revenue'),
            ('flat_fee', 'Flat Fee'),
            ('tiered', 'Tiered Pricing'),
            ('custom', 'Custom Pricing'),
            ('freemium', 'Freemium Model')
        ],
        blank=True,
        help_text="Pricing model used by the system"
    )
    base_monthly_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base monthly cost"
    )
    per_transaction_fee = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Fee per transaction"
    )
    setup_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="One-time setup fee"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for pricing"
    )
    
    # Implementation and Support
    implementation_time_weeks = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical implementation time in weeks"
    )
    training_provided = models.BooleanField(
        default=True,
        help_text="Whether training is provided"
    )
    support_channels = models.JSONField(
        default=list,
        help_text="Available support channels (phone, email, chat, etc.)"
    )
    support_hours = models.CharField(
        max_length=100,
        blank=True,
        help_text="Support hours (e.g., 24/7, business hours)"
    )
    dedicated_account_manager = models.BooleanField(
        default=False,
        help_text="Whether dedicated account manager is provided"
    )
    
    # Customer Information
    total_customers = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of customers"
    )
    healthcare_customers = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of healthcare customers"
    )
    customer_satisfaction_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Customer satisfaction rating (1-10)"
    )
    customer_retention_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Customer retention rate percentage"
    )
    
    # Certifications and Compliance
    certification_status = models.CharField(
        max_length=20,
        choices=CERTIFICATION_STATUS_CHOICES,
        default='not_certified'
    )
    certification_body = models.CharField(
        max_length=200,
        blank=True,
        help_text="Certification body or authority"
    )
    certification_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of certification"
    )
    certification_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Certification expiry date"
    )
    audit_frequency = models.CharField(
        max_length=20,
        choices=[
            ('annual', 'Annual'),
            ('biannual', 'Bi-Annual'),
            ('quarterly', 'Quarterly'),
            ('on_demand', 'On Demand'),
            ('continuous', 'Continuous')
        ],
        blank=True,
        help_text="Frequency of compliance audits"
    )
    
    # Reporting and Analytics
    reporting_capabilities = models.JSONField(
        default=list,
        help_text="Available reporting capabilities"
    )
    analytics_features = models.JSONField(
        default=list,
        help_text="Analytics features available"
    )
    custom_reporting = models.BooleanField(
        default=False,
        help_text="Whether custom reporting is available"
    )
    real_time_dashboards = models.BooleanField(
        default=False,
        help_text="Whether real-time dashboards are available"
    )
    
    # Integration Partnerships
    ehr_integrations = models.JSONField(
        default=list,
        help_text="EHR systems with direct integrations"
    )
    practice_management_integrations = models.JSONField(
        default=list,
        help_text="Practice management systems with integrations"
    )
    payment_processor_partnerships = models.JSONField(
        default=list,
        help_text="Payment processor partnerships"
    )
    marketplace_listings = models.JSONField(
        default=list,
        help_text="Marketplace listings (AWS, Azure, etc.)"
    )
    
    # Contact Information
    sales_contact_email = models.EmailField(
        blank=True,
        help_text="Sales contact email"
    )
    sales_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Sales contact phone"
    )
    support_contact_email = models.EmailField(
        blank=True,
        help_text="Support contact email"
    )
    support_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Support contact phone"
    )
    
    # Reviews and Ratings
    industry_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Industry rating (1-10)"
    )
    ease_of_use_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Ease of use rating (1-10)"
    )
    feature_completeness_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Feature completeness rating (1-10)"
    )
    customer_reviews = models.JSONField(
        default=list,
        help_text="Customer reviews and testimonials"
    )
    
    # Competitive Analysis
    main_competitors = models.JSONField(
        default=list,
        help_text="Main competitor systems"
    )
    competitive_advantages = models.TextField(
        blank=True,
        help_text="Key competitive advantages"
    )
    unique_features = models.JSONField(
        default=list,
        help_text="Unique features not found in competitors"
    )
    
    # Risk Assessment
    vendor_stability_risk = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical Risk')
        ],
        default='medium',
        help_text="Vendor stability risk assessment"
    )
    technology_risk = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical Risk')
        ],
        default='medium',
        help_text="Technology risk assessment"
    )
    security_risk = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical Risk')
        ],
        default='medium',
        help_text="Security risk assessment"
    )
    
    # Status and Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether billing system is currently active/available"
    )
    is_recommended = models.BooleanField(
        default=False,
        help_text="Whether this system is recommended by organization"
    )
    last_evaluated = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last evaluation"
    )
    evaluation_source = models.CharField(
        max_length=200,
        blank=True,
        help_text="Source of last evaluation"
    )
    
    # Additional Information
    implementation_notes = models.TextField(
        blank=True,
        help_text="Notes about implementation considerations"
    )
    known_issues = models.TextField(
        blank=True,
        help_text="Known issues or limitations"
    )
    recent_updates = models.TextField(
        blank=True,
        help_text="Recent updates or changes to the system"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the billing system"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_billing_systems',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_billing_systems',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['system_code']),
            models.Index(fields=['vendor_name']),
            models.Index(fields=['system_type']),
            models.Index(fields=['deployment_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_recommended']),
            models.Index(fields=['certification_status']),
        ]
        permissions = [
            ("can_manage_billing_systems", "Can manage billing systems"),
            ("can_evaluate_billing_systems", "Can evaluate billing systems"),
            ("can_view_billing_system_details", "Can view billing system details"),
        ]

    def __str__(self):
        return f"{self.name} by {self.vendor_name}"

    def clean(self):
        """Validate billing system data"""
        super().clean()
        
        # Generate system code if not provided
        if not self.system_code:
            self.system_code = self.generate_system_code()
        
        # Validate certification dates
        if self.certification_date and self.certification_expiry_date:
            if self.certification_date > self.certification_expiry_date:
                raise ValidationError(
                    "Certification date must be before expiry date"
                )
        
        # Validate ratings are within range
        rating_fields = [
            ('customer_satisfaction_rating', 1, 10),
            ('industry_rating', 1, 10),
            ('ease_of_use_rating', 1, 10),
            ('feature_completeness_rating', 1, 10)
        ]
        
        for field_name, min_val, max_val in rating_fields:
            value = getattr(self, field_name)
            if value is not None and (value < min_val or value > max_val):
                raise ValidationError(
                    f"{field_name} must be between {min_val} and {max_val}"
                )
        
        # Validate percentages
        percentage_fields = [
            'uptime_percentage',
            'customer_retention_rate'
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

    def generate_system_code(self):
        """Generate unique system code"""
        import re
        import random
        
        # Create code from vendor and system name
        vendor_code = re.sub(r'[^A-Za-z]', '', self.vendor_name)[:2].upper()
        system_code = re.sub(r'[^A-Za-z]', '', self.name)[:3].upper()
        
        # Add random number
        suffix = str(random.randint(10, 99))
        code = f"{vendor_code}{system_code}{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while BillingSystem.objects.filter(system_code=code).exists():
            code = f"{original_code}{counter}"
            counter += 1
            
        return code

    @property
    def is_certification_expiring_soon(self):
        """Check if certification is expiring within 90 days"""
        if not self.certification_expiry_date:
            return False
            
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=90)
        return self.certification_expiry_date <= warning_date

    @property
    def is_certification_expired(self):
        """Check if certification is expired"""
        if not self.certification_expiry_date:
            return False
        return timezone.now().date() > self.certification_expiry_date

    @property
    def overall_rating(self):
        """Calculate overall rating from component ratings"""
        ratings = []
        
        if self.industry_rating:
            ratings.append(float(self.industry_rating))
        if self.ease_of_use_rating:
            ratings.append(float(self.ease_of_use_rating))
        if self.feature_completeness_rating:
            ratings.append(float(self.feature_completeness_rating))
        if self.customer_satisfaction_rating:
            ratings.append(float(self.customer_satisfaction_rating))
        
        if not ratings:
            return None
        
        return round(sum(ratings) / len(ratings), 1)

    @property
    def estimated_monthly_cost(self):
        """Estimate monthly cost based on pricing model"""
        if self.base_monthly_cost:
            return self.base_monthly_cost
        
        # For other pricing models, return a placeholder or None
        return None

    @property
    def risk_score(self):
        """Calculate overall risk score"""
        risk_values = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        risks = [
            risk_values.get(self.vendor_stability_risk, 2),
            risk_values.get(self.technology_risk, 2),
            risk_values.get(self.security_risk, 2)
        ]
        
        avg_risk = sum(risks) / len(risks)
        
        if avg_risk <= 1.5:
            return 'Low'
        elif avg_risk <= 2.5:
            return 'Medium'
        elif avg_risk <= 3.5:
            return 'High'
        else:
            return 'Critical'

    def get_core_features_summary(self):
        """Get summary of core features"""
        if not self.core_features:
            return []
        
        # Return first 5 features for summary
        return self.core_features[:5]

    def get_supported_countries_list(self):
        """Get formatted list of supported countries"""
        if not self.supported_countries:
            return ["Not specified"]
        
        return self.supported_countries

    def get_integration_summary(self):
        """Get integration capabilities summary"""
        summary = {
            'api_available': self.api_available,
            'webhook_support': self.webhook_support,
            'hl7_support': self.hl7_support,
            'fhir_support': self.fhir_support,
            'complexity': self.get_integration_complexity_display(),
            'methods': self.integration_methods if self.integration_methods else []
        }
        
        return summary

    def get_compliance_summary(self):
        """Get compliance and security summary"""
        compliance = {
            'hipaa': self.hipaa_compliant,
            'sox': self.sox_compliant,
            'pci_dss': self.pci_dss_compliant,
            'gdpr': self.gdpr_compliant,
            'encryption': self.data_encryption,
            'certifications': self.security_certifications if self.security_certifications else []
        }
        
        return compliance

    def get_pricing_summary(self):
        """Get pricing structure summary"""
        pricing = {
            'model': self.get_pricing_model_display() if self.pricing_model else 'Not specified',
            'base_monthly': f"{self.base_monthly_cost} {self.currency}" if self.base_monthly_cost else None,
            'per_transaction': f"{self.per_transaction_fee} {self.currency}" if self.per_transaction_fee else None,
            'setup_fee': f"{self.setup_fee} {self.currency}" if self.setup_fee else None
        }
        
        return pricing

    def get_performance_summary(self):
        """Get performance metrics summary"""
        performance = {
            'uptime': f"{self.uptime_percentage}%" if self.uptime_percentage else None,
            'response_time': f"{self.average_response_time_ms}ms" if self.average_response_time_ms else None,
            'capacity': self.transaction_volume_capacity,
            'concurrent_users': self.concurrent_user_capacity
        }
        
        return performance

    def get_support_summary(self):
        """Get support and implementation summary"""
        support = {
            'implementation_weeks': self.implementation_time_weeks,
            'training_provided': self.training_provided,
            'support_channels': self.support_channels if self.support_channels else [],
            'support_hours': self.support_hours,
            'dedicated_manager': self.dedicated_account_manager
        }
        
        return support

    def assess_suitability(self, organization_type='hospital', 
                          required_features=None, budget_limit=None,
                          integration_requirements=None):
        """Assess suitability for an organization"""
        suitability_score = 0
        recommendations = []
        
        # Feature assessment
        if required_features:
            available_features = set(self.core_features) if self.core_features else set()
            required_set = set(required_features)
            
            if required_set.issubset(available_features):
                suitability_score += 30
                recommendations.append("All required features are available")
            else:
                missing = required_set - available_features
                suitability_score += max(0, 30 - len(missing) * 5)
                recommendations.append(f"Missing features: {', '.join(missing)}")
        
        # Budget assessment
        if budget_limit and self.estimated_monthly_cost:
            if self.estimated_monthly_cost <= budget_limit:
                suitability_score += 25
                recommendations.append("Within budget range")
            else:
                budget_ratio = budget_limit / self.estimated_monthly_cost
                suitability_score += int(25 * budget_ratio)
                recommendations.append("Exceeds budget - consider negotiating or looking for alternatives")
        
        # Integration assessment
        if integration_requirements:
            integration_score = 0
            if 'api' in integration_requirements and self.api_available:
                integration_score += 10
            if 'hl7' in integration_requirements and self.hl7_support:
                integration_score += 10
            if 'fhir' in integration_requirements and self.fhir_support:
                integration_score += 5
            
            suitability_score += integration_score
        
        # Compliance assessment
        if organization_type == 'hospital':
            if self.hipaa_compliant:
                suitability_score += 15
                recommendations.append("HIPAA compliant")
            else:
                recommendations.append("Warning: Not HIPAA compliant")
        
        # Overall rating contribution
        if self.overall_rating:
            rating_score = int((self.overall_rating / 10) * 10)
            suitability_score += rating_score
        
        return {
            'suitability_score': min(100, suitability_score),
            'suitability_level': self._get_suitability_level(suitability_score),
            'recommendations': recommendations,
            'risk_level': self.risk_score
        }

    def _get_suitability_level(self, score):
        """Convert suitability score to level"""
        if score >= 80:
            return "Excellent Match"
        elif score >= 60:
            return "Good Match"
        elif score >= 40:
            return "Fair Match"
        else:
            return "Poor Match"

    def get_competitive_analysis(self):
        """Get competitive analysis summary"""
        return {
            'main_competitors': self.main_competitors if self.main_competitors else [],
            'competitive_advantages': self.competitive_advantages,
            'unique_features': self.unique_features if self.unique_features else [],
            'overall_rating': self.overall_rating,
            'market_position': self._determine_market_position()
        }

    def _determine_market_position(self):
        """Determine market position based on various factors"""
        factors = []
        
        if self.total_customers and self.total_customers > 1000:
            factors.append("Large customer base")
        
        if self.overall_rating and self.overall_rating >= 8:
            factors.append("High rated")
        
        if self.vendor_size in ['large', 'enterprise']:
            factors.append("Established vendor")
        
        if len(factors) >= 2:
            return "Market Leader"
        elif len(factors) == 1:
            return "Strong Contender"
        else:
            return "Emerging Player"

    @classmethod
    def get_recommended_systems(cls, system_type=None, deployment_type=None):
        """Get recommended billing systems"""
        queryset = cls.objects.filter(
            is_active=True,
            is_recommended=True
        )
        
        if system_type:
            queryset = queryset.filter(system_type=system_type)
        
        if deployment_type:
            queryset = queryset.filter(deployment_type=deployment_type)
        
        return queryset.order_by('-industry_rating', 'name')

    @classmethod
    def get_by_features(cls, required_features):
        """Get systems that support specific features"""
        queryset = cls.objects.filter(is_active=True)
        
        for feature in required_features:
            queryset = queryset.filter(core_features__contains=[feature])
        
        return queryset.order_by('-industry_rating', 'name')

    @classmethod
    def get_by_budget_range(cls, min_budget=None, max_budget=None):
        """Get systems within budget range"""
        queryset = cls.objects.filter(is_active=True)
        
        if min_budget:
            queryset = queryset.filter(base_monthly_cost__gte=min_budget)
        
        if max_budget:
            queryset = queryset.filter(base_monthly_cost__lte=max_budget)
        
        return queryset.order_by('base_monthly_cost', 'name')

    @classmethod
    def get_comparison_matrix(cls, system_ids):
        """Get comparison matrix for multiple systems"""
        systems = cls.objects.filter(id__in=system_ids, is_active=True)
        
        comparison_data = []
        for system in systems:
            comparison_data.append({
                'name': system.name,
                'vendor': system.vendor_name,
                'type': system.get_system_type_display(),
                'deployment': system.get_deployment_type_display(),
                'pricing_model': system.get_pricing_model_display(),
                'monthly_cost': system.base_monthly_cost,
                'api_available': system.api_available,
                'hipaa_compliant': system.hipaa_compliant,
                'overall_rating': system.overall_rating,
                'implementation_weeks': system.implementation_time_weeks,
                'risk_score': system.risk_score
            })
        
        return comparison_data

    @classmethod
    def get_market_analysis(cls):
        """Get market analysis of billing systems"""
        from django.db.models import Avg, Count
        
        active_systems = cls.objects.filter(is_active=True)
        
        return {
            'total_systems': active_systems.count(),
            'by_type': active_systems.values('system_type').annotate(count=Count('id')),
            'by_deployment': active_systems.values('deployment_type').annotate(count=Count('id')),
            'avg_rating': active_systems.aggregate(avg_rating=Avg('industry_rating'))['avg_rating'],
            'avg_monthly_cost': active_systems.aggregate(avg_cost=Avg('base_monthly_cost'))['avg_cost'],
            'hipaa_compliant_count': active_systems.filter(hipaa_compliant=True).count(),
            'api_enabled_count': active_systems.filter(api_available=True).count(),
            'recommended_count': active_systems.filter(is_recommended=True).count()
        }