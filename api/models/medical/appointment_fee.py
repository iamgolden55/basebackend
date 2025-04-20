from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class AppointmentFee(models.Model):
    """
    Model to manage appointment fees and payment structures
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('NGN', 'Nigerian Naira'),
        # Add more currencies as needed
    ]

    FEE_TYPE_CHOICES = [
        ('general', 'General Consultation'),
        ('specialist', 'Specialist Consultation'),
        ('emergency', 'Emergency Consultation'),
        ('follow_up', 'Follow-up Visit'),
        ('video', 'Video Consultation'),
    ]

    # Basic Information
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='appointment_fees'
    )
    department = models.ForeignKey(
        'api.Department',
        on_delete=models.CASCADE,
        related_name='appointment_fees',
        null=True,
        blank=True
    )
    doctor = models.ForeignKey(
        'api.Doctor',
        on_delete=models.CASCADE,
        related_name='appointment_fees',
        null=True,
        blank=True
    )

    # Fee Structure
    fee_type = models.CharField(
        max_length=50,
        choices=FEE_TYPE_CHOICES,
        default='standard'
    )
    base_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN'
    )
    
    # Additional Fees
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    medical_card_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Discounts and Insurance
    insurance_coverage_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Percentage of fee covered by insurance"
    )
    senior_citizen_discount = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Percentage discount for senior citizens"
    )
    
    # Validity Period
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [
            ['hospital', 'department', 'doctor', 'fee_type']
        ]

    def __str__(self):
        base = f"{self.get_fee_type_display()} - {self.currency} {self.base_fee}"
        if self.department:
            base = f"{self.department.name} - {base}"
        if self.doctor:
            base = f"Dr. {self.doctor.user.get_full_name()} - {base}"
        return base

    def clean(self):
        """Validate fee structure"""
        if self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError("Valid from date must be before valid until date")
            
        if self.insurance_coverage_percentage > 100:
            raise ValidationError("Insurance coverage cannot exceed 100%")
            
        if self.senior_citizen_discount > 100:
            raise ValidationError("Senior citizen discount cannot exceed 100%")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def total_base_fee(self):
        """Calculate total base fee including registration and medical card fee"""
        return self.base_fee + self.registration_fee + self.medical_card_fee

    def calculate_fee(self, patient=None, insurance_applied=False):
        """
        Calculate final fee based on patient details and insurance
        """
        total = self.total_base_fee
        
        # Apply senior citizen discount if applicable
        if patient and patient.is_senior_citizen and self.senior_citizen_discount > 0:
            discount = (total * self.senior_citizen_discount) / 100
            total -= discount
            
        # Apply insurance if applicable
        if insurance_applied and self.insurance_coverage_percentage > 0:
            coverage = (total * self.insurance_coverage_percentage) / 100
            total -= coverage
            
        return round(total, 2)

    def is_valid_on_date(self, date):
        """Check if fee structure is valid on a specific date"""
        if not self.is_active:
            return False
            
        if date < self.valid_from:
            return False
            
        if self.valid_until and date > self.valid_until:
            return False
            
        return True

    @classmethod
    def get_active_fee(cls, hospital, department=None, doctor=None, fee_type='standard', date=None):
        """
        Get active fee structure for given parameters
        """
        from django.utils import timezone
        
        if date is None:
            date = timezone.now().date()
            
        queryset = cls.objects.filter(
            hospital=hospital,
            is_active=True,
            valid_from__lte=date,
            fee_type=fee_type
        ).filter(
            models.Q(valid_until__isnull=True) |
            models.Q(valid_until__gte=date)
        )
        
        if department:
            queryset = queryset.filter(department=department)
            
        if doctor:
            queryset = queryset.filter(doctor=doctor)
            
        return queryset.first() 