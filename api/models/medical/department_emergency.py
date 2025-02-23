# api/models/medical/department_emergency.py
from django.db import models

class DepartmentEmergency(models.Model):
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    reason = models.TextField()
    required_staff = models.PositiveIntegerField()
    declared_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
