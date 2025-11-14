from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class HospitalLicense(models.Model):
    """
    Model representing hospital's government licenses and regulatory registrations
    """
    LICENSE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('pending', 'Pending Approval'),
        ('renewal_pending', 'Renewal Pending'),
        ('under_review', 'Under Review')
    ]
    
    LICENSE_TYPE_CHOICES = [
        ('business_registration', 'Business Registration (CAC)'),
        ('operating', 'Operating License'),
        ('emergency', 'Emergency Services License'),
        ('surgical', 'Surgical Services License'),
        ('maternity', 'Maternity Services License'),
        ('icu', 'ICU/Critical Care License'),
        ('psychiatric', 'Psychiatric Services License'),
        ('pediatric', 'Pediatric Services License'),
        ('radiology', 'Radiology/Imaging License'),
        ('laboratory', 'Laboratory Services License'),
        ('pharmacy', 'Hospital Pharmacy License'),
        ('blood_bank', 'Blood Bank License'),
        ('ambulance', 'Ambulance Services License'),
        ('research', 'Medical Research License'),
        ('teaching', 'Teaching Hospital License'),
        ('specialty', 'Specialty Services License'),
        ('other', 'Other License Type')
    ]
    
    RENEWAL_STATUS_CHOICES = [
        ('current', 'Current'),
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('in_process', 'Renewal in Process'),
        ('not_applicable', 'Not Applicable')
    ]
    
    # Relationships
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='licenses'
    )
    healthcare_authority = models.ForeignKey(
        'api.HealthcareAuthority',
        on_delete=models.PROTECT,
        related_name='issued_licenses',
        null=True,
        blank=True,
        help_text="Healthcare authority that issued this license (not applicable for CAC certificates)"
    )
    
    # License Information
    license_number = models.CharField(
        max_length=100,
        help_text="Official license number"
    )
    license_type = models.CharField(
        max_length=30,
        choices=LICENSE_TYPE_CHOICES,
        default='operating'
    )
    license_category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific category or classification"
    )
    license_name = models.CharField(
        max_length=200,
        help_text="Official name of the license"
    )
    
    # Status and Dates
    license_status = models.CharField(
        max_length=20,
        choices=LICENSE_STATUS_CHOICES,
        default='pending'
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date license was issued"
    )
    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date license becomes effective"
    )
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="License expiration date (if applicable)"
    )
    
    # Renewal Information
    renewal_status = models.CharField(
        max_length=20,
        choices=RENEWAL_STATUS_CHOICES,
        default='current'
    )
    last_renewal_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last renewal"
    )
    next_renewal_due = models.DateField(
        null=True,
        blank=True,
        help_text="Date when next renewal is due"
    )
    renewal_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Renewal frequency in months"
    )
    
    # License Conditions and Restrictions
    conditions = models.TextField(
        blank=True,
        help_text="Conditions or restrictions on the license"
    )
    limitations = models.TextField(
        blank=True,
        help_text="Any limitations specified in the license"
    )
    bed_capacity_authorized = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Authorized bed capacity (if specified)"
    )
    services_authorized = models.JSONField(
        default=list,
        help_text="List of authorized services"
    )
    
    # Compliance and Inspection
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last regulatory inspection"
    )
    next_inspection_due = models.DateField(
        null=True,
        blank=True,
        help_text="Date when next inspection is due"
    )
    inspection_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Inspection frequency in months"
    )
    compliance_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Latest compliance score (1-100)"
    )
    
    # Financial Information
    license_fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="License fee paid"
    )
    renewal_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Renewal fee amount"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for fees"
    )
    
    # Application and Processing
    application_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date application was submitted"
    )
    processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Days taken to process application"
    )
    application_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Application reference number"
    )
    
    # Contact and Communication
    license_officer_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of assigned license officer"
    )
    license_officer_email = models.EmailField(
        blank=True,
        help_text="Email of license officer"
    )
    license_officer_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone of license officer"
    )
    
    # Documentation
    license_certificate = models.FileField(
        upload_to='licenses/certificates/',
        null=True,
        blank=True,
        help_text="Digital copy of license certificate"
    )
    supporting_documents = models.JSONField(
        default=list,
        help_text="List of supporting documents"
    )
    inspection_reports = models.JSONField(
        default=list,
        help_text="List of inspection reports"
    )
    
    # Verification and Monitoring
    verification_url = models.URLField(
        blank=True,
        help_text="URL to verify license online"
    )
    public_verification_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Public verification code"
    )
    last_verified = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time license was verified"
    )
    auto_verification_enabled = models.BooleanField(
        default=False,
        help_text="Whether automatic verification is enabled"
    )
    
    # Alerts and Notifications
    expiry_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether expiry alert has been sent"
    )
    renewal_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether renewal alert has been sent"
    )
    inspection_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether inspection alert has been sent"
    )
    
    # History and Audit
    previous_license_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Previous license number (if renewed)"
    )
    license_history = models.JSONField(
        default=list,
        help_text="History of license changes"
    )
    violations_history = models.JSONField(
        default=list,
        help_text="History of violations or issues"
    )
    
    # Additional Information
    is_transferable = models.BooleanField(
        default=False,
        help_text="Whether license can be transferred"
    )
    requires_medical_director = models.BooleanField(
        default=False,
        help_text="Whether license requires a medical director"
    )
    medical_director_required = models.CharField(
        max_length=200,
        blank=True,
        help_text="Medical director information"
    )
    
    # Status Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether license record is active"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the license"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_hospital_licenses',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_hospital_licenses',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['hospital', 'license_number']]
        ordering = ['-created_at', 'license_type']
        indexes = [
            models.Index(fields=['hospital', 'license_status']),
            models.Index(fields=['license_number']),
            models.Index(fields=['license_type']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['next_renewal_due']),
            models.Index(fields=['next_inspection_due']),
            models.Index(fields=['healthcare_authority']),
        ]
        permissions = [
            ("can_manage_licenses", "Can manage hospital licenses"),
            ("can_view_license_details", "Can view license details"),
            ("can_verify_licenses", "Can verify license status"),
            ("can_upload_documents", "Can upload license documents"),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.get_license_type_display()} ({self.license_number})"

    def clean(self):
        """Validate hospital license data"""
        super().clean()

        # Only validate dates if they are provided
        if self.effective_date and self.effective_date > timezone.now().date():
            if self.license_status == 'active':
                raise ValidationError(
                    "License cannot be active before effective date"
                )

        if self.expiration_date and self.effective_date:
            if self.effective_date >= self.expiration_date:
                raise ValidationError(
                    "Effective date must be before expiration date"
                )

        if self.next_renewal_due and self.expiration_date:
            if self.next_renewal_due > self.expiration_date:
                raise ValidationError(
                    "Renewal due date cannot be after expiration date"
                )

        if self.compliance_score and (self.compliance_score < 1 or self.compliance_score > 100):
            raise ValidationError(
                "Compliance score must be between 1 and 100"
            )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
        
        # Update renewal status based on dates
        self.update_renewal_status()
        
        # Add to license history if this is an update
        if self.pk:
            old_license = HospitalLicense.objects.get(pk=self.pk)
            if old_license.license_status != self.license_status:
                self.add_to_history('status_change', {
                    'from': old_license.license_status,
                    'to': self.license_status,
                    'date': timezone.now().isoformat()
                })
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expiring_soon(self):
        """Check if license is expiring within 60 days"""
        if not self.expiration_date:
            return False
            
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=60)
        return self.expiration_date <= warning_date

    @property
    def is_expired(self):
        """Check if license is expired"""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    @property
    def is_renewal_due(self):
        """Check if renewal is due"""
        if not self.next_renewal_due:
            return False
        return timezone.now().date() >= self.next_renewal_due

    @property
    def is_inspection_due(self):
        """Check if inspection is due"""
        if not self.next_inspection_due:
            return False
        return timezone.now().date() >= self.next_inspection_due

    @property
    def days_until_expiry(self):
        """Calculate days until license expires"""
        if not self.expiration_date:
            return None
        
        delta = self.expiration_date - timezone.now().date()
        return delta.days if delta.days >= 0 else 0

    @property
    def days_until_renewal(self):
        """Calculate days until renewal is due"""
        if not self.next_renewal_due:
            return None
        
        delta = self.next_renewal_due - timezone.now().date()
        return delta.days

    def update_renewal_status(self):
        """Update renewal status based on current dates"""
        if not self.next_renewal_due:
            self.renewal_status = 'not_applicable'
            return
        
        days_until_renewal = self.days_until_renewal
        
        if days_until_renewal is None:
            self.renewal_status = 'not_applicable'
        elif days_until_renewal < 0:
            self.renewal_status = 'overdue'
        elif days_until_renewal <= 30:
            self.renewal_status = 'due_soon'
        else:
            self.renewal_status = 'current'

    def mark_as_renewed(self, new_expiration_date, new_license_number=None, user=None):
        """Mark license as renewed"""
        self.last_renewal_date = timezone.now().date()
        
        if new_license_number and new_license_number != self.license_number:
            self.previous_license_number = self.license_number
            self.license_number = new_license_number
        
        if new_expiration_date:
            self.expiration_date = new_expiration_date
            
            # Calculate next renewal due date
            if self.renewal_frequency_months:
                from dateutil.relativedelta import relativedelta
                self.next_renewal_due = new_expiration_date - relativedelta(months=1)
        
        self.license_status = 'active'
        self.renewal_status = 'current'
        self.renewal_alert_sent = False
        
        self.add_to_history('renewal', {
            'renewal_date': self.last_renewal_date.isoformat(),
            'new_expiration': new_expiration_date.isoformat() if new_expiration_date else None,
            'renewed_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def mark_as_expired(self, user=None):
        """Mark license as expired"""
        self.license_status = 'expired'
        self.renewal_status = 'overdue'
        
        self.add_to_history('expiration', {
            'expired_date': timezone.now().date().isoformat(),
            'marked_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def suspend_license(self, reason, suspended_until=None, user=None):
        """Suspend the license"""
        self.license_status = 'suspended'
        
        suspension_info = {
            'suspension_date': timezone.now().date().isoformat(),
            'reason': reason,
            'suspended_by': user.get_full_name() if user else 'System'
        }
        
        if suspended_until:
            suspension_info['suspended_until'] = suspended_until.isoformat()
        
        self.add_to_history('suspension', suspension_info)
        self.save()

    def reinstate_license(self, user=None):
        """Reinstate a suspended license"""
        if self.license_status != 'suspended':
            raise ValidationError("Only suspended licenses can be reinstated")
        
        self.license_status = 'active'
        
        self.add_to_history('reinstatement', {
            'reinstatement_date': timezone.now().date().isoformat(),
            'reinstated_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def record_inspection(self, inspection_date, compliance_score=None, 
                         next_inspection_date=None, notes=None, user=None):
        """Record an inspection"""
        self.last_inspection_date = inspection_date
        
        if compliance_score:
            self.compliance_score = compliance_score
        
        if next_inspection_date:
            self.next_inspection_due = next_inspection_date
        
        inspection_info = {
            'inspection_date': inspection_date.isoformat(),
            'compliance_score': compliance_score,
            'inspector': user.get_full_name() if user else 'Unknown',
            'notes': notes
        }
        
        self.add_to_history('inspection', inspection_info)
        self.inspection_alert_sent = False
        self.save()

    def add_violation(self, violation_description, violation_date=None, 
                     severity='medium', resolved=False):
        """Add a violation to the history"""
        violation = {
            'date': (violation_date or timezone.now().date()).isoformat(),
            'description': violation_description,
            'severity': severity,
            'resolved': resolved,
            'added_on': timezone.now().isoformat()
        }
        
        if not isinstance(self.violations_history, list):
            self.violations_history = []
        
        self.violations_history.append(violation)
        self.save()

    def resolve_violation(self, violation_index, resolution_notes=None, user=None):
        """Mark a violation as resolved"""
        if violation_index < len(self.violations_history):
            self.violations_history[violation_index]['resolved'] = True
            self.violations_history[violation_index]['resolved_date'] = timezone.now().date().isoformat()
            self.violations_history[violation_index]['resolved_by'] = user.get_full_name() if user else 'System'
            
            if resolution_notes:
                self.violations_history[violation_index]['resolution_notes'] = resolution_notes
            
            self.save()

    def add_to_history(self, event_type, event_data):
        """Add an event to license history"""
        if not isinstance(self.license_history, list):
            self.license_history = []
        
        history_entry = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        self.license_history.append(history_entry)

    def verify_license_online(self):
        """Attempt to verify license online if verification URL is available"""
        if not self.verification_url:
            return {'success': False, 'message': 'No verification URL available'}
        
        try:
            import requests
            # This would be customized based on each authority's verification system
            response = requests.get(
                self.verification_url,
                params={'license_number': self.license_number},
                timeout=30
            )
            
            if response.status_code == 200:
                self.last_verified = timezone.now()
                self.save()
                return {'success': True, 'message': 'License verified successfully'}
            else:
                return {'success': False, 'message': f'Verification failed: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Verification error: {str(e)}'}

    def get_license_summary(self):
        """Get license summary for display"""
        return {
            'license_number': self.license_number,
            'license_type': self.get_license_type_display(),
            'status': self.get_license_status_display(),
            'authority': self.healthcare_authority.name if self.healthcare_authority else 'Not specified',
            'issue_date': self.issue_date,
            'expiration_date': self.expiration_date,
            'days_until_expiry': self.days_until_expiry,
            'is_expiring_soon': self.is_expiring_soon,
            'is_expired': self.is_expired,
            'renewal_due': self.is_renewal_due,
            'compliance_score': self.compliance_score,
            'verification_url': self.verification_url
        }

    def get_alerts(self):
        """Get list of alerts for this license"""
        alerts = []
        
        if self.is_expired:
            alerts.append({
                'type': 'error',
                'message': f'License expired on {self.expiration_date}',
                'priority': 'high'
            })
        elif self.is_expiring_soon:
            alerts.append({
                'type': 'warning',
                'message': f'License expires in {self.days_until_expiry} days',
                'priority': 'medium'
            })
        
        if self.is_renewal_due:
            alerts.append({
                'type': 'warning',
                'message': 'License renewal is due',
                'priority': 'medium'
            })
        
        if self.is_inspection_due:
            alerts.append({
                'type': 'info',
                'message': 'Inspection is due',
                'priority': 'low'
            })
        
        if self.license_status == 'suspended':
            alerts.append({
                'type': 'error',
                'message': 'License is currently suspended',
                'priority': 'high'
            })
        
        return alerts

    @classmethod
    def get_expiring_licenses(cls, days_ahead=60, hospital=None):
        """Get licenses expiring within specified days"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        queryset = cls.objects.filter(
            expiration_date__lte=cutoff_date,
            expiration_date__isnull=False,
            license_status='active'
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('expiration_date')

    @classmethod
    def get_expired_licenses(cls, hospital=None):
        """Get expired licenses"""
        today = timezone.now().date()
        
        queryset = cls.objects.filter(
            expiration_date__lt=today,
            expiration_date__isnull=False
        ).exclude(license_status__in=['expired', 'revoked'])
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('expiration_date')

    @classmethod
    def get_compliance_summary(cls, hospital=None):
        """Get compliance summary for licenses"""
        queryset = cls.objects.filter(license_status='active')
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        from django.db.models import Avg, Count
        
        return queryset.aggregate(
            total_licenses=Count('id'),
            avg_compliance_score=Avg('compliance_score'),
            expiring_soon=Count('id', filter=models.Q(
                expiration_date__lte=timezone.now().date() + timezone.timedelta(days=60)
            )),
            expired=Count('id', filter=models.Q(
                expiration_date__lt=timezone.now().date()
            ))
        )