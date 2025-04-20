from django.db import models
from django.utils import timezone

class HospitalRegistration(models.Model):
    user = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.CASCADE,
        related_name='hospital_registrations'
    )
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    approved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'hospital']

    def approve_registration(self):
        self.status = 'approved'
        self.approved_date = timezone.now()
        
        if self.is_primary:
            # Update user's primary hospital
            self.user.hospital = self.hospital
            self.user.save()
            
        self.save() 