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
    MedicalRecord
)

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