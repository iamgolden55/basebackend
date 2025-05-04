from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Medical Record Access Security fields
    medical_record_otp = models.CharField(max_length=6, null=True, blank=True)
    medical_record_otp_created_at = models.DateTimeField(null=True, blank=True)
    medical_record_access_token = models.CharField(max_length=64, null=True, blank=True)
    medical_record_token_created_at = models.DateTimeField(null=True, blank=True) 