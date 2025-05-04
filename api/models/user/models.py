from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_email_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    # Medical Record Access Security fields
    medical_record_otp = models.CharField(max_length=6, null=True, blank=True)
    medical_record_otp_created_at = models.DateTimeField(null=True, blank=True)
    medical_record_access_token = models.CharField(max_length=64, null=True, blank=True)
    medical_record_token_created_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
 