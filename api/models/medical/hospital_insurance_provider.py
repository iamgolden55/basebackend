from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class HospitalInsuranceProvider(models.Model):
    """
    Model representing the relationship between hospitals and insurance providers
    """
    CONTRACT_STATUS_CHOICES = [
        ('active', 'Active Contract'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired')
    ]
    
    NETWORK_TYPE_CHOICES = [
        ('in_network', 'In-Network Provider'),
        ('out_of_network', 'Out-of-Network Provider'),
        ('preferred', 'Preferred Provider'),
        ('exclusive', 'Exclusive Provider')
    ]
    
    CLAIMS_SUBMISSION_METHOD_CHOICES = [
        ('electronic', 'Electronic Submission'),
        ('paper', 'Paper Submission'),
        ('portal', 'Insurance Portal'),
        ('edi', 'EDI Submission'),
        ('api', 'API Integration')
    ]
    
    # Relationship
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='insurance_relationships'
    )
    insurance_provider = models.ForeignKey(
        'api.InsuranceProvider',
        on_delete=models.CASCADE,
        related_name='hospital_relationships'
    )
    
    # Contract Information
    contract_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Hospital's contract number with insurance provider"
    )
    provider_id = models.CharField(
        max_length=50,
        help_text="Hospital's provider ID with this insurance company"
    )
    network_type = models.CharField(
        max_length=20,
        choices=NETWORK_TYPE_CHOICES,
        default='in_network'
    )
    contract_status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS_CHOICES,
        default='active'
    )
    
    # Contract Dates
    contract_start_date = models.DateField()
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for indefinite contracts"
    )
    last_renewal_date = models.DateField(
        null=True,
        blank=True
    )
    next_renewal_due = models.DateField(
        null=True,
        blank=True
    )
    
    # Financial Terms
    base_reimbursement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Base reimbursement percentage"
    )
    emergency_reimbursement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Emergency services reimbursement percentage"
    )
    specialist_reimbursement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Specialist consultation reimbursement percentage"
    )
    
    # Patient Costs
    standard_copay_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Standard copay amount for consultations"
    )
    specialist_copay_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Copay amount for specialist consultations"
    )
    emergency_copay_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Emergency services copay amount"
    )
    
    # Deductibles and Limits
    annual_deductible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Annual deductible amount"
    )
    visit_limit_per_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum visits per year (0 for unlimited)"
    )
    max_coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum coverage amount per year"
    )
    
    # Service Coverage
    covered_services = models.JSONField(
        default=list,
        help_text="List of covered services/specialties"
    )
    excluded_services = models.JSONField(
        default=list,
        help_text="List of excluded services/treatments"
    )
    requires_referral = models.JSONField(
        default=list,
        help_text="Services that require referral"
    )
    requires_preauthorization = models.JSONField(
        default=list,
        help_text="Services requiring pre-authorization"
    )
    
    # Claims Processing
    claims_submission_method = models.CharField(
        max_length=20,
        choices=CLAIMS_SUBMISSION_METHOD_CHOICES,
        default='electronic'
    )
    claims_contact_email = models.EmailField(
        blank=True,
        help_text="Email for claims submission"
    )
    claims_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone for claims inquiries"
    )
    claims_portal_url = models.URLField(
        blank=True,
        help_text="URL for claims submission portal"
    )
    average_claims_processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average days to process claims"
    )
    
    # Performance Metrics
    claims_approval_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of claims approved"
    )
    average_payment_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average days to receive payment"
    )
    
    # Contact Information
    primary_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary contact person at insurance company"
    )
    primary_contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email"
    )
    primary_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary contact phone"
    )
    
    # Administrative
    requires_credentialing = models.BooleanField(
        default=True,
        help_text="Whether doctors need to be credentialed individually"
    )
    credentialing_in_progress = models.BooleanField(
        default=False,
        help_text="Whether credentialing is currently in progress"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the relationship"
    )
    
    # Status and Alerts
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this relationship is currently active"
    )
    contract_renewal_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether renewal alert has been sent"
    )
    last_verification_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last time contract details were verified"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_hospital_insurance_relationships',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_hospital_insurance_relationships',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['hospital', 'insurance_provider']]
        ordering = ['hospital__name', 'insurance_provider__name']
        indexes = [
            models.Index(fields=['hospital', 'contract_status']),
            models.Index(fields=['insurance_provider', 'network_type']),
            models.Index(fields=['contract_end_date']),
            models.Index(fields=['next_renewal_due']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("can_manage_insurance_contracts", "Can manage insurance contracts"),
            ("can_view_financial_terms", "Can view financial terms"),
            ("can_update_performance_metrics", "Can update performance metrics"),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.insurance_provider.name} ({self.get_contract_status_display()})"

    def clean(self):
        """Validate hospital insurance relationship"""
        super().clean()
        
        if self.contract_end_date and self.contract_start_date > self.contract_end_date:
            raise ValidationError(
                "Contract start date must be before end date"
            )
        
        if self.next_renewal_due and self.contract_end_date and self.next_renewal_due > self.contract_end_date:
            raise ValidationError(
                "Next renewal due must be before contract end date"
            )
        
        # Validate reimbursement rates
        rates = [
            self.base_reimbursement_rate,
            self.emergency_reimbursement_rate,
            self.specialist_reimbursement_rate
        ]
        for rate in rates:
            if rate and rate > 100:
                raise ValidationError(
                    "Reimbursement rates cannot exceed 100%"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_contract_expiring_soon(self):
        """Check if contract is expiring within 60 days"""
        if not self.contract_end_date:
            return False
            
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=60)
        return self.contract_end_date <= warning_date

    @property
    def is_renewal_due(self):
        """Check if contract renewal is due"""
        if not self.next_renewal_due:
            return False
            
        return timezone.now().date() >= self.next_renewal_due

    @property
    def contract_days_remaining(self):
        """Calculate days remaining on contract"""
        if not self.contract_end_date:
            return None
            
        remaining = self.contract_end_date - timezone.now().date()
        return remaining.days if remaining.days >= 0 else 0

    def calculate_patient_cost(self, service_type='standard', total_amount=None):
        """Calculate patient's out-of-pocket cost"""
        if not total_amount:
            return None
            
        # Get appropriate copay and reimbursement rate
        if service_type == 'emergency':
            copay = self.emergency_copay_amount or Decimal('0')
            reimbursement_rate = self.emergency_reimbursement_rate or self.base_reimbursement_rate
        elif service_type == 'specialist':
            copay = self.specialist_copay_amount or self.standard_copay_amount or Decimal('0')
            reimbursement_rate = self.specialist_reimbursement_rate or self.base_reimbursement_rate
        else:
            copay = self.standard_copay_amount or Decimal('0')
            reimbursement_rate = self.base_reimbursement_rate
        
        # Calculate insurance coverage
        insurance_coverage = (total_amount * reimbursement_rate) / 100
        patient_cost = total_amount - insurance_coverage + copay
        
        return max(patient_cost, Decimal('0'))

    def calculate_insurance_coverage(self, service_type='standard', total_amount=None):
        """Calculate insurance coverage amount"""
        if not total_amount:
            return None
            
        # Get appropriate reimbursement rate
        if service_type == 'emergency':
            reimbursement_rate = self.emergency_reimbursement_rate or self.base_reimbursement_rate
        elif service_type == 'specialist':
            reimbursement_rate = self.specialist_reimbursement_rate or self.base_reimbursement_rate
        else:
            reimbursement_rate = self.base_reimbursement_rate
        
        return (total_amount * reimbursement_rate) / 100

    def is_service_covered(self, service_name):
        """Check if a service is covered"""
        if service_name in self.excluded_services:
            return False
        if self.covered_services and service_name not in self.covered_services:
            return False
        return True

    def requires_service_referral(self, service_name):
        """Check if service requires referral"""
        return service_name in self.requires_referral

    def requires_service_preauth(self, service_name):
        """Check if service requires pre-authorization"""
        return service_name in self.requires_preauthorization

    def get_effective_reimbursement_rate(self, service_type='standard'):
        """Get effective reimbursement rate for service type"""
        if service_type == 'emergency' and self.emergency_reimbursement_rate:
            return self.emergency_reimbursement_rate
        elif service_type == 'specialist' and self.specialist_reimbursement_rate:
            return self.specialist_reimbursement_rate
        else:
            return self.base_reimbursement_rate

    def update_performance_metrics(self, claims_approved=None, claims_total=None, payment_days=None):
        """Update performance metrics based on claims data"""
        if claims_approved and claims_total:
            self.claims_approval_rate = (claims_approved / claims_total) * 100
        
        if payment_days:
            if self.average_payment_days:
                # Simple moving average
                self.average_payment_days = (self.average_payment_days + payment_days) // 2
            else:
                self.average_payment_days = payment_days
        
        self.last_verification_date = timezone.now().date()
        self.save()

    def get_contract_summary(self):
        """Get contract summary for display"""
        return {
            'provider': self.insurance_provider.name,
            'status': self.get_contract_status_display(),
            'network_type': self.get_network_type_display(),
            'reimbursement_rate': f"{self.base_reimbursement_rate}%",
            'contract_expires': self.contract_end_date,
            'days_remaining': self.contract_days_remaining,
            'is_expiring_soon': self.is_contract_expiring_soon,
            'renewal_due': self.is_renewal_due
        }

    @classmethod
    def get_active_relationships(cls, hospital=None):
        """Get active insurance relationships"""
        queryset = cls.objects.filter(
            is_active=True,
            contract_status='active'
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
            
        return queryset.select_related('insurance_provider')

    @classmethod
    def get_expiring_contracts(cls, days_ahead=60):
        """Get contracts expiring within specified days"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        return cls.objects.filter(
            is_active=True,
            contract_status='active',
            contract_end_date__lte=cutoff_date,
            contract_end_date__isnull=False
        ).select_related('hospital', 'insurance_provider')

    @classmethod
    def get_renewal_due_contracts(cls):
        """Get contracts where renewal is due"""
        today = timezone.now().date()
        
        return cls.objects.filter(
            is_active=True,
            contract_status='active',
            next_renewal_due__lte=today,
            next_renewal_due__isnull=False
        ).select_related('hospital', 'insurance_provider')