from django.db import models
from django.conf import settings

class MedicalRecordAccess(models.Model):
    """
    Model to log every access to medical records for security auditing
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_record_accesses'
    )
    access_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Medical Record Access Log"
        verbose_name_plural = "Medical Record Access Logs"
        ordering = ['-access_time']
        
    def __str__(self):
        return f"{self.user.email} accessed at {self.access_time}" 