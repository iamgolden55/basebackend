from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .permissions import IsMedicalStaff
from .models import (
    Hospital, 
    GPPractice, 
    GeneralPractitioner, 
    CustomUser, 
    MedicalRecord,
    Department,
    Doctor,
    Appointment,
    PaymentTransaction,
    HospitalRegistration,
    AppointmentFee,
    SecureDocument,
    InAppNotification,
    AppointmentDocument,
    AppointmentNotification,
    AppointmentReminder,
    StaffTransfer,
    DepartmentEmergency,
    DocumentAccessLog,
    DocumentShare
)
# from .models.medical.hospital_auth import HospitalAdmin

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'hpn')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth', 
                                    'phone', 'gender', 'state', 'country', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                  'groups', 'user_permissions', 'has_completed_onboarding')}),  # Added here
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name')}
        ),
    )
    readonly_fields = ('hpn',)
    list_display = ('email', 'hpn', 'first_name', 'last_name', 'is_staff', 'country', 'has_completed_onboarding')  # Added here
    list_filter = ('gender', 'country', 'state', 'has_completed_onboarding')  # Added here too
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name', 'gender', 
                    'state', 'country', 'city', 'phone', 'nin')

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete_model(self, request, obj):
        try:
            if hasattr(obj, 'medical_record'):
                obj.medical_record.user = None
                obj.medical_record.is_anonymous = True
                obj.medical_record.save()
        except Exception as e:
            print(f"Error anonymizing medical record: {e}")
        super().delete_model(request, obj)

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    
    list_display = ['hpn', 'user', 'is_anonymous']
    list_filter = ['is_anonymous', 'is_high_risk']
    search_fields = ['hpn', 'user__email', 'user__first_name', 'user__last_name']
    
    def get_readonly_fields(self, request, obj=None):
        return ['hpn']

    def save_model(self, request, obj, form, change):
        if obj.is_anonymous:
            obj.anonymize_record()
        else:
            super().save_model(request, obj, form, change)

    actions = ['make_anonymous']
    
    def make_anonymous(self, request, queryset):
        for record in queryset:
            record.anonymize_record()
    make_anonymous.short_description = "Make selected records anonymous"

# Register other models with appropriate permissions
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['name', 'is_verified']
    search_fields = ['name', 'address']

@admin.register(GPPractice)
class GPPracticeAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['name', 'hospital']
    search_fields = ['name', 'address']

@admin.register(GeneralPractitioner)
class GeneralPractitionerAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['get_full_name', 'license_number', 'practice']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    get_full_name.short_description = 'Name'

admin.site.register(CustomUser, CustomUserAdmin)

# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['name', 'code', 'department_type', 'is_active', 'current_patient_count', 'bed_capacity']
    list_filter = ['hospital', 'is_active', 'department_type', 'is_24_hours']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['current_patient_count', 'occupied_beds', 'current_staff_count']

# Doctor Admin  
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['get_full_name', 'medical_license_number', 'department', 'specialization', 'years_of_experience', 'is_active']
    list_filter = ['department', 'specialization', 'is_active', 'hospital', 'status', 'available_for_appointments']
    search_fields = ['user__first_name', 'user__last_name', 'medical_license_number', 'specialization']
    readonly_fields = ['years_of_experience', 'is_verified']
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    get_full_name.short_description = 'Name'

# Appointment Admin
@admin.register(Appointment)
class AppointmentAdminConfig(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_date', 'status', 'appointment_type', 'priority']
    list_filter = ['status', 'appointment_type', 'priority', 'hospital', 'department', 'payment_status']
    search_fields = ['appointment_id', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name', 'chief_complaint']
    date_hierarchy = 'appointment_date'
    readonly_fields = ['appointment_id', 'completed_at', 'cancelled_at']
    ordering = ['-created_at']  # Show newest created appointments first in admin

# Payment Transaction Admin
@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['transaction_id', 'patient', 'amount_display', 'currency', 'payment_status', 'payment_method', 'created_at']
    list_filter = ['payment_status', 'currency', 'payment_method', 'payment_gateway', 'created_at']
    search_fields = ['transaction_id', 'patient__first_name', 'patient__last_name', 'gateway_transaction_id']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at', 'gateway_transaction_id']
    date_hierarchy = 'created_at'


# Hospital Admin Users - Temporarily disabled due to import issues
# @admin.register(HospitalAdmin)
# class HospitalAdminUserAdmin(admin.ModelAdmin):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsMedicalStaff]
#     list_display = ['name', 'email', 'hospital', 'position']
#     list_filter = ['hospital', 'position']
#     search_fields = ['name', 'email', 'position']
#     readonly_fields = ['password']

# Hospital Registration Admin
@admin.register(HospitalRegistration)
class HospitalRegistrationAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['user', 'hospital', 'created_at']
    list_filter = ['hospital', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'hospital__name']
    date_hierarchy = 'created_at'

# Appointment Fee Admin
@admin.register(AppointmentFee)
class AppointmentFeeAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]

# Secure Document Admin
@admin.register(SecureDocument)
class SecureDocumentAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['original_filename', 'user', 'file_type', 'is_encrypted', 'file_size', 'created_at']
    list_filter = ['file_type', 'is_encrypted', 'is_active', 'virus_scanned', 'created_at']
    search_fields = ['original_filename', 'user__first_name', 'user__last_name']
    readonly_fields = ['file_id', 'secure_filename', 'encryption_key_id', 'access_count', 'last_accessed']

# In-App Notification Admin
@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'


# Appointment Document Admin
@admin.register(AppointmentDocument)
class AppointmentDocumentAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['appointment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['appointment__appointment_id']

# Appointment Notification Admin
@admin.register(AppointmentNotification)
class AppointmentNotificationAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['appointment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['appointment__appointment_id']
    date_hierarchy = 'created_at'

# Appointment Reminder Admin
@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['appointment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['appointment__appointment_id']
    date_hierarchy = 'created_at'

# Staff Transfer Admin
@admin.register(StaffTransfer)
class StaffTransferAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]

# Department Emergency Admin
@admin.register(DepartmentEmergency)
class DepartmentEmergencyAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['department']
    list_filter = ['department']
    search_fields = ['department__name']

# Document Access Log Admin
@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['document', 'user']
    search_fields = ['document__original_filename', 'user__first_name', 'user__last_name']

# Document Share Admin
@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['document', 'shared_by']
    search_fields = ['document__original_filename', 'shared_by__first_name']