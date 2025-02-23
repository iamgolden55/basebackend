# api/models/medical/hospital_auth.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .hospital import Hospital
from api.models.user.custom_user import CustomUser
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

class HospitalAdminManager(BaseUserManager):
    def create_hospital_admin(self, email, hospital, password=None, **extra_fields):
        """
        Create a hospital administrator account
        """
        if not email:
            raise ValueError('Hospital admin must have an email address')
        if not hospital:
            raise ValueError('Hospital admin must be associated with a hospital')
            
        admin = self.model(
            email=self.normalize_email(email),
            hospital=hospital,
            **extra_fields
        )
        admin.set_password(password)
        admin.save(using=self._db)
        return admin

class HospitalAdmin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='hospital_admin_profile', null=True)
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # This will be removed later

    def save(self, *args, **kwargs):
        creating = self._state.adding  # Check if this is a new instance
        if creating:
            # Create CustomUser first
            user = CustomUser.objects.create(
                email=self.email,
                first_name=self.name.split()[0],
                last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 else '',
                role='hospital_admin',  # Set the role
                is_staff=True,  # Give them staff access
                is_email_verified=True  # They're pre-verified
            )
            user.set_password(self.password)
            user.save()
            
            # Link the user
            self.user = user
            # Don't store password here anymore
            self.password = ''
            
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return self.user.check_password(raw_password) 