from rest_framework import permissions

class IsMedicalStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )

class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            not request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        # Patients can only view their own records
        return obj.user == request.user