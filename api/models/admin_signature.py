from django.db import models


class AdminSignature(models.Model):
    """
    Store admin signature for hospital approval certificates
    """
    name = models.CharField(
        max_length=100,
        default="PHB Administration",
        help_text="Name to display under signature"
    )
    signature_image = models.ImageField(
        upload_to='signatures/',
        help_text="Upload your signature (PNG with transparent background recommended)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Use this signature for certificates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Signature"
        verbose_name_plural = "Admin Signatures"
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"

    def save(self, *args, **kwargs):
        # Ensure only one active signature
        if self.is_active:
            AdminSignature.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
