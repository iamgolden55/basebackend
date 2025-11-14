from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid


class MessageAuditLog(TimestampedModel):
    """
    HIPAA-compliant audit logging for all messaging activities
    Tracks who accessed what, when, and from where for compliance
    """
    AUDIT_ACTIONS = [
        # Message actions
        ('message_sent', 'Message Sent'),
        ('message_read', 'Message Read'),
        ('message_edited', 'Message Edited'),
        ('message_deleted', 'Message Deleted'),
        ('message_forwarded', 'Message Forwarded'),
        
        # Conversation actions
        ('conversation_created', 'Conversation Created'),
        ('conversation_joined', 'Joined Conversation'),
        ('conversation_left', 'Left Conversation'),
        ('participant_added', 'Participant Added'),
        ('participant_removed', 'Participant Removed'),
        
        # Attachment actions
        ('attachment_uploaded', 'Attachment Uploaded'),
        ('attachment_downloaded', 'Attachment Downloaded'),
        ('attachment_viewed', 'Attachment Viewed'),
        ('attachment_deleted', 'Attachment Deleted'),
        
        # Security actions
        ('login_attempt', 'Login Attempt'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('encryption_failure', 'Encryption Failure'),
        ('decryption_failure', 'Decryption Failure'),
        
        # System actions
        ('storage_strategy_switch', 'Storage Strategy Switch'),
        ('data_migration', 'Data Migration'),
        ('backup_created', 'Backup Created'),
        ('retention_cleanup', 'Retention Cleanup'),
        
        # Medical context actions
        ('patient_context_added', 'Patient Context Added'),
        ('patient_context_removed', 'Patient Context Removed'),
        ('medical_data_accessed', 'Medical Data Accessed'),
        ('emergency_alert_sent', 'Emergency Alert Sent'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # What happened
    action = models.CharField(max_length=50, choices=AUDIT_ACTIONS)
    description = models.TextField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, default='low')
    
    # Who did it
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text="User who performed the action (null for system actions)"
    )
    user_role = models.CharField(max_length=100, blank=True, null=True)
    user_department = models.CharField(max_length=100, blank=True, null=True)
    
    # What was affected
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        'Message',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    attachment = models.ForeignKey(
        'MessageAttachment',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    
    # When and where
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Healthcare context
    patient_context = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        related_name='audit_logs_as_patient',
        null=True,
        blank=True,
        help_text="Patient affected by this action"
    )
    hospital_context = models.ForeignKey(
        'Hospital',
        on_delete=models.SET_NULL,
        related_name='messaging_audit_logs',
        null=True,
        blank=True
    )
    department_context = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional details (JSON)
    details = models.JSONField(default=dict, blank=True)
    
    # Security and compliance
    is_suspicious = models.BooleanField(default=False)
    requires_investigation = models.BooleanField(default=False)
    investigation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('investigating', 'Under Investigation'),
            ('resolved', 'Resolved'),
            ('false_positive', 'False Positive'),
        ],
        blank=True,
        null=True
    )
    
    # Data retention
    retention_date = models.DateTimeField(
        help_text="Date when this audit log should be archived/deleted",
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'messaging_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['patient_context', 'timestamp']),
            models.Index(fields=['hospital_context', 'timestamp']),
            models.Index(fields=['risk_level', 'is_suspicious']),
            models.Index(fields=['requires_investigation', 'investigation_status']),
            models.Index(fields=['timestamp', 'action']),  # For time-based queries
        ]
    
    def __str__(self):
        user_info = f"{self.user.get_full_name()}" if self.user else "System"
        return f"{user_info} - {self.get_action_display()} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Override save to set retention date and risk assessment"""
        if not self.retention_date:
            # Default 7 years retention for healthcare data
            retention_years = 7
            if self.patient_context or self.action in ['medical_data_accessed', 'patient_context_added']:
                retention_years = 10  # Longer for patient-related actions
            
            self.retention_date = timezone.now() + timezone.timedelta(days=365 * retention_years)
        
        # Auto-assess risk level if not set
        if self.risk_level == 'low':
            self.risk_level = self._assess_risk_level()
        
        # Check for suspicious activity
        if not self.is_suspicious:
            self.is_suspicious = self._detect_suspicious_activity()
        
        super().save(*args, **kwargs)
        
        # Trigger real-time monitoring if high risk
        if self.risk_level in ['high', 'critical'] or self.is_suspicious:
            self._trigger_security_alert()
    
    def _assess_risk_level(self) -> str:
        """Automatically assess risk level based on action and context"""
        high_risk_actions = [
            'unauthorized_access', 'encryption_failure', 'decryption_failure',
            'medical_data_accessed', 'emergency_alert_sent'
        ]
        
        medium_risk_actions = [
            'message_deleted', 'participant_removed', 'attachment_deleted',
            'patient_context_added', 'patient_context_removed'
        ]
        
        if self.action in high_risk_actions:
            return 'high'
        elif self.action in medium_risk_actions:
            return 'medium'
        elif self.patient_context or self.hospital_context:
            return 'medium'  # Any action with medical context is medium risk
        else:
            return 'low'
    
    def _detect_suspicious_activity(self) -> bool:
        """Detect potentially suspicious activity patterns"""
        # Check for rapid successive actions
        if self.user:
            recent_actions = MessageAuditLog.objects.filter(
                user=self.user,
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
            ).count()
            
            if recent_actions > 50:  # More than 50 actions in 5 minutes
                return True
        
        # Check for access outside normal hours (if hospital has specific hours)
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM
            if self.action in ['medical_data_accessed', 'attachment_downloaded']:
                return True
        
        # Check for unusual IP addresses
        if self.ip_address and self.user:
            # Get user's typical IP addresses (simplified)
            usual_ips = MessageAuditLog.objects.filter(
                user=self.user,
                timestamp__gte=timezone.now() - timezone.timedelta(days=30)
            ).values_list('ip_address', flat=True).distinct()
            
            if self.ip_address not in usual_ips and len(usual_ips) > 0:
                return True
        
        return False
    
    def _trigger_security_alert(self):
        """Trigger real-time security alert for high-risk activities"""
        try:
            from api.tasks.messaging import send_security_alert
            send_security_alert.delay(str(self.id))
        except ImportError:
            # Fallback to email notification
            self._send_security_email()
    
    def _send_security_email(self):
        """Send security alert email to administrators"""
        try:
            from django.core.mail import mail_admins
            
            subject = f"Security Alert: {self.get_action_display()}"
            message = f"""
            Security Alert Details:
            
            Action: {self.get_action_display()}
            User: {self.user.get_full_name() if self.user else 'System'}
            Timestamp: {self.timestamp}
            Risk Level: {self.get_risk_level_display()}
            Suspicious: {self.is_suspicious}
            
            IP Address: {self.ip_address}
            User Agent: {self.user_agent[:100] if self.user_agent else 'N/A'}
            
            Details: {self.details}
            
            Investigation Required: {self.requires_investigation}
            """
            
            mail_admins(subject, message, fail_silently=True)
            
        except Exception as e:
            import logging
            logger = logging.getLogger('messaging.security')
            logger.error(f"Failed to send security alert email: {e}")
    
    @classmethod
    def log_action(cls, action, user=None, conversation=None, message=None, 
                   attachment=None, patient_context=None, hospital_context=None,
                   ip_address=None, user_agent=None, details=None, request=None):
        """
        Convenience method to create audit log entries
        
        Args:
            action: Action being performed
            user: User performing the action
            conversation: Conversation affected
            message: Message affected
            attachment: Attachment affected
            patient_context: Patient affected
            hospital_context: Hospital affected
            ip_address: IP address of the user
            user_agent: User agent string
            details: Additional details as dict
            request: Django request object (to extract IP and user agent)
        """
        # Extract info from request if provided
        if request:
            if not ip_address:
                ip_address = cls._get_client_ip(request)
            if not user_agent:
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not user and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
        
        # Get user context
        user_role = None
        user_department = None
        if user:
            user_role = getattr(user, 'role', None)
            # Try to get department from hospital admin
            if hasattr(user, 'hospital_admin'):
                user_department = getattr(user.hospital_admin, 'department', None)
        
        return cls.objects.create(
            action=action,
            user=user,
            user_role=user_role,
            user_department=user_department,
            conversation=conversation,
            message=message,
            attachment=attachment,
            patient_context=patient_context,
            hospital_context=hospital_context,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,  # Limit length
            details=details or {},
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def mark_investigated(self, status='resolved', notes=None):
        """Mark audit log as investigated"""
        self.investigation_status = status
        self.requires_investigation = (status == 'pending')
        
        if notes:
            if 'investigation_notes' not in self.details:
                self.details['investigation_notes'] = []
            self.details['investigation_notes'].append({
                'timestamp': timezone.now().isoformat(),
                'notes': notes,
                'status': status
            })
        
        self.save(update_fields=['investigation_status', 'requires_investigation', 'details'])
    
    def get_summary(self) -> dict:
        """Get summary of audit log for reporting"""
        return {
            'id': str(self.id),
            'action': self.get_action_display(),
            'user': self.user.get_full_name() if self.user else 'System',
            'timestamp': self.timestamp.isoformat(),
            'risk_level': self.get_risk_level_display(),
            'suspicious': self.is_suspicious,
            'patient_involved': bool(self.patient_context),
            'hospital': self.hospital_context.name if self.hospital_context else None,
            'investigation_required': self.requires_investigation,
        }