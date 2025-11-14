from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class HospitalBillingIntegration(models.Model):
    """
    Model representing hospital's integration with billing systems
    """
    INTEGRATION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('implementation', 'Implementation In Progress'),
        ('suspended', 'Suspended'),
        ('failed', 'Failed'),
        ('maintenance', 'Under Maintenance'),
        ('migrating', 'Migrating'),
        ('deprecated', 'Deprecated')
    ]
    
    INTEGRATION_TYPE_CHOICES = [
        ('primary', 'Primary Billing System'),
        ('secondary', 'Secondary Billing System'),
        ('backup', 'Backup System'),
        ('specialty', 'Specialty Billing'),
        ('reporting', 'Reporting Only'),
        ('analytics', 'Analytics Only'),
        ('archive', 'Archive System')
    ]
    
    DATA_SYNC_METHOD_CHOICES = [
        ('real_time', 'Real-time Sync'),
        ('batch', 'Batch Processing'),
        ('scheduled', 'Scheduled Sync'),
        ('manual', 'Manual Upload'),
        ('api_webhook', 'API with Webhooks'),
        ('file_transfer', 'File Transfer'),
        ('hybrid', 'Hybrid Approach')
    ]
    
    # Relationships
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='billing_integrations'
    )
    billing_system = models.ForeignKey(
        'api.BillingSystem',
        on_delete=models.PROTECT,
        related_name='hospital_integrations'
    )
    
    # Integration Configuration
    integration_name = models.CharField(
        max_length=200,
        help_text="Custom name for this integration"
    )
    integration_type = models.CharField(
        max_length=20,
        choices=INTEGRATION_TYPE_CHOICES,
        default='primary'
    )
    integration_status = models.CharField(
        max_length=20,
        choices=INTEGRATION_STATUS_CHOICES,
        default='inactive'
    )
    
    # Technical Configuration
    api_endpoint = models.URLField(
        blank=True,
        help_text="API endpoint for the billing system"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        help_text="Encrypted API key"
    )
    api_secret = models.CharField(
        max_length=500,
        blank=True,
        help_text="Encrypted API secret"
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="Webhook URL for receiving updates"
    )
    webhook_secret = models.CharField(
        max_length=200,
        blank=True,
        help_text="Webhook verification secret"
    )
    
    # Data Synchronization
    data_sync_method = models.CharField(
        max_length=20,
        choices=DATA_SYNC_METHOD_CHOICES,
        default='real_time'
    )
    sync_frequency_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sync frequency in minutes for scheduled sync"
    )
    last_sync_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful synchronization"
    )
    next_sync_scheduled = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled synchronization"
    )
    
    # Data Mapping Configuration
    patient_id_mapping = models.JSONField(
        default=dict,
        help_text="Patient ID mapping configuration"
    )
    procedure_code_mapping = models.JSONField(
        default=dict,
        help_text="Procedure code mapping configuration"
    )
    diagnosis_code_mapping = models.JSONField(
        default=dict,
        help_text="Diagnosis code mapping configuration"
    )
    insurance_mapping = models.JSONField(
        default=dict,
        help_text="Insurance provider mapping configuration"
    )
    custom_field_mapping = models.JSONField(
        default=dict,
        help_text="Custom field mapping configuration"
    )
    
    # Billing Configuration
    default_billing_rules = models.JSONField(
        default=dict,
        help_text="Default billing rules and configurations"
    )
    payment_terms_days = models.PositiveIntegerField(
        default=30,
        help_text="Default payment terms in days"
    )
    automatic_billing_enabled = models.BooleanField(
        default=False,
        help_text="Whether automatic billing is enabled"
    )
    invoice_generation_enabled = models.BooleanField(
        default=True,
        help_text="Whether automatic invoice generation is enabled"
    )
    
    # Claims Processing
    claims_submission_enabled = models.BooleanField(
        default=False,
        help_text="Whether claims submission is enabled"
    )
    auto_claims_submission = models.BooleanField(
        default=False,
        help_text="Whether automatic claims submission is enabled"
    )
    claims_batch_size = models.PositiveIntegerField(
        default=100,
        help_text="Batch size for claims submission"
    )
    claims_retry_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Number of retry attempts for failed claims"
    )
    
    # Financial Configuration
    transaction_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Transaction fee percentage"
    )
    monthly_subscription_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly subscription fee"
    )
    setup_fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Setup fee paid"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for fees"
    )
    
    # Performance Metrics
    total_transactions_processed = models.PositiveIntegerField(
        default=0,
        help_text="Total number of transactions processed"
    )
    successful_transactions = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful transactions"
    )
    failed_transactions = models.PositiveIntegerField(
        default=0,
        help_text="Number of failed transactions"
    )
    average_processing_time_seconds = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average processing time in seconds"
    )
    uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Integration uptime percentage"
    )
    
    # Error Handling and Monitoring
    error_notification_emails = models.JSONField(
        default=list,
        help_text="Email addresses for error notifications"
    )
    max_retry_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts for failed operations"
    )
    retry_delay_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Delay between retry attempts in seconds"
    )
    error_log_retention_days = models.PositiveIntegerField(
        default=90,
        help_text="Number of days to retain error logs"
    )
    
    # Security Configuration
    encryption_enabled = models.BooleanField(
        default=True,
        help_text="Whether data encryption is enabled"
    )
    ssl_verification = models.BooleanField(
        default=True,
        help_text="Whether SSL certificate verification is enabled"
    )
    ip_whitelist = models.JSONField(
        default=list,
        help_text="IP addresses allowed to access the integration"
    )
    rate_limit_enabled = models.BooleanField(
        default=True,
        help_text="Whether rate limiting is enabled"
    )
    rate_limit_requests_per_minute = models.PositiveIntegerField(
        default=60,
        help_text="Maximum requests per minute"
    )
    
    # Implementation Details
    implementation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date integration was implemented"
    )
    go_live_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date integration went live"
    )
    implementation_team = models.JSONField(
        default=list,
        help_text="Team members involved in implementation"
    )
    vendor_contacts = models.JSONField(
        default=list,
        help_text="Vendor contact information"
    )
    
    # Business Rules
    billing_schedules = models.JSONField(
        default=list,
        help_text="Billing schedule configurations"
    )
    approval_workflows = models.JSONField(
        default=list,
        help_text="Approval workflow configurations"
    )
    discount_rules = models.JSONField(
        default=list,
        help_text="Discount and pricing rules"
    )
    collection_policies = models.JSONField(
        default=list,
        help_text="Collection policy configurations"
    )
    
    # Reporting and Analytics
    reporting_enabled = models.BooleanField(
        default=True,
        help_text="Whether reporting is enabled"
    )
    report_generation_schedule = models.JSONField(
        default=list,
        help_text="Automated report generation schedule"
    )
    dashboard_metrics = models.JSONField(
        default=list,
        help_text="Metrics displayed on dashboard"
    )
    custom_reports = models.JSONField(
        default=list,
        help_text="Custom report configurations"
    )
    
    # Compliance and Audit
    audit_logging_enabled = models.BooleanField(
        default=True,
        help_text="Whether audit logging is enabled"
    )
    compliance_monitoring = models.BooleanField(
        default=True,
        help_text="Whether compliance monitoring is enabled"
    )
    audit_trail = models.JSONField(
        default=list,
        help_text="Audit trail of integration changes"
    )
    compliance_checks = models.JSONField(
        default=list,
        help_text="Compliance check configurations"
    )
    
    # Backup and Recovery
    backup_enabled = models.BooleanField(
        default=True,
        help_text="Whether data backup is enabled"
    )
    backup_frequency_hours = models.PositiveIntegerField(
        default=24,
        help_text="Backup frequency in hours"
    )
    backup_retention_days = models.PositiveIntegerField(
        default=30,
        help_text="Backup retention period in days"
    )
    disaster_recovery_plan = models.TextField(
        blank=True,
        help_text="Disaster recovery plan"
    )
    
    # Testing and Validation
    test_mode_enabled = models.BooleanField(
        default=False,
        help_text="Whether test mode is enabled"
    )
    sandbox_environment_url = models.URLField(
        blank=True,
        help_text="Sandbox environment URL for testing"
    )
    last_test_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last integration test"
    )
    test_results = models.JSONField(
        default=list,
        help_text="Results of integration tests"
    )
    
    # Contract and Commercial Terms
    contract_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract start date"
    )
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract end date"
    )
    auto_renewal_enabled = models.BooleanField(
        default=False,
        help_text="Whether contract auto-renewal is enabled"
    )
    termination_notice_days = models.PositiveIntegerField(
        default=30,
        help_text="Required notice period for termination in days"
    )
    
    # Support and Maintenance
    support_contact_email = models.EmailField(
        blank=True,
        help_text="Support contact email"
    )
    support_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Support contact phone"
    )
    maintenance_windows = models.JSONField(
        default=list,
        help_text="Scheduled maintenance windows"
    )
    escalation_procedures = models.JSONField(
        default=list,
        help_text="Issue escalation procedures"
    )
    
    # User Access and Permissions
    authorized_users = models.JSONField(
        default=list,
        help_text="Users authorized to access this integration"
    )
    role_based_permissions = models.JSONField(
        default=dict,
        help_text="Role-based permission configurations"
    )
    access_logs = models.JSONField(
        default=list,
        help_text="User access logs"
    )
    
    # Status Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether integration is active"
    )
    requires_attention = models.BooleanField(
        default=False,
        help_text="Whether integration requires attention"
    )
    health_status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
            ('down', 'Down'),
            ('unknown', 'Unknown')
        ],
        default='unknown',
        help_text="Overall health status of integration"
    )
    
    # Additional Information
    integration_notes = models.TextField(
        blank=True,
        help_text="Notes about the integration"
    )
    known_issues = models.TextField(
        blank=True,
        help_text="Known issues or limitations"
    )
    future_enhancements = models.TextField(
        blank=True,
        help_text="Planned future enhancements"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_billing_integrations',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_billing_integrations',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['hospital', 'billing_system', 'integration_type']]
        ordering = ['-integration_type', 'integration_name']
        indexes = [
            models.Index(fields=['hospital', 'integration_status']),
            models.Index(fields=['billing_system']),
            models.Index(fields=['integration_type']),
            models.Index(fields=['integration_status']),
            models.Index(fields=['health_status']),
            models.Index(fields=['last_sync_timestamp']),
            models.Index(fields=['next_sync_scheduled']),
            models.Index(fields=['requires_attention']),
        ]
        permissions = [
            ("can_manage_billing_integrations", "Can manage billing integrations"),
            ("can_configure_billing_systems", "Can configure billing systems"),
            ("can_view_billing_metrics", "Can view billing metrics"),
            ("can_test_integrations", "Can test integrations"),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.billing_system.name} ({self.integration_type})"

    def clean(self):
        """Validate hospital billing integration data"""
        super().clean()
        
        # Validate date relationships
        if self.contract_start_date and self.contract_end_date:
            if self.contract_start_date > self.contract_end_date:
                raise ValidationError(
                    "Contract start date must be before end date"
                )
        
        if self.implementation_date and self.go_live_date:
            if self.implementation_date > self.go_live_date:
                raise ValidationError(
                    "Implementation date must be before go-live date"
                )
        
        # Validate percentage fields
        percentage_fields = ['transaction_fee_percentage', 'uptime_percentage']
        for field_name in percentage_fields:
            value = getattr(self, field_name)
            if value is not None and (value < 0 or value > 100):
                raise ValidationError(
                    f"{field_name} must be between 0 and 100"
                )
        
        # Validate primary integration limit
        if self.integration_type == 'primary' and self.is_active:
            existing_primary = HospitalBillingIntegration.objects.filter(
                hospital=self.hospital,
                integration_type='primary',
                is_active=True
            ).exclude(pk=self.pk)
            
            if existing_primary.exists():
                raise ValidationError(
                    "Hospital can only have one active primary billing integration"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
        
        # Add to audit trail if this is an update
        if self.pk:
            old_integration = HospitalBillingIntegration.objects.get(pk=self.pk)
            if old_integration.integration_status != self.integration_status:
                self.add_to_audit_trail('status_change', {
                    'from': old_integration.integration_status,
                    'to': self.integration_status,
                    'date': timezone.now().isoformat(),
                    'changed_by': user.get_full_name() if user else 'System'
                })
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def success_rate_percentage(self):
        """Calculate transaction success rate"""
        if self.total_transactions_processed == 0:
            return None
        
        success_rate = (self.successful_transactions / self.total_transactions_processed) * 100
        return round(success_rate, 2)

    @property
    def failure_rate_percentage(self):
        """Calculate transaction failure rate"""
        if self.total_transactions_processed == 0:
            return None
        
        failure_rate = (self.failed_transactions / self.total_transactions_processed) * 100
        return round(failure_rate, 2)

    @property
    def is_sync_overdue(self):
        """Check if synchronization is overdue"""
        if not self.next_sync_scheduled:
            return False
        
        return timezone.now() > self.next_sync_scheduled

    @property
    def days_since_last_sync(self):
        """Calculate days since last sync"""
        if not self.last_sync_timestamp:
            return None
        
        delta = timezone.now() - self.last_sync_timestamp
        return delta.days

    @property
    def contract_days_remaining(self):
        """Calculate days remaining in contract"""
        if not self.contract_end_date:
            return None
        
        delta = self.contract_end_date - timezone.now().date()
        return delta.days if delta.days > 0 else 0

    @property
    def monthly_transaction_volume(self):
        """Estimate monthly transaction volume"""
        if not self.last_sync_timestamp or self.days_since_last_sync is None:
            return None
        
        if self.days_since_last_sync == 0:
            return self.total_transactions_processed
        
        daily_avg = self.total_transactions_processed / max(self.days_since_last_sync, 1)
        return round(daily_avg * 30)

    def calculate_monthly_cost(self):
        """Calculate total monthly cost"""
        monthly_cost = Decimal('0.00')
        
        if self.monthly_subscription_fee:
            monthly_cost += self.monthly_subscription_fee
        
        if self.transaction_fee_percentage and self.monthly_transaction_volume:
            # Estimate transaction fees (would need transaction amounts for accurate calculation)
            estimated_transaction_fees = Decimal('0.00')  # Placeholder
            monthly_cost += estimated_transaction_fees
        
        return monthly_cost

    def test_connection(self):
        """Test connection to billing system"""
        if not self.api_endpoint:
            return {
                'success': False,
                'message': 'No API endpoint configured',
                'response_time': None
            }
        
        try:
            import requests
            import time
            
            start_time = time.time()
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(
                f"{self.api_endpoint}/health",
                headers=headers,
                timeout=30,
                verify=self.ssl_verification
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
            
            if response.status_code == 200:
                self.health_status = 'healthy'
                self.last_test_date = timezone.now()
                self.save()
                
                return {
                    'success': True,
                    'message': 'Connection successful',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                self.health_status = 'warning'
                self.save()
                
                return {
                    'success': False,
                    'message': f'Connection failed with status {response.status_code}',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
        
        except Exception as e:
            self.health_status = 'critical'
            self.save()
            
            return {
                'success': False,
                'message': f'Connection error: {str(e)}',
                'response_time': None
            }

    def sync_data(self, data_type='all', force=False):
        """Synchronize data with billing system"""
        if self.integration_status != 'active' and not force:
            return {
                'success': False,
                'message': 'Integration is not active'
            }
        
        try:
            sync_results = {
                'success': True,
                'synced_records': 0,
                'failed_records': 0,
                'errors': []
            }
            
            # Implement actual sync logic here
            # This is a placeholder implementation
            
            self.last_sync_timestamp = timezone.now()
            
            # Schedule next sync
            if self.sync_frequency_minutes:
                from datetime import timedelta
                self.next_sync_scheduled = timezone.now() + timedelta(minutes=self.sync_frequency_minutes)
            
            self.save()
            
            return sync_results
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}'
            }

    def process_payment(self, payment_data):
        """Process a payment through the billing system"""
        if self.integration_status != 'active':
            return {
                'success': False,
                'message': 'Integration is not active'
            }
        
        try:
            # Implement actual payment processing logic here
            # This is a placeholder implementation
            
            # Update transaction counters
            self.total_transactions_processed += 1
            self.successful_transactions += 1
            self.save()
            
            return {
                'success': True,
                'transaction_id': f'TXN_{timezone.now().strftime("%Y%m%d%H%M%S")}',
                'message': 'Payment processed successfully'
            }
        
        except Exception as e:
            self.total_transactions_processed += 1
            self.failed_transactions += 1
            self.save()
            
            return {
                'success': False,
                'message': f'Payment processing failed: {str(e)}'
            }

    def generate_report(self, report_type='summary', date_range=None):
        """Generate integration report"""
        report_data = {
            'integration_name': self.integration_name,
            'billing_system': self.billing_system.name,
            'status': self.get_integration_status_display(),
            'health_status': self.get_health_status_display(),
            'performance_metrics': {
                'total_transactions': self.total_transactions_processed,
                'success_rate': self.success_rate_percentage,
                'failure_rate': self.failure_rate_percentage,
                'uptime': self.uptime_percentage,
                'avg_processing_time': self.average_processing_time_seconds
            },
            'sync_status': {
                'last_sync': self.last_sync_timestamp,
                'next_sync': self.next_sync_scheduled,
                'sync_overdue': self.is_sync_overdue
            },
            'financial': {
                'monthly_cost': self.monthly_subscription_fee,
                'transaction_fee': self.transaction_fee_percentage,
                'setup_fee_paid': self.setup_fee_paid
            }
        }
        
        if report_type == 'detailed':
            report_data.update({
                'configuration': {
                    'data_sync_method': self.get_data_sync_method_display(),
                    'sync_frequency': self.sync_frequency_minutes,
                    'auto_billing': self.automatic_billing_enabled,
                    'claims_submission': self.claims_submission_enabled
                },
                'security': {
                    'encryption_enabled': self.encryption_enabled,
                    'ssl_verification': self.ssl_verification,
                    'rate_limiting': self.rate_limit_enabled
                },
                'contract': {
                    'start_date': self.contract_start_date,
                    'end_date': self.contract_end_date,
                    'days_remaining': self.contract_days_remaining
                }
            })
        
        return report_data

    def activate_integration(self, user=None):
        """Activate the integration"""
        # Test connection before activation
        test_result = self.test_connection()
        
        if not test_result['success']:
            return {
                'success': False,
                'message': f'Cannot activate: {test_result["message"]}'
            }
        
        self.integration_status = 'active'
        self.health_status = 'healthy'
        
        self.add_to_audit_trail('activation', {
            'activated_by': user.get_full_name() if user else 'System',
            'activation_date': timezone.now().isoformat(),
            'test_result': test_result
        })
        
        self.save()
        
        return {
            'success': True,
            'message': 'Integration activated successfully'
        }

    def deactivate_integration(self, reason=None, user=None):
        """Deactivate the integration"""
        self.integration_status = 'inactive'
        self.health_status = 'down'
        
        self.add_to_audit_trail('deactivation', {
            'deactivated_by': user.get_full_name() if user else 'System',
            'deactivation_date': timezone.now().isoformat(),
            'reason': reason
        })
        
        self.save()
        
        return {
            'success': True,
            'message': 'Integration deactivated successfully'
        }

    def update_health_status(self):
        """Update health status based on recent performance"""
        if self.integration_status != 'active':
            self.health_status = 'down'
            return
        
        # Check various health indicators
        health_score = 0
        
        # Success rate indicator
        if self.success_rate_percentage:
            if self.success_rate_percentage >= 95:
                health_score += 25
            elif self.success_rate_percentage >= 90:
                health_score += 20
            elif self.success_rate_percentage >= 80:
                health_score += 15
            else:
                health_score += 5
        
        # Uptime indicator
        if self.uptime_percentage:
            if self.uptime_percentage >= 99:
                health_score += 25
            elif self.uptime_percentage >= 95:
                health_score += 20
            elif self.uptime_percentage >= 90:
                health_score += 15
            else:
                health_score += 5
        
        # Sync status indicator
        if not self.is_sync_overdue:
            health_score += 25
        
        # Response time indicator
        if self.average_processing_time_seconds:
            if self.average_processing_time_seconds <= 2:
                health_score += 25
            elif self.average_processing_time_seconds <= 5:
                health_score += 20
            elif self.average_processing_time_seconds <= 10:
                health_score += 15
            else:
                health_score += 5
        
        # Determine health status
        if health_score >= 80:
            self.health_status = 'healthy'
        elif health_score >= 60:
            self.health_status = 'warning'
        else:
            self.health_status = 'critical'
        
        self.save()

    def add_to_audit_trail(self, event_type, event_data):
        """Add an event to audit trail"""
        if not isinstance(self.audit_trail, list):
            self.audit_trail = []
        
        audit_entry = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        self.audit_trail.append(audit_entry)
        
        # Keep only last 100 entries
        if len(self.audit_trail) > 100:
            self.audit_trail = self.audit_trail[-100:]

    def get_integration_summary(self):
        """Get integration summary for dashboard"""
        return {
            'name': self.integration_name,
            'billing_system': self.billing_system.name,
            'type': self.get_integration_type_display(),
            'status': self.get_integration_status_display(),
            'health': self.get_health_status_display(),
            'success_rate': self.success_rate_percentage,
            'last_sync': self.last_sync_timestamp,
            'requires_attention': self.requires_attention,
            'monthly_cost': self.monthly_subscription_fee
        }

    def get_alerts(self):
        """Get list of alerts for this integration"""
        alerts = []
        
        if self.health_status == 'critical':
            alerts.append({
                'type': 'error',
                'message': 'Integration health is critical',
                'priority': 'high'
            })
        elif self.health_status == 'warning':
            alerts.append({
                'type': 'warning',
                'message': 'Integration health needs attention',
                'priority': 'medium'
            })
        
        if self.is_sync_overdue:
            alerts.append({
                'type': 'warning',
                'message': 'Data synchronization is overdue',
                'priority': 'medium'
            })
        
        if self.contract_days_remaining and self.contract_days_remaining <= 30:
            alerts.append({
                'type': 'info',
                'message': f'Contract expires in {self.contract_days_remaining} days',
                'priority': 'low'
            })
        
        if self.failure_rate_percentage and self.failure_rate_percentage > 10:
            alerts.append({
                'type': 'warning',
                'message': f'High failure rate: {self.failure_rate_percentage}%',
                'priority': 'medium'
            })
        
        return alerts

    @classmethod
    def get_hospital_integration_overview(cls, hospital):
        """Get integration overview for a hospital"""
        from django.db.models import Count, Avg
        
        integrations = cls.objects.filter(hospital=hospital, is_active=True)
        
        overview = integrations.aggregate(
            total_integrations=Count('id'),
            active_integrations=Count('id', filter=models.Q(integration_status='active')),
            healthy_integrations=Count('id', filter=models.Q(health_status='healthy')),
            avg_success_rate=Avg('successful_transactions') * 100 / Avg('total_transactions_processed'),
            total_transactions=models.Sum('total_transactions_processed')
        )
        
        overview['health_percentage'] = 0
        if overview['total_integrations'] > 0:
            overview['health_percentage'] = round(
                (overview['healthy_integrations'] / overview['total_integrations']) * 100, 1
            )
        
        return overview

    @classmethod
    def get_sync_overdue_integrations(cls, hospital=None):
        """Get integrations with overdue synchronization"""
        queryset = cls.objects.filter(
            next_sync_scheduled__lt=timezone.now(),
            integration_status='active',
            is_active=True
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('next_sync_scheduled')

    @classmethod
    def get_integration_dashboard_data(cls, hospital=None):
        """Get comprehensive integration dashboard data"""
        queryset = cls.objects.filter(is_active=True)
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        from django.db.models import Count, Avg
        
        return {
            'overview': queryset.aggregate(
                total=Count('id'),
                active=Count('id', filter=models.Q(integration_status='active')),
                healthy=Count('id', filter=models.Q(health_status='healthy')),
                critical=Count('id', filter=models.Q(health_status='critical'))
            ),
            'by_type': queryset.values('integration_type').annotate(count=Count('id')),
            'by_status': queryset.values('integration_status').annotate(count=Count('id')),
            'by_health': queryset.values('health_status').annotate(count=Count('id')),
            'sync_overdue': queryset.filter(
                next_sync_scheduled__lt=timezone.now(),
                integration_status='active'
            ).count(),
            'contract_expiring': queryset.filter(
                contract_end_date__lte=timezone.now().date() + timezone.timedelta(days=30)
            ).count()
        }