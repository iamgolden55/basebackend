from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import json

class PatientInsurancePolicy(models.Model):
    """
    Model representing a patient's insurance policy information
    """
    POLICY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('pending', 'Pending Activation')
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending Verification'),
        ('failed', 'Verification Failed'),
        ('expired', 'Verification Expired'),
        ('not_verified', 'Not Verified')
    ]
    
    RELATIONSHIP_CHOICES = [
        ('self', 'Self'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('dependent', 'Dependent'),
        ('other', 'Other')
    ]
    
    # Basic Information
    patient = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.CASCADE,
        related_name='insurance_policies'
    )
    insurance_provider = models.ForeignKey(
        'api.InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='patient_policies'
    )
    
    # Policy Details
    policy_number = models.CharField(
        max_length=100,
        help_text="Insurance policy number"
    )
    group_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Group policy number (for employer insurance)"
    )
    member_id = models.CharField(
        max_length=100,
        help_text="Member/subscriber ID"
    )
    subscriber_name = models.CharField(
        max_length=200,
        help_text="Name of the primary subscriber"
    )
    
    # Relationship and Coverage
    relationship_to_subscriber = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default='self'
    )
    is_primary_insurance = models.BooleanField(
        default=True,
        help_text="Whether this is the primary insurance"
    )
    priority_order = models.PositiveIntegerField(
        default=1,
        help_text="Priority order for multiple insurance policies"
    )
    
    # Policy Dates
    policy_effective_date = models.DateField()
    policy_expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for policies without expiration"
    )
    coverage_start_date = models.DateField(
        help_text="When coverage starts for this patient"
    )
    coverage_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When coverage ends for this patient"
    )
    
    # Financial Information
    annual_deductible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Annual deductible amount"
    )
    deductible_met_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Amount of deductible already met this year"
    )
    out_of_pocket_maximum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Annual out-of-pocket maximum"
    )
    out_of_pocket_met_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Amount of out-of-pocket maximum already met"
    )
    
    # Coverage Details
    coverage_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MinValueValidator(100)],
        help_text="General coverage percentage"
    )
    copay_primary_care = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Copay for primary care visits"
    )
    copay_specialist = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Copay for specialist visits"
    )
    copay_emergency = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Copay for emergency room visits"
    )
    
    # Verification Information
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='not_verified'
    )
    last_verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time eligibility was verified"
    )
    verification_frequency_days = models.PositiveIntegerField(
        default=30,
        help_text="How often to verify eligibility"
    )
    
    # Encrypted Verification Data
    _encrypted_verification_data = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
        help_text="Encrypted verification response data"
    )
    
    # Authorization and Referral Requirements
    requires_referral_for_specialists = models.BooleanField(
        default=False,
        help_text="Whether specialist visits require referrals"
    )
    requires_preauthorization = models.JSONField(
        default=list,
        help_text="Services requiring pre-authorization"
    )
    covered_services = models.JSONField(
        default=list,
        help_text="List of covered services"
    )
    excluded_services = models.JSONField(
        default=list,
        help_text="List of excluded services"
    )
    
    # Contact Information
    member_services_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Insurance company member services phone"
    )
    claims_address = models.TextField(
        blank=True,
        help_text="Address for mailing claims"
    )
    
    # Additional Information
    employer_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Employer name (for employer-sponsored insurance)"
    )
    plan_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Specific plan name"
    )
    plan_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of plan (HMO, PPO, EPO, etc.)"
    )
    
    # Status and Administrative
    policy_status = models.CharField(
        max_length=20,
        choices=POLICY_STATUS_CHOICES,
        default='active'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this policy is currently active"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the policy"
    )
    
    # Document Storage
    insurance_card_front = models.FileField(
        upload_to='insurance_cards/front/',
        null=True,
        blank=True,
        help_text="Front of insurance card"
    )
    insurance_card_back = models.FileField(
        upload_to='insurance_cards/back/',
        null=True,
        blank=True,
        help_text="Back of insurance card"
    )
    benefits_summary = models.FileField(
        upload_to='insurance_documents/benefits/',
        null=True,
        blank=True,
        help_text="Benefits summary document"
    )
    
    # Timestamps and Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_patient_policies',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_patient_policies',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['patient', 'insurance_provider', 'policy_number']]
        ordering = ['priority_order', '-created_at']
        indexes = [
            models.Index(fields=['patient', 'is_primary_insurance']),
            models.Index(fields=['policy_number']),
            models.Index(fields=['member_id']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['policy_status']),
            models.Index(fields=['last_verification_date']),
        ]
        permissions = [
            ("can_view_insurance_details", "Can view insurance details"),
            ("can_verify_eligibility", "Can verify insurance eligibility"),
            ("can_update_verification", "Can update verification status"),
        ]
        verbose_name_plural = "Patient Insurance Policies"

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.insurance_provider.name} ({self.policy_number})"

    def clean(self):
        """Validate patient insurance policy"""
        super().clean()
        
        if self.policy_expiration_date and self.policy_effective_date > self.policy_expiration_date:
            raise ValidationError(
                "Policy effective date must be before expiration date"
            )
        
        if self.coverage_end_date and self.coverage_start_date > self.coverage_end_date:
            raise ValidationError(
                "Coverage start date must be before end date"
            )
        
        if self.deductible_met_amount and self.annual_deductible:
            if self.deductible_met_amount > self.annual_deductible:
                raise ValidationError(
                    "Deductible met amount cannot exceed annual deductible"
                )
        
        if self.out_of_pocket_met_amount and self.out_of_pocket_maximum:
            if self.out_of_pocket_met_amount > self.out_of_pocket_maximum:
                raise ValidationError(
                    "Out-of-pocket met amount cannot exceed annual maximum"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        # Set priority order for multiple policies
        if not self.priority_order:
            max_priority = PatientInsurancePolicy.objects.filter(
                patient=self.patient
            ).aggregate(
                max_priority=models.Max('priority_order')
            )['max_priority'] or 0
            self.priority_order = max_priority + 1
        
        # Ensure only one primary insurance
        if self.is_primary_insurance:
            PatientInsurancePolicy.objects.filter(
                patient=self.patient,
                is_primary_insurance=True
            ).exclude(pk=self.pk).update(is_primary_insurance=False)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    @property
    def verification_data(self):
        """Decrypt and return verification data"""
        if self._encrypted_verification_data:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='insurance_verification')
                return json.loads(signer.unsign(self._encrypted_verification_data.decode()))
            except Exception:
                return {}
        return {}

    @verification_data.setter
    def verification_data(self, data):
        """Encrypt and store verification data"""
        if data:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='insurance_verification')
                self._encrypted_verification_data = signer.sign(json.dumps(data)).encode()
            except Exception:
                pass

    @property
    def is_verification_due(self):
        """Check if verification is due"""
        if not self.last_verification_date:
            return True
            
        from datetime import timedelta
        due_date = self.last_verification_date + timedelta(days=self.verification_frequency_days)
        return timezone.now() > due_date

    @property
    def is_coverage_active(self):
        """Check if coverage is currently active"""
        if not self.is_active or self.policy_status != 'active':
            return False
            
        today = timezone.now().date()
        
        # Check policy dates
        if self.policy_expiration_date and today > self.policy_expiration_date:
            return False
        if today < self.policy_effective_date:
            return False
            
        # Check coverage dates
        if self.coverage_end_date and today > self.coverage_end_date:
            return False
        if today < self.coverage_start_date:
            return False
            
        return True

    @property
    def remaining_deductible(self):
        """Calculate remaining deductible amount"""
        if not self.annual_deductible:
            return Decimal('0')
        return max(self.annual_deductible - self.deductible_met_amount, Decimal('0'))

    @property
    def remaining_out_of_pocket(self):
        """Calculate remaining out-of-pocket maximum"""
        if not self.out_of_pocket_maximum:
            return None
        return max(self.out_of_pocket_maximum - self.out_of_pocket_met_amount, Decimal('0'))

    def is_deductible_met(self):
        """Check if annual deductible is met"""
        if not self.annual_deductible:
            return True
        return self.deductible_met_amount >= self.annual_deductible

    def is_out_of_pocket_max_met(self):
        """Check if out-of-pocket maximum is met"""
        if not self.out_of_pocket_maximum:
            return False
        return self.out_of_pocket_met_amount >= self.out_of_pocket_maximum

    def calculate_coverage_for_service(self, service_type, amount):
        """Calculate coverage for a specific service"""
        if not self.is_coverage_active:
            return {
                'covered_amount': Decimal('0'),
                'patient_amount': amount,
                'reason': 'Coverage not active'
            }
        
        # Check if service is excluded
        if service_type in self.excluded_services:
            return {
                'covered_amount': Decimal('0'),
                'patient_amount': amount,
                'reason': 'Service excluded from coverage'
            }
        
        # Get copay for service type
        copay = self.get_copay_for_service(service_type)
        
        # If out-of-pocket max is met, insurance covers everything except copay
        if self.is_out_of_pocket_max_met():
            return {
                'covered_amount': amount - copay,
                'patient_amount': copay,
                'reason': 'Out-of-pocket maximum met'
            }
        
        # Calculate based on deductible and coverage percentage
        remaining_deductible = self.remaining_deductible
        
        if remaining_deductible > 0:
            # Apply amount to deductible first
            deductible_applied = min(amount, remaining_deductible)
            remaining_amount = amount - deductible_applied
            
            # Apply coverage percentage to remaining amount
            if remaining_amount > 0 and self.coverage_percentage:
                covered_remaining = (remaining_amount * self.coverage_percentage) / 100
                patient_amount = deductible_applied + (remaining_amount - covered_remaining) + copay
                covered_amount = covered_remaining
            else:
                patient_amount = amount + copay
                covered_amount = Decimal('0')
        else:
            # Deductible already met, apply coverage percentage
            if self.coverage_percentage:
                covered_amount = (amount * self.coverage_percentage) / 100
                patient_amount = amount - covered_amount + copay
            else:
                covered_amount = Decimal('0')
                patient_amount = amount + copay
        
        return {
            'covered_amount': max(covered_amount, Decimal('0')),
            'patient_amount': max(patient_amount, Decimal('0')),
            'reason': 'Standard coverage calculation'
        }

    def get_copay_for_service(self, service_type):
        """Get copay amount for service type"""
        copay_mapping = {
            'primary_care': self.copay_primary_care,
            'specialist': self.copay_specialist,
            'emergency': self.copay_emergency
        }
        return copay_mapping.get(service_type, Decimal('0')) or Decimal('0')

    def requires_service_referral(self, service_type):
        """Check if service requires referral"""
        if service_type == 'specialist':
            return self.requires_referral_for_specialists
        return False

    def requires_service_preauth(self, service_name):
        """Check if service requires pre-authorization"""
        return service_name in self.requires_preauthorization

    def mark_verification_completed(self, verification_response=None, success=True):
        """Mark verification as completed"""
        self.last_verification_date = timezone.now()
        
        if success:
            self.verification_status = 'verified'
        else:
            self.verification_status = 'failed'
        
        if verification_response:
            self.verification_data = verification_response
        
        self.save()

    def update_financial_tracking(self, deductible_amount=None, out_of_pocket_amount=None):
        """Update deductible and out-of-pocket tracking"""
        if deductible_amount:
            self.deductible_met_amount = min(
                self.deductible_met_amount + deductible_amount,
                self.annual_deductible or Decimal('999999')
            )
        
        if out_of_pocket_amount:
            self.out_of_pocket_met_amount = min(
                self.out_of_pocket_met_amount + out_of_pocket_amount,
                self.out_of_pocket_maximum or Decimal('999999')
            )
        
        self.save()

    def reset_annual_amounts(self):
        """Reset annual deductible and out-of-pocket amounts (for new year)"""
        self.deductible_met_amount = Decimal('0')
        self.out_of_pocket_met_amount = Decimal('0')
        self.save()

    def get_policy_summary(self):
        """Get policy summary for display"""
        return {
            'provider': self.insurance_provider.name,
            'policy_number': self.policy_number,
            'member_id': self.member_id,
            'status': self.get_policy_status_display(),
            'is_primary': self.is_primary_insurance,
            'coverage_active': self.is_coverage_active,
            'verification_status': self.get_verification_status_display(),
            'verification_due': self.is_verification_due,
            'deductible_remaining': self.remaining_deductible,
            'out_of_pocket_remaining': self.remaining_out_of_pocket
        }

    @classmethod
    def get_active_policies_for_patient(cls, patient):
        """Get active insurance policies for a patient"""
        return cls.objects.filter(
            patient=patient,
            is_active=True,
            policy_status='active'
        ).order_by('priority_order')

    @classmethod
    def get_primary_policy_for_patient(cls, patient):
        """Get primary insurance policy for a patient"""
        return cls.objects.filter(
            patient=patient,
            is_active=True,
            policy_status='active',
            is_primary_insurance=True
        ).first()

    @classmethod
    def get_verification_due_policies(cls):
        """Get policies that need verification"""
        return cls.objects.filter(
            is_active=True,
            policy_status='active'
        ).exclude(
            verification_status='verified'
        )