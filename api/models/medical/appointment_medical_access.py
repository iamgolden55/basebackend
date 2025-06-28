"""
🛡️ APPOINTMENT MEDICAL ACCESS - SECURE TIME-LIMITED SHARING
Links appointments with medical record sharing permissions
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid
from datetime import timedelta


class AppointmentMedicalAccess(models.Model):
    """
    🔐 Manages time-limited access to patient medical records during appointments
    Enables patients to share both structured medical data and documents with doctors
    """
    
    ACCESS_TYPE_CHOICES = [
        ('medical_records', 'Medical Records Only'),
        ('documents', 'Documents Only'),
        ('full_access', 'Medical Records + Documents'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Access Requested'),
        ('granted', 'Access Granted'),
        ('denied', 'Access Denied'),
        ('expired', 'Access Expired'),
        ('revoked', 'Access Revoked'),
    ]
    
    # Core relationships
    appointment = models.OneToOneField(
        'api.Appointment',
        on_delete=models.CASCADE,
        related_name='medical_access'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='granted_medical_access'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_medical_access'
    )
    
    # Access configuration
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='full_access'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='requested'
    )
    
    # Time management
    requested_at = models.DateTimeField(auto_now_add=True)
    granted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    # Access token for secure sharing
    access_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Notes and reasons
    request_reason = models.TextField(
        blank=True,
        help_text="Doctor's reason for requesting access"
    )
    patient_notes = models.TextField(
        blank=True,
        help_text="Patient's notes when granting/denying access"
    )
    
    # Access tracking
    first_accessed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['appointment', 'status']),
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['access_token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Medical Access: {self.appointment.appointment_id} - {self.status}"
    
    def grant_access(self, duration_hours=2, patient_notes=None):
        """Grant access for specified duration"""
        self.status = 'granted'
        self.granted_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(hours=duration_hours)
        
        if patient_notes:
            self.patient_notes = patient_notes
            
        self.save()
        
        # Create document shares for the appointment
        self._create_document_shares()
        
        # Log the access grant
        self._log_access_event('access_granted')
    
    def deny_access(self, reason=None):
        """Deny the access request"""
        self.status = 'denied'
        if reason:
            self.patient_notes = reason
        self.save()
        
        # Log the denial
        self._log_access_event('access_denied')
    
    def revoke_access(self, reason=None):
        """Revoke previously granted access"""
        if self.status != 'granted':
            return False
            
        self.status = 'revoked'
        self.revoked_at = timezone.now()
        if reason:
            self.patient_notes = f"{self.patient_notes}\nRevoked: {reason}" if self.patient_notes else f"Revoked: {reason}"
        
        self.save()
        
        # Revoke related document shares
        self._revoke_document_shares()
        
        # Log the revocation
        self._log_access_event('access_revoked')
        return True
    
    def mark_accessed(self):
        """Track access to medical records"""
        now = timezone.now()
        
        if not self.first_accessed_at:
            self.first_accessed_at = now
            
        self.last_accessed_at = now
        self.access_count += 1
        self.save(update_fields=['first_accessed_at', 'last_accessed_at', 'access_count'])
        
        # Log the access
        self._log_access_event('record_accessed')
    
    @property
    def is_active(self):
        """Check if access is currently active"""
        if self.status != 'granted':
            return False
            
        if self.expires_at and timezone.now() > self.expires_at:
            # Auto-expire
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
            
        return True
    
    @property
    def time_remaining(self):
        """Get remaining time for access"""
        if not self.is_active or not self.expires_at:
            return None
            
        remaining = self.expires_at - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None
    
    @property
    def can_access_medical_records(self):
        """Check if can access structured medical records"""
        return (
            self.is_active and 
            self.access_type in ['medical_records', 'full_access']
        )
    
    @property
    def can_access_documents(self):
        """Check if can access medical documents"""
        return (
            self.is_active and 
            self.access_type in ['documents', 'full_access']
        )
    
    def _create_document_shares(self):
        """Create DocumentShare entries for the appointment"""
        if not self.can_access_documents:
            return
            
        from api.models.secure_documents import DocumentShare, SecureDocument
        
        # Get all patient's documents
        patient_documents = SecureDocument.objects.filter(
            user=self.patient,
            is_active=True
        )
        
        for document in patient_documents:
            # Create or update document share
            share, created = DocumentShare.objects.get_or_create(
                document=document,
                shared_by=self.patient,
                share_type='appointment',
                allowed_email=self.doctor.email,
                defaults={
                    'expires_at': self.expires_at,
                    'max_accesses': 10,  # Allow multiple views during appointment
                    'is_active': True,
                }
            )
            
            if not created and share.expires_at != self.expires_at:
                # Update expiry time if share already exists
                share.expires_at = self.expires_at
                share.is_active = True
                share.save()
    
    def _revoke_document_shares(self):
        """Revoke all related document shares"""
        from api.models.secure_documents import DocumentShare
        
        appointment_shares = DocumentShare.objects.filter(
            shared_by=self.patient,
            share_type='appointment',
            allowed_email=self.doctor.email,
            is_active=True,
            expires_at=self.expires_at  # Match the specific appointment session
        )
        
        appointment_shares.update(is_revoked=True, is_active=False)
    
    def _log_access_event(self, event_type):
        """Log access events for audit trail"""
        from api.models.secure_documents import DocumentAccessLog
        
        # Create a system log entry
        # Note: This would ideally go to a dedicated audit system
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(
            f"MEDICAL_ACCESS_EVENT: {event_type} - "
            f"Appointment: {self.appointment.appointment_id}, "
            f"Patient: {self.patient.email}, "
            f"Doctor: {self.doctor.email}, "
            f"Access Type: {self.access_type}, "
            f"Token: {self.access_token}"
        )
    
    @classmethod
    def request_access(cls, appointment, doctor, access_type='full_access', reason=None):
        """Create a new access request"""
        access_request, created = cls.objects.get_or_create(
            appointment=appointment,
            defaults={
                'patient': appointment.patient,
                'doctor': doctor,
                'access_type': access_type,
                'request_reason': reason or f"Medical consultation for appointment {appointment.appointment_id}",
                'status': 'requested',
            }
        )
        
        if not created:
            # Update existing request
            access_request.status = 'requested'
            access_request.access_type = access_type
            if reason:
                access_request.request_reason = reason
            access_request.save()
        
        # Log the request
        access_request._log_access_event('access_requested')
        
        return access_request
    
    @classmethod
    def get_active_access(cls, appointment, doctor):
        """Get active access for appointment and doctor"""
        try:
            access = cls.objects.get(
                appointment=appointment,
                doctor=doctor,
                status='granted'
            )
            return access if access.is_active else None
        except cls.DoesNotExist:
            return None


class MedicalAccessAuditLog(models.Model):
    """
    📊 Detailed audit trail for medical access events
    """
    
    EVENT_TYPES = [
        ('access_requested', 'Access Requested'),
        ('access_granted', 'Access Granted'),
        ('access_denied', 'Access Denied'),
        ('access_revoked', 'Access Revoked'),
        ('record_accessed', 'Medical Record Accessed'),
        ('document_accessed', 'Document Accessed'),
        ('access_expired', 'Access Expired'),
    ]
    
    medical_access = models.ForeignKey(
        AppointmentMedicalAccess,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_timestamp = models.DateTimeField(auto_now_add=True)
    
    # User who triggered the event
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Additional event data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-event_timestamp']
        indexes = [
            models.Index(fields=['medical_access', 'event_type']),
            models.Index(fields=['event_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.medical_access.appointment.appointment_id} at {self.event_timestamp}"