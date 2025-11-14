# api/models/medical/pharmacy.py

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..base import TimestampedModel

User = get_user_model()


class Pharmacy(TimestampedModel):
    """
    Standalone pharmacy model for PHB pharmacies.
    Tracks pharmacy information for nomination and prescription delivery.
    """

    # PHB Organization identification
    phb_pharmacy_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="PHB pharmacy code (e.g., PHB-PH-001)"
    )
    name = models.CharField(max_length=255)

    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=10, db_index=True)
    country = models.CharField(max_length=100, default='Nigeria')

    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Electronic prescription capability
    electronic_prescriptions_enabled = models.BooleanField(
        default=False,
        help_text="Can receive electronic prescriptions via PHB system"
    )

    # Services and hours (JSON fields)
    opening_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Format: {'monday': {'open': '09:00', 'close': '18:00', 'closed': False}, ...}"
    )
    services_offered = models.JSONField(
        default=list,
        blank=True,
        help_text="List of services: ['prescription_collection', 'flu_jab', 'health_check', 'delivery', ...]"
    )

    # Geolocation for map display
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True,
        help_text="Latitude coordinate for map display"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True,
        help_text="Longitude coordinate for map display"
    )

    # Hospital affiliation (optional - some pharmacies are hospital-based)
    hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affiliated_pharmacies',
        help_text="If pharmacy is part of a hospital"
    )

    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether pharmacy is currently active in the system"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether pharmacy has been verified by PHB admin"
    )

    # Additional information
    description = models.TextField(
        blank=True,
        help_text="Brief description of the pharmacy"
    )

    class Meta:
        verbose_name_plural = "Pharmacies"
        ordering = ['name']
        indexes = [
            models.Index(fields=['phb_pharmacy_code']),
            models.Index(fields=['postcode']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['electronic_prescriptions_enabled', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phb_pharmacy_code})"

    def is_open_now(self):
        """Check if pharmacy is currently open based on opening hours"""
        from datetime import datetime

        if not self.opening_hours:
            return False

        now = datetime.now()
        day_name = now.strftime('%A').lower()

        if day_name not in self.opening_hours:
            return False

        hours = self.opening_hours[day_name]
        if not hours or hours.get('closed'):
            return False

        try:
            current_time = now.time()
            open_time = datetime.strptime(hours['open'], '%H:%M').time()
            close_time = datetime.strptime(hours['close'], '%H:%M').time()

            return open_time <= current_time <= close_time
        except (KeyError, ValueError):
            # If there's an error parsing times, return False
            return False

    def get_full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postcode,
            self.country
        ]
        return ', '.join(filter(None, address_parts))


class NominatedPharmacy(TimestampedModel):
    """
    User's nominated pharmacy for electronic prescription delivery.
    Each user can have only ONE current nominated pharmacy.
    """

    NOMINATION_TYPE_CHOICES = [
        ('repeat', 'Repeat nomination'),       # Ongoing (default) - all prescriptions
        ('acute', 'Acute nomination'),         # Acute prescriptions only
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pharmacy_nominations'
    )
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name='nominations',
        null=True,
        blank=True,
        help_text="Admin-created pharmacy (can be hospital-affiliated)"
    )
    practice_page = models.ForeignKey(
        'ProfessionalPracticePage',
        on_delete=models.CASCADE,
        related_name='nominations',
        null=True,
        blank=True,
        help_text="Professional-created practice page (mutually exclusive with pharmacy)"
    )

    nomination_type = models.CharField(
        max_length=20,
        choices=NOMINATION_TYPE_CHOICES,
        default='repeat',
        help_text="Type of nomination - repeat for all prescriptions"
    )
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Only one current nomination per user allowed"
    )

    # Timestamps
    nominated_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this nomination"
    )

    class Meta:
        ordering = ['-nominated_at']
        indexes = [
            models.Index(fields=['user', 'is_current']),
            models.Index(fields=['pharmacy', 'is_current']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_current'],
                condition=models.Q(is_current=True),
                name='unique_current_nomination_per_user'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(pharmacy__isnull=False, practice_page__isnull=True) |
                    models.Q(pharmacy__isnull=True, practice_page__isnull=False)
                ),
                name='pharmacy_or_practice_page_not_both'
            )
        ]

    def __str__(self):
        status = 'Current' if self.is_current else 'Historical'
        location_name = self.pharmacy.name if self.pharmacy else self.practice_page.practice_name
        return f"{self.user.email} → {location_name} ({status})"

    def get_nominated_location(self):
        """Get nominated location (either Pharmacy or ProfessionalPracticePage)"""
        if self.pharmacy:
            return {
                'type': 'pharmacy',
                'name': self.pharmacy.name,
                'address': self.pharmacy.address_line_1,
                'city': self.pharmacy.city,
                'phone': self.pharmacy.phone,
            }
        elif self.practice_page:
            return {
                'type': 'practice_page',
                'name': self.practice_page.practice_name,
                'address': self.practice_page.address_line_1,
                'city': self.practice_page.city,
                'phone': self.practice_page.phone,
            }
        return None

    def save(self, *args, **kwargs):
        """Ensure only one current nomination per user"""
        if self.is_current:
            # End all other current nominations for this user
            NominatedPharmacy.objects.filter(
                user=self.user,
                is_current=True
            ).exclude(pk=self.pk).update(
                is_current=False,
                ended_at=timezone.now()
            )
        super().save(*args, **kwargs)

    def end_nomination(self):
        """End this nomination"""
        self.is_current = False
        self.ended_at = timezone.now()
        self.save()


# Signal handlers to update nomination counts
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(post_save, sender=NominatedPharmacy)
def update_nomination_count_on_create(sender, instance, created, **kwargs):
    """Update practice page nomination count when a nomination is created or updated"""
    if instance.practice_page:
        # Always recalculate the current nomination count for the practice page
        current_count = NominatedPharmacy.objects.filter(
            practice_page=instance.practice_page,
            is_current=True
        ).count()

        # Update the practice page nomination count
        instance.practice_page.nomination_count = current_count
        instance.practice_page.save(update_fields=['nomination_count'])


@receiver(pre_save, sender=NominatedPharmacy)
def update_nomination_count_on_end(sender, instance, **kwargs):
    """Update practice page nomination count when a nomination is ended"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = NominatedPharmacy.objects.get(pk=instance.pk)

            # If nomination was current and is now being ended
            if old_instance.is_current and not instance.is_current:
                if instance.practice_page:
                    # Decrement will happen after save in post_save signal
                    pass

        except NominatedPharmacy.DoesNotExist:
            pass


class PharmacyAccessLog(TimestampedModel):
    """
    Model to log every access to patient prescriptions by pharmacies.
    Implements audit trail for pharmacy prescription lookups (NHS EPS standard).
    """
    # Pharmacy and Pharmacist
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name='prescription_access_logs',
        null=True,
        blank=True,
        help_text="Pharmacy that accessed the prescription"
    )
    pharmacist_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pharmacy_access_logs',
        help_text="Pharmacist user who accessed the prescription"
    )

    # Patient Information
    patient_hpn = models.CharField(
        max_length=30,
        db_index=True,
        help_text="Patient's HPN that was searched"
    )
    patient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pharmacy_lookups',
        help_text="Patient user account"
    )

    # Access Details
    access_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the access occurred"
    )
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('search', 'HPN Search'),
            ('view', 'View Prescriptions'),
            ('dispense', 'Dispense Medication'),
        ],
        default='search',
        help_text="Type of access performed"
    )

    # Prescriptions Accessed
    prescriptions_accessed = models.JSONField(
        default=list,
        help_text="List of prescription IDs accessed in this session"
    )
    prescription_count = models.IntegerField(
        default=0,
        help_text="Number of prescriptions viewed"
    )
    controlled_substance_count = models.IntegerField(
        default=0,
        help_text="Number of controlled substance prescriptions accessed"
    )

    # Technical Details
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the access"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/client user agent"
    )

    # Patient Verification (for dispensing)
    patient_verified = models.BooleanField(
        default=False,
        help_text="Whether patient identity was verified"
    )
    verification_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('', 'Not Verified'),
            ('hpn_name', 'HPN + Name Match'),
            ('government_id', 'Government ID'),
            ('biometric', 'Biometric'),
        ],
        help_text="Method used to verify patient identity"
    )

    # Result and Notes
    access_granted = models.BooleanField(
        default=True,
        help_text="Whether access was successfully granted"
    )
    denial_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason if access was denied"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this access"
    )

    class Meta:
        verbose_name = "Pharmacy Access Log"
        verbose_name_plural = "Pharmacy Access Logs"
        ordering = ['-access_time']
        indexes = [
            models.Index(fields=['pharmacy', 'access_time']),
            models.Index(fields=['patient_hpn', 'access_time']),
            models.Index(fields=['pharmacist_user', 'access_time']),
            models.Index(fields=['access_type', 'access_time']),
        ]

    def __str__(self):
        return f"{self.pharmacy.name} - {self.pharmacist_user.get_full_name()} accessed HPN {self.patient_hpn} at {self.access_time}"
