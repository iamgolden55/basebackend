from django.db import models
from django.contrib.postgres.fields import ArrayField

class Role(models.Model):
    """
    Role-based access control for admin users.
    Inspired by AWS IAM roles.
    """
    ROLE_TYPES = [
        ('platform_admin', 'Platform Admin'),
        ('registry_reviewer', 'Registry Reviewer'),
        ('registry_verifier', 'Registry Verifier'),
        ('support_staff', 'Support Staff'),
    ]

    name = models.CharField(max_length=100, unique=True)
    role_type = models.CharField(max_length=50, choices=ROLE_TYPES)
    description = models.TextField(blank=True)
    permissions = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="List of permission strings"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name

# Permission constants
PERMISSIONS = {
    'PLATFORM_ADMIN': [
        # Professional Applications
        'view_applications',
        'review_applications',
        'verify_documents',
        'approve_applications',
        'reject_applications',
        'suspend_licenses',
        'revoke_licenses',
        'reactivate_licenses',
        # Practice Pages
        'view_practice_pages',
        'verify_practice_pages',
        'flag_practice_pages',
        'suspend_practice_pages',
        # User Management
        'manage_users',
        # Analytics & Settings
        'view_analytics',
        'manage_settings',
        'view_audit_logs',
    ],
    'REGISTRY_REVIEWER': [
        # Professional Applications
        'view_applications',
        'review_applications',
        'verify_documents',
        'approve_applications',
        'reject_applications',
        'request_clarification',
        'request_additional_documents',
        'suspend_licenses',
        # Practice Pages
        'view_practice_pages',
        'verify_practice_pages',
        'flag_practice_pages',
        'suspend_practice_pages',
    ],
    'REGISTRY_VERIFIER': [
        # Professional Applications
        'view_applications',
        'verify_documents',
        'reject_documents',
        'request_clarification',
        # Practice Pages (read-only)
        'view_practice_pages',
    ],
    'SUPPORT_STAFF': [
        # Professional Applications (read-only)
        'view_applications',
        # Practice Pages (read-only)
        'view_practice_pages',
        # Analytics
        'view_analytics',
    ],
}
