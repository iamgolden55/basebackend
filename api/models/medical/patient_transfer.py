# api/models/medical/patient_transfer.py

from django.db import models
from django.utils import timezone
from ..base import TimestampedModel

class PatientTransfer(TimestampedModel):
    """
    Model for tracking patient transfers between departments
    """
    admission = models.ForeignKey(
        'api.PatientAdmission',
        on_delete=models.CASCADE,
        related_name='transfers',
        help_text="The admission being transferred"
    )
    from_department = models.ForeignKey(
        'api.Department',
        on_delete=models.PROTECT,
        related_name='patient_transfers_out',
        help_text="Department transferring from"
    )
    to_department = models.ForeignKey(
        'api.Department',
        on_delete=models.PROTECT,
        related_name='patient_transfers_in',
        help_text="Department transferring to"
    )
    transfer_date = models.DateTimeField(
        default=timezone.now,
        help_text="When transfer occurred"
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for transfer"
    )
    
    class Meta:
        ordering = ['-transfer_date']
        
    def __str__(self):
        return f"Transfer: {self.admission.patient.get_full_name()} from {self.from_department.name} to {self.to_department.name}"
