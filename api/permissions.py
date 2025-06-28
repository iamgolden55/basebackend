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


class IsHospitalAdmin(permissions.BasePermission):
    """
    Permission class to check if user is a hospital administrator.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'hospital_admin'
        )

class IsHospitalAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow hospital admins full access and others read-only.
    """
    def has_permission(self, request, view):
        # Read permissions for authenticated medical staff
        if request.method in permissions.SAFE_METHODS:
            return bool(
                request.user and
                request.user.is_authenticated and
                request.user.role in ['doctor', 'nurse', 'pharmacist', 'lab_technician', 
                                    'physician_assistant', 'medical_secretary', 'hospital_admin']
            )
        
        # Write permissions only for hospital admins
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'hospital_admin'
        )

class CanAccessGuideline(permissions.BasePermission):
    """
    Permission class for accessing clinical guidelines based on user role and organization.
    """
    def has_permission(self, request, view):
        # Must be authenticated medical staff or hospital admin
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['doctor', 'nurse', 'pharmacist', 'lab_technician',
                                'physician_assistant', 'medical_secretary', 'hospital_admin',
                                'radiologist_tech', 'paramedic', 'emt', 'midwife']
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Hospital admin can access their organization's guidelines
        if user.role == 'hospital_admin':
            try:
                hospital_admin = user.hospital_admin_profile
                return obj.organization == hospital_admin.hospital
            except:
                return False
        
        # Medical staff can access published guidelines from hospitals they're registered with
        if user.role in ['doctor', 'nurse', 'pharmacist', 'lab_technician']:
            # Check if user is registered with the guideline's organization
            try:
                # For doctors, check if they work at the hospital
                if hasattr(user, 'doctor_profile'):
                    return user.doctor_profile.hospital == obj.organization
                
                # For other staff, check hospital registrations
                user_hospitals = user.hospital_registrations.filter(
                    status='approved'
                ).values_list('hospital', flat=True)
                
                return (obj.organization.id in user_hospitals and 
                        obj.is_published and 
                        obj.is_active and
                        obj.approval_status == 'approved')
            except:
                return False
        
        return False

class IsGuidelineOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class for guideline ownership - only creator or hospital admin can modify.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authorized users (handled by CanAccessGuideline)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for guideline creator or hospital admin of the same organization
        user = request.user
        
        # Creator can always edit their own guidelines
        if obj.created_by == user:
            return True
        
        # Hospital admin of the same organization can edit
        if user.role == 'hospital_admin':
            try:
                hospital_admin = user.hospital_admin_profile
                return obj.organization == hospital_admin.hospital
            except:
                return False
        
        return False