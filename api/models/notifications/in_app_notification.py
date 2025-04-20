from django.db import models
from django.utils import timezone

class InAppNotification(models.Model):
    """Model for in-app notifications"""
    user = models.ForeignKey('api.CustomUser', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save() 