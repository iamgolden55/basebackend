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
    
    # This will not be stored in the database, just used to pass data during object creation
    _user_data = None

    # Add the custom manager
    objects = HospitalAdminManager()

    def save(self, *args, **kwargs):
        creating = self._state.adding  # Check if this is a new instance
        if creating and not self.user:
            # Get additional user data if provided
            user_data = getattr(self, '_user_data', {}) or {}
            
            # Create CustomUser first with enhanced data
            user = CustomUser.objects.create(
                email=self.email,
                first_name=self.name.split()[0] if not user_data.get('first_name') else user_data.get('first_name'),
                last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 and not user_data.get('last_name') else user_data.get('last_name', ''),
                role='hospital_admin',  # Set the role
                is_staff=True,  # Give them staff access
                is_email_verified=True,  # They're pre-verified
                date_of_birth=user_data.get('date_of_birth'),
                gender=user_data.get('gender'),
                phone=user_data.get('phone'),
                country=user_data.get('country'),
                state=user_data.get('state'),
                city=user_data.get('city'),
                preferred_language=user_data.get('preferred_language'),
                secondary_languages=user_data.get('secondary_languages', []),
                custom_language=user_data.get('custom_language', ''),
                consent_terms=user_data.get('consent_terms', False),
                consent_hipaa=user_data.get('consent_hipaa', False),
                consent_data_processing=user_data.get('consent_data_processing', False)
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