# api/models/medical/staff_transfer.py

from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date, datetime

class StaffTransfer(models.Model):
    """
    Model to handle all aspects of staff transfers between hospitals and departments
    """
    # Transfer Status Options
    class Status:
        PENDING = 'pending'
        APPROVED = 'approved'
        REJECTED = 'rejected'
        COMPLETED = 'completed'
        CANCELLED = 'cancelled'
        
        CHOICES = [
            (PENDING, 'Pending Approval'),
            (APPROVED, 'Approved'),
            (REJECTED, 'Rejected'),
            (COMPLETED, 'Transfer Completed'),
            (CANCELLED, 'Transfer Cancelled')
        ]

    # Basic Transfer Information
    staff_member = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='transfers'
    )
    from_hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.CASCADE,
        related_name='transfers_out'
    )
    to_hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.CASCADE,
        related_name='transfers_in'
    )
    from_department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='transfers_out',
        null=True
    )
    to_department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='transfers_in',
        null=True
    )

    # Timing Information
    request_date = models.DateTimeField(auto_now_add=True)
    transfer_date = models.DateField()  # Planned transfer date
    effective_date = models.DateField()  # When transfer becomes effective
    completion_date = models.DateTimeField(null=True, blank=True)

    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.CHOICES,
        default=Status.PENDING
    )
    
    # Approval Chain
    requested_by = models.ForeignKey(
        'HospitalAdmin',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_transfers'
    )
    approved_by_source = models.ForeignKey(
        'HospitalAdmin',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_outgoing_transfers'
    )
    approved_by_destination = models.ForeignKey(
        'HospitalAdmin',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_incoming_transfers'
    )

    # Documentation
    reason = models.TextField(
        help_text="Detailed reason for the transfer request"
    )
    additional_notes = models.TextField(
        blank=True,
        help_text="Any additional information about the transfer"
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason if transfer is rejected"
    )

    # Transfer Type
    TRANSFER_TYPES = [
        ('permanent', 'Permanent Transfer'),
        ('temporary', 'Temporary Transfer'),
        ('rotation', 'Rotation Program'),
        ('emergency', 'Emergency Transfer')
    ]
    transfer_type = models.CharField(
        max_length=20,
        choices=TRANSFER_TYPES,
        default='permanent'
    )
    
    # For temporary transfers
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for temporary transfers"
    )

    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['transfer_date']),
            models.Index(fields=['staff_member']),
        ]

    def __str__(self):
        return f"Transfer: {self.staff_member.full_name} - {self.from_hospital} to {self.to_hospital}"

    def clean(self):
        """Validate transfer data"""
        if self.transfer_date < date.today():
            raise ValidationError("Transfer date cannot be in the past")
            
        if self.transfer_type == 'temporary' and not self.end_date:
            raise ValidationError("End date is required for temporary transfers")
            
        if self.end_date and self.end_date <= self.transfer_date:
            raise ValidationError("End date must be after transfer date")

    @transaction.atomic
    def approve_by_source_hospital(self, admin):
        """Approve transfer by source hospital"""
        if self.status != self.Status.PENDING:
            raise ValidationError("Can only approve pending transfers")
            
        if admin.hospital != self.from_hospital:
            raise ValidationError("Admin must belong to source hospital")
            
        self.approved_by_source = admin
        self.save()
        
        # Check if both approvals are complete
        self._check_complete_approval()

    @transaction.atomic
    def approve_by_destination_hospital(self, admin):
        """Approve transfer by destination hospital"""
        if self.status != self.Status.PENDING:
            raise ValidationError("Can only approve pending transfers")
            
        if admin.hospital != self.to_hospital:
            raise ValidationError("Admin must belong to destination hospital")
            
        self.approved_by_destination = admin
        self.save()
        
        # Check if both approvals are complete
        self._check_complete_approval()

    def _check_complete_approval(self):
        """Check if both hospitals have approved"""
        if self.approved_by_source and self.approved_by_destination:
            self.status = self.Status.APPROVED
            self.save()

    @transaction.atomic
    def complete_transfer(self):
        """Mark transfer as completed and update staff member's assignment"""
        if self.status != self.Status.APPROVED:
            raise ValidationError("Can only complete approved transfers")
            
        # Update staff member's hospital and department
        self.staff_member.primary_hospital = self.to_hospital
        if hasattr(self.staff_member, 'doctor_profile'):
            self.staff_member.doctor_profile.department = self.to_department
            self.staff_member.doctor_profile.save()
        self.staff_member.save()
        
        self.status = self.Status.COMPLETED
        self.completion_date = datetime.now()
        self.save()

    def reject_transfer(self, admin, reason):
        """Reject the transfer request"""
        if self.status != self.Status.PENDING:
            raise ValidationError("Can only reject pending transfers")
            
        if admin.hospital not in [self.from_hospital, self.to_hospital]:
            raise ValidationError("Admin must belong to source or destination hospital")
            
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.save()

    @transaction.atomic
    def cancel_transfer(self):
        """Cancel a pending or approved transfer"""
        if self.status not in [self.Status.PENDING, self.Status.APPROVED]:
            raise ValidationError("Can only cancel pending or approved transfers")
            
        self.status = self.Status.CANCELLED
        self.save()