# api/models/signals.py

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.mail import send_mail
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from datetime import date, timedelta
import logging
from api.models import MedicalRecord

logger = logging.getLogger(__name__)

# User and Medical Record Signals
@receiver(post_save, sender='api.CustomUser')
def create_medical_record(sender, instance, created, **kwargs):
    """Creates medical record for new users"""
    if created:
        try:
            MedicalRecord.objects.create(hpn=instance.hpn, user=instance)
            logger.info(f"Medical record created for user {instance.hpn}")
        except Exception as e:
            logger.error(f"Failed to create medical record for {instance.hpn}: {str(e)}")

@receiver(pre_delete, sender='api.CustomUser')
def handle_related_deletions(sender, instance, **kwargs):
    """Handles cleanup when a user is deleted"""
    try:
        with transaction.atomic():
            if hasattr(instance, 'medical_record'):
                instance.medical_record.anonymize_record()
                logger.info(f"Medical record anonymized for {instance.hpn}")

            OutstandingToken.objects.filter(user=instance).delete()
    except Exception as e:
        logger.error(f"Error during user deletion cleanup: {str(e)}")

# Staff Transfer Signal
@receiver(post_save, sender='api.StaffTransfer')
def handle_staff_transfer(sender, instance, created, **kwargs):
    """Updates department counts after staff transfer"""
    if instance.status == 'completed':
        try:
            with transaction.atomic():
                if instance.from_department:
                    instance.from_department.update_staff_count()
                if instance.to_department:
                    instance.to_department.update_staff_count()
                logger.info(f"Staff transfer completed for {instance.staff_member}")
        except Exception as e:
            logger.error(f"Error updating department counts: {str(e)}")

# Doctor License Signal
@receiver(post_save, sender='api.Doctor')
def check_license_expiry(sender, instance, **kwargs):
    """Monitors doctor license expiration"""
    if instance.license_expiry_date:
        days_until_expiry = (instance.license_expiry_date - date.today()).days
        
        if days_until_expiry <= 30:
            try:
                # Send email notification
                send_mail(
                    subject=f"License Expiry Warning - Dr. {instance.user.get_full_name()}",
                    message=f"Medical license expires in {days_until_expiry} days",
                    from_email="no-reply@yourhospital.com",
                    recipient_list=[instance.user.email, instance.hospital.administrator.email],
                    fail_silently=True
                )
                logger.warning(f"License expiring soon for Dr. {instance.user.get_full_name()}")
            except Exception as e:
                logger.error(f"Failed to send license expiry notification: {str(e)}")

# Department Capacity Signal
@receiver(post_save, sender='api.Department')
def monitor_bed_capacity(sender, instance, **kwargs):
    """Monitors department bed capacity"""
    try:
        occupancy_rate = (instance.occupied_beds / instance.total_beds * 100 
                         if instance.total_beds > 0 else 0)
        
        if occupancy_rate >= 90:
            # Send email alert
            send_mail(
                subject=f"High Capacity Alert - {instance.name}",
                message=f"Department is at {occupancy_rate:.1f}% capacity",
                from_email="no-reply@yourhospital.com",
                recipient_list=[instance.hospital.administrator.email],
                fail_silently=True
            )
            logger.warning(f"Department {instance.name} at {occupancy_rate:.1f}% capacity")
    except Exception as e:
        logger.error(f"Error monitoring bed capacity: {str(e)}")