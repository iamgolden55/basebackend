from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """
    Track all admin actions for accountability and compliance.
    """
    ACTION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('verify', 'Verify'),
        ('suspend', 'Suspend'),
        ('revoke', 'Revoke'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='registry_audit_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=100)  # e.g., 'ProfessionalApplication'
    resource_id = models.CharField(max_length=255)
    description = models.TextField()
    metadata = models.JSONField(default=dict)  # Store additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.resource_type} - {self.timestamp}"
