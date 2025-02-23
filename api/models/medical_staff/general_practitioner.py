# api/models/medical_staff/general_practitioner.py

from django.db import models
from ..user.custom_user import CustomUser

class GeneralPractitioner(models.Model):
    user = models.OneToOneField(
        'api.CustomUser',
        on_delete=models.CASCADE,
        related_name='gp_profile',
        null=True,
        blank=True
    )
    practice = models.ForeignKey(
        'api.GPPractice',
        on_delete=models.SET_NULL,
        null=True,
        related_name='general_practitioners'
    )
    license_number = models.CharField(max_length=50, unique=True)
    specializations = models.TextField(blank=True)
    clinic_location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Physical location of the clinic"
    )
    consultation_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Consultation fee in local currency"
    )
    available_days = models.CharField(
        max_length=20,
        default="Monday to Friday",
        help_text="e.g., Monday to Friday"
    )

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"