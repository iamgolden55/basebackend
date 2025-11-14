"""
Professional Practice Page Models

Public-facing practice pages for approved healthcare professionals.
Allows professionals to market services (in-store or virtual).
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..base import TimestampedModel
from ..registry.professional_registry import PHBProfessionalRegistry
import uuid

User = get_user_model()


class ProfessionalPracticePage(TimestampedModel):
    """
    Public-facing practice page for approved healthcare professionals.
    Allows professionals to market services (in-store or virtual).
    """
    # Primary Keys & Relations
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='practice_page',
        help_text="Professional who owns this page"
    )
    linked_registry_entry = models.ForeignKey(
        PHBProfessionalRegistry,
        on_delete=models.PROTECT,
        related_name='practice_pages',
        help_text="Link to verified PHB registry entry"
    )

    # Basic Information
    practice_name = models.CharField(
        max_length=200,
        help_text="Name of practice (e.g., 'Golden Pharmacy Abuja')"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        help_text="URL-friendly slug (e.g., 'golden-pharmacy-abuja')"
    )
    tagline = models.CharField(
        max_length=160,
        blank=True,
        help_text="Short description for SEO and previews"
    )
    about = models.TextField(
        blank=True,
        help_text="Detailed about section (rich text supported)"
    )

    # Service Type
    SERVICE_TYPE_CHOICES = [
        ('in_store', 'In-Store/Walk-In Service'),
        ('virtual', 'Virtual Service Only'),
        ('both', 'Both In-Store and Virtual'),
    ]
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        help_text="Type of service offered"
    )

    # Physical Location (required if service_type includes 'in_store')
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')

    # Geolocation (for map display and proximity searches)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate"
    )

    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    # Opening Hours (JSONField)
    opening_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Operating hours for in-store services"
    )

    # Virtual Service Details
    virtual_consultation_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Availability for virtual consultations"
    )
    online_booking_url = models.URLField(
        blank=True,
        help_text="Link to booking system for virtual appointments"
    )
    video_platform = models.CharField(
        max_length=100,
        blank=True,
        help_text="Platform used (Zoom, Google Meet, etc.)"
    )

    # Services & Pricing (JSONField)
    services_offered = models.JSONField(
        default=list,
        blank=True,
        help_text="List of services with optional pricing"
    )

    # Payment Methods (JSONField)
    payment_methods = models.JSONField(
        default=list,
        blank=True,
        help_text="Accepted payment methods"
    )

    # Additional Credentials (JSONField)
    additional_certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="Certifications beyond PHB license"
    )

    # Languages (JSONField)
    languages_spoken = models.JSONField(
        default=list,
        blank=True,
        help_text="Languages spoken at practice"
    )

    # Publication Status
    is_published = models.BooleanField(
        default=False,
        help_text="Whether page is publicly visible"
    )

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('flagged', 'Flagged for Review'),
        ('suspended', 'Suspended'),
    ]
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        help_text="Admin verification status"
    )

    verification_notes = models.TextField(
        blank=True,
        help_text="Admin notes about verification"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_practice_pages',
        help_text="Admin who verified page"
    )
    verified_date = models.DateTimeField(null=True, blank=True)

    # Statistics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times page viewed"
    )
    nomination_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times nominated by patients"
    )

    # SEO
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO keywords"
    )

    class Meta:
        db_table = 'professional_practice_pages'
        verbose_name = 'Professional Practice Page'
        verbose_name_plural = 'Professional Practice Pages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', 'verification_status']),
            models.Index(fields=['service_type']),
            models.Index(fields=['city', 'state']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.practice_name} ({self.owner.get_full_name()})"

    def save(self, *args, **kwargs):
        # Auto-generate slug from practice_name if not provided
        if not self.slug:
            self.slug = slugify(self.practice_name)

            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while ProfessionalPracticePage.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def clean(self):
        """Validate model fields"""
        # If in_store service, require physical location
        if self.service_type in ['in_store', 'both']:
            if not (self.address_line_1 and self.city and self.state):
                raise ValidationError(
                    "Physical location required for in-store services"
                )

        # If virtual service, require virtual details
        if self.service_type in ['virtual', 'both']:
            if not (self.online_booking_url or self.phone or self.email):
                raise ValidationError(
                    "Contact method required for virtual services"
                )

    def get_absolute_url(self):
        """Public URL for this practice page"""
        return f"/pages/{self.slug}"

    def is_open_now(self):
        """Check if practice is currently open (for in-store)"""
        if self.service_type == 'virtual':
            return False

        from datetime import datetime
        now = datetime.now()
        day_name = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')

        day_hours = self.opening_hours.get(day_name, {})
        if day_hours.get('closed', False):
            return False

        open_time = day_hours.get('open', '')
        close_time = day_hours.get('close', '')

        if not (open_time and close_time):
            return False

        return open_time <= current_time <= close_time

    def increment_view_count(self):
        """Increment page view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_nomination_count(self):
        """Increment nomination counter"""
        self.nomination_count += 1
        self.save(update_fields=['nomination_count'])


class PhysicalLocation(TimestampedModel):
    """
    Physical location for a practice page (for practices with multiple locations).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    practice_page = models.ForeignKey(
        ProfessionalPracticePage,
        on_delete=models.CASCADE,
        related_name='locations'
    )

    name = models.CharField(
        max_length=200,
        help_text="Location name (e.g., 'Main Branch', 'Ikeja Office')"
    )
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    opening_hours = models.JSONField(default=dict, blank=True)

    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the main location?"
    )

    class Meta:
        db_table = 'physical_locations'
        verbose_name = 'Physical Location'
        verbose_name_plural = 'Physical Locations'
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.practice_page.practice_name} - {self.name}"


class VirtualServiceOffering(TimestampedModel):
    """
    Virtual service offerings for a practice page.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    practice_page = models.ForeignKey(
        ProfessionalPracticePage,
        on_delete=models.CASCADE,
        related_name='virtual_services'
    )

    service_name = models.CharField(
        max_length=200,
        help_text="Name of virtual service (e.g., 'Online Consultation')"
    )
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(
        help_text="Typical consultation duration"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in Naira"
    )

    # Availability Schedule (JSONField)
    availability_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Weekly availability slots"
    )

    booking_url = models.URLField(
        blank=True,
        help_text="Direct booking link for this service"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether service is currently offered"
    )

    class Meta:
        db_table = 'virtual_service_offerings'
        verbose_name = 'Virtual Service Offering'
        verbose_name_plural = 'Virtual Service Offerings'
        ordering = ['service_name']

    def __str__(self):
        return f"{self.practice_page.practice_name} - {self.service_name}"
