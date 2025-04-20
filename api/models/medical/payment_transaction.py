from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import Signer
import json
from datetime import datetime

class PaymentTransaction(models.Model):
    """
    Model to track payment transactions for appointments with enhanced security
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('insurance', 'Insurance'),
        ('mobile_money', 'Mobile Money'),
        ('wallet', 'E-Wallet'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('NGN', 'Nigerian Naira'),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ('paystack', 'Paystack'),
        ('moniepoint', 'Moniepoint'),
        ('flutterwave', 'Flutterwave'),
        ('stripe', 'Stripe'),
    ]

    # Basic Information
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the transaction"
    )
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    patient = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # Payment Details with Encryption
    _encrypted_amount = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted amount for security"
    )
    amount_display = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Display amount for UI"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN'
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Insurance Information with Encryption
    _encrypted_insurance_data = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted insurance information"
    )
    insurance_provider = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    insurance_coverage_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Payment Processing Details with Enhanced Security
    _encrypted_gateway_data = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted gateway response data"
    )
    payment_gateway = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Payment gateway used for processing"
    )
    gateway_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction ID from payment gateway"
    )
    
    # Audit Trail
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='created_transactions',
        help_text="User who created the transaction"
    )
    last_modified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='modified_transactions',
        help_text="User who last modified the transaction"
    )
    status_change_history = models.JSONField(
        default=list,
        help_text="History of status changes with timestamps and users"
    )
    access_log = models.JSONField(
        default=list,
        help_text="Log of users who accessed this transaction"
    )
    
    # Gift Payment Support
    gift_sender = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_gift_payments'
    )
    
    # Additional Information
    description = models.TextField(
        blank=True,
        help_text="Additional details about the transaction"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about the transaction"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Payment Provider Information
    payment_provider = models.CharField(
        max_length=50,
        choices=PAYMENT_PROVIDER_CHOICES,
        null=True,
        help_text="Payment provider used for processing"
    )
    provider_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Reference ID from payment provider"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]
        permissions = [
            ("can_view_sensitive_data", "Can view sensitive transaction data"),
            ("can_process_refunds", "Can process refunds"),
            ("can_view_audit_trail", "Can view transaction audit trail"),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signer = Signer(salt='payment_transaction')
        self._old_status = self.payment_status

    def __str__(self):
        return f"{self.transaction_id} - {self.payment_status}"

    @property
    def amount(self):
        """Decrypt and return the actual amount"""
        if self._encrypted_amount:
            return float(self._signer.unsign(self._encrypted_amount.decode()))
        return float(self.amount_display)

    @amount.setter
    def amount(self, value):
        """Encrypt and store the amount"""
        self.amount_display = value
        self._encrypted_amount = self._signer.sign(str(value)).encode()

    @property
    def insurance_data(self):
        """Decrypt and return insurance data"""
        if self._encrypted_insurance_data:
            return json.loads(self._signer.unsign(self._encrypted_insurance_data.decode()))
        return {}

    @insurance_data.setter
    def insurance_data(self, data):
        """Encrypt and store insurance data"""
        if data:
            self._encrypted_insurance_data = self._signer.sign(json.dumps(data)).encode()

    @property
    def gateway_data(self):
        """Decrypt and return gateway data"""
        if self._encrypted_gateway_data:
            return json.loads(self._signer.unsign(self._encrypted_gateway_data.decode()))
        return {}

    @gateway_data.setter
    def gateway_data(self, data):
        """Encrypt and store gateway data"""
        if data:
            self._encrypted_gateway_data = self._signer.sign(json.dumps(data)).encode()

    def log_access(self, user):
        """Log user access to transaction"""
        self.access_log.append({
            'user': user.id,
            'timestamp': datetime.now().isoformat(),
            'action': 'viewed'
        })
        self.save()

    def log_status_change(self, user):
        """Log status change in history"""
        if self.payment_status != self._old_status:
            self.status_change_history.append({
                'from_status': self._old_status,
                'to_status': self.payment_status,
                'changed_by': user.id,
                'timestamp': datetime.now().isoformat()
            })
            self._old_status = self.payment_status

    def clean(self):
        """Enhanced validation with security checks"""
        super().clean()
        
        if self.payment_method == 'insurance' and not all([
            self.insurance_provider,
            self.insurance_policy_number
        ]):
            raise ValidationError(
                "Insurance provider and policy number are required for insurance payments"
            )
            
        if self.insurance_coverage_amount > self.amount:
            raise ValidationError(
                "Insurance coverage amount cannot exceed total amount"
            )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        # First save for new instances
        if not self.pk:
            if user:
                self.created_by = user
                self.last_modified_by = user
            
            # Generate transaction ID if not provided
            if not self.transaction_id:
                self.transaction_id = self.generate_transaction_id()
        
        # Update last modified user
        if user:
            self.last_modified_by = user
            self.log_status_change(user)
        
        # Set completed_at timestamp
        if self.payment_status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.clean()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_transaction_id():
        """Generate a unique transaction ID"""
        import uuid
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"

    def mark_as_completed(self, gateway_response=None, user=None):
        """Mark payment as completed with audit"""
        self.payment_status = 'completed'
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_data = gateway_response
        self.save(user=user)

    def mark_as_failed(self, gateway_response=None, user=None):
        """Mark payment as failed with audit"""
        self.payment_status = 'failed'
        if gateway_response:
            self.gateway_data = gateway_response
        self.save(user=user)

    def process_refund(self, amount=None, reason=None, user=None):
        """Process refund with enhanced security"""
        if not user.has_perm('payment_transaction.can_process_refunds'):
            raise ValidationError("User does not have permission to process refunds")
            
        if self.payment_status != 'completed':
            raise ValidationError("Only completed payments can be refunded")
            
        if amount and amount > self.amount:
            raise ValidationError("Refund amount cannot exceed payment amount")
            
        self.payment_status = 'refunded'
        if reason:
            self.notes += f"\nRefund reason: {reason}"
        self.save(user=user)

    def get_audit_trail(self, user=None):
        """Get complete audit trail if user has permission"""
        if user and not user.has_perm('payment_transaction.can_view_audit_trail'):
            raise ValidationError("User does not have permission to view audit trail")
            
        return {
            'status_changes': self.status_change_history,
            'access_log': self.access_log,
            'created_by': self.created_by.get_full_name(),
            'created_at': self.created_at,
            'last_modified_by': self.last_modified_by.get_full_name(),
            'last_modified_at': self.updated_at
        }

    def get_payment_summary(self, include_sensitive=False):
        """Get summary of payment details with security check"""
        summary = {
            'transaction_id': self.transaction_id,
            'amount': self.amount_display,
            'currency': self.currency,
            'status': self.payment_status,
            'method': self.payment_method,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }
        
        if include_sensitive:
            summary.update({
                'actual_amount': self.amount,
                'insurance_data': self.insurance_data,
                'gateway_data': self.gateway_data
            })
            
        return summary

    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.payment_status == 'completed'

    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.payment_status == 'completed'

    @property
    def payment_duration(self):
        """Calculate duration of payment processing"""
        if self.completed_at:
            return self.completed_at - self.created_at
        return None

    def get_payment_provider(self):
        """Get the payment provider instance"""
        if not self.payment_provider:
            return None
            
        from ..payment_providers import PROVIDER_MAPPING
        provider_class = PROVIDER_MAPPING.get(self.payment_provider)
        if provider_class:
            return provider_class(self)
        return None

    def initialize_payment(self):
        """Initialize payment with selected provider"""
        provider = self.get_payment_provider()
        if not provider:
            raise ValidationError("No payment provider selected")
            
        return provider.initialize_payment()

    def verify_payment(self, reference=None):
        """Verify payment with provider"""
        provider = self.get_payment_provider()
        if not provider:
            raise ValidationError("No payment provider selected")
            
        return provider.verify_payment(reference or self.provider_reference) 