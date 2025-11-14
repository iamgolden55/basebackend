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
    DocumentShare,
    # Women's Health Models
    WomensHealthProfile,
    MenstrualCycle,
    PregnancyRecord,
    FertilityTracking,
    HealthGoal,
    DailyHealthLog,
    HealthScreening,
    # Pharmacy Models
    Pharmacy,
    NominatedPharmacy,
    PharmacyAccessLog,
    # Professional Registry Models
    ProfessionalApplication,
    ApplicationDocument,
    PHBProfessionalRegistry,
    # Professional Practice Page Models
    ProfessionalPracticePage,
    PhysicalLocation,
    VirtualServiceOffering,
    # Admin Models
    AdminSignature,
)
# from .models.medical.hospital_auth import HospitalAdmin

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'hpn')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth', 
                                    'phone', 'gender', 'state', 'country', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                  'groups', 'user_permissions', 'has_completed_onboarding')}),
        ('Women\'s Health', {'fields': ('womens_health_verified', 'womens_health_verification_date')}),
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

# ======================== WOMEN'S HEALTH ADMIN ========================

# Women's Health Profile Admin
@admin.register(WomensHealthProfile)
class WomensHealthProfileAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['user', 'pregnancy_status', 'current_contraception', 'fertility_tracking_enabled', 'profile_completion_percentage']
    list_filter = ['pregnancy_status', 'current_contraception', 'fertility_tracking_enabled', 'pcos', 'endometriosis']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['profile_completion_percentage', 'current_cycle_day', 'estimated_ovulation_date', 'estimated_next_period']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Reproductive Health', {
            'fields': ('age_at_menarche', 'average_cycle_length', 'average_period_duration', 'last_menstrual_period')
        }),
        ('Pregnancy Status', {
            'fields': ('pregnancy_status', 'current_pregnancy_week', 'estimated_due_date')
        }),
        ('Pregnancy History', {
            'fields': ('total_pregnancies', 'live_births', 'miscarriages', 'abortions')
        }),
        ('Contraception', {
            'fields': ('current_contraception', 'contraception_start_date')
        }),
        ('Fertility Tracking', {
            'fields': ('fertility_tracking_enabled', 'temperature_tracking', 'cervical_mucus_tracking', 'ovulation_test_tracking')
        }),
        ('Health Conditions', {
            'fields': ('pcos', 'endometriosis', 'fibroids', 'thyroid_disorder', 'diabetes', 'gestational_diabetes_history', 'hypertension')
        }),
        ('Family History', {
            'fields': ('family_history_breast_cancer', 'family_history_ovarian_cancer', 'family_history_cervical_cancer', 'family_history_diabetes', 'family_history_heart_disease')
        }),
        ('Lifestyle', {
            'fields': ('exercise_frequency', 'stress_level', 'sleep_quality')
        }),
        ('Medical Care', {
            'fields': ('primary_gynecologist', 'last_pap_smear', 'last_mammogram', 'last_gynecological_exam')
        }),
        ('Calculated Fields', {
            'fields': ('profile_completion_percentage', 'current_cycle_day', 'estimated_ovulation_date', 'estimated_next_period'),
            'classes': ('collapse',)
        })
    )

# Menstrual Cycle Admin
@admin.register(MenstrualCycle)
class MenstrualCycleAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['womens_health_profile', 'cycle_start_date', 'cycle_length', 'period_length', 'flow_intensity', 'is_current_cycle', 'data_completeness_score']
    list_filter = ['flow_intensity', 'is_current_cycle', 'is_regular', 'conception_attempt', 'hormonal_contraception']
    search_fields = ['womens_health_profile__user__first_name', 'womens_health_profile__user__last_name']
    readonly_fields = ['cycle_day', 'days_until_ovulation', 'is_in_fertile_window', 'cycle_phase', 'data_completeness_score']
    date_hierarchy = 'cycle_start_date'
    ordering = ['-cycle_start_date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'cycle_start_date', 'cycle_end_date', 'period_end_date')
        }),
        ('Cycle Characteristics', {
            'fields': ('cycle_length', 'period_length', 'flow_intensity', 'is_regular', 'cycle_quality_score')
        }),
        ('Ovulation', {
            'fields': ('ovulation_date', 'ovulation_confirmed', 'ovulation_detection_method')
        }),
        ('Pregnancy Testing', {
            'fields': ('pregnancy_test_taken', 'pregnancy_test_result', 'pregnancy_test_date', 'conception_attempt')
        }),
        ('Medications', {
            'fields': ('medications_taken', 'supplements_taken', 'hormonal_contraception')
        }),
        ('Lifestyle Factors', {
            'fields': ('stress_level', 'exercise_frequency', 'travel_during_cycle', 'illness_during_cycle')
        }),
        ('Calculated Fields', {
            'fields': ('cycle_day', 'days_until_ovulation', 'is_in_fertile_window', 'cycle_phase', 'data_completeness_score'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_current_cycle', 'predicted_cycle')
        })
    )

# Pregnancy Record Admin
@admin.register(PregnancyRecord)
class PregnancyRecordAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['womens_health_profile', 'pregnancy_number', 'pregnancy_status', 'estimated_due_date', 'gestational_age_at_completion', 'is_current_pregnancy']
    list_filter = ['pregnancy_status', 'pregnancy_type', 'conception_method', 'risk_level', 'is_current_pregnancy']
    search_fields = ['womens_health_profile__user__first_name', 'womens_health_profile__user__last_name']
    readonly_fields = ['current_gestational_age', 'trimester', 'days_until_due_date', 'is_high_risk']
    date_hierarchy = 'pregnancy_start_date'
    ordering = ['-pregnancy_number']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'pregnancy_number', 'is_current_pregnancy')
        }),
        ('Pregnancy Timeline', {
            'fields': ('last_menstrual_period', 'estimated_due_date', 'conception_date', 'pregnancy_start_date')
        }),
        ('Pregnancy Details', {
            'fields': ('pregnancy_type', 'conception_method', 'pregnancy_status', 'completion_date', 'gestational_age_at_completion')
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'risk_factors')
        }),
        ('Prenatal Care', {
            'fields': ('first_prenatal_visit_date', 'first_prenatal_visit_week', 'total_prenatal_visits', 'adequate_prenatal_care')
        }),
        ('Healthcare Providers', {
            'fields': ('primary_obstetrician', 'hospital_for_delivery', 'midwife_care', 'doula_support')
        }),
        ('Complications', {
            'fields': ('pregnancy_complications', 'gestational_diabetes', 'preeclampsia', 'placenta_previa', 'preterm_labor_risk')
        }),
        ('Delivery Information', {
            'fields': ('delivery_type', 'delivery_location', 'labor_duration_hours', 'delivery_complications')
        }),
        ('Birth Outcomes', {
            'fields': ('birth_weight_grams', 'birth_length_cm', 'head_circumference_cm', 'apgar_1_minute', 'apgar_5_minute')
        }),
        ('Calculated Fields', {
            'fields': ('current_gestational_age', 'trimester', 'days_until_due_date', 'is_high_risk'),
            'classes': ('collapse',)
        })
    )

# Fertility Tracking Admin
@admin.register(FertilityTracking)
class FertilityTrackingAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['womens_health_profile', 'date', 'cycle_day', 'basal_body_temperature', 'cervical_mucus_type', 'ovulation_test_result', 'fertility_score', 'data_completeness_score']
    list_filter = ['cervical_mucus_type', 'ovulation_test_result', 'pregnancy_test_result', 'intercourse', 'trying_to_conceive']
    search_fields = ['womens_health_profile__user__first_name', 'womens_health_profile__user__last_name']
    readonly_fields = ['is_potential_ovulation_day', 'fertility_score', 'data_completeness_score']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'date', 'cycle_day')
        }),
        ('Basal Body Temperature', {
            'fields': ('basal_body_temperature', 'bbt_time_taken', 'bbt_method', 'bbt_disrupted', 'bbt_disruption_reason')
        }),
        ('Cervical Mucus', {
            'fields': ('cervical_mucus_type', 'cervical_mucus_amount', 'cervical_mucus_stretchy', 'cervical_mucus_notes')
        }),
        ('Cervical Position', {
            'fields': ('cervical_position_height', 'cervical_position_firmness', 'cervical_position_opening')
        }),
        ('Ovulation Tests', {
            'fields': ('ovulation_test_taken', 'ovulation_test_result', 'ovulation_test_time', 'ovulation_test_brand', 'lh_level')
        }),
        ('Pregnancy Tests', {
            'fields': ('pregnancy_test_taken', 'pregnancy_test_result', 'pregnancy_test_time', 'pregnancy_test_brand')
        }),
        ('Sexual Activity', {
            'fields': ('intercourse', 'protected_intercourse', 'intercourse_times', 'trying_to_conceive')
        }),
        ('Symptoms', {
            'fields': ('symptoms', 'ovulation_pain', 'ovulation_pain_side', 'breast_tenderness', 'spotting', 'spotting_color')
        }),
        ('Calculated Fields', {
            'fields': ('is_potential_ovulation_day', 'fertility_score', 'data_completeness_score'),
            'classes': ('collapse',)
        })
    )

# Health Goal Admin
@admin.register(HealthGoal)
class HealthGoalAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['title', 'womens_health_profile', 'category', 'status', 'priority', 'progress_percentage', 'current_streak', 'target_date']
    list_filter = ['category', 'status', 'priority', 'goal_type', 'is_template_based', 'recommended_by_professional']
    search_fields = ['title', 'womens_health_profile__user__first_name', 'womens_health_profile__user__last_name']
    readonly_fields = ['progress_percentage', 'current_streak', 'longest_streak', 'days_since_start', 'days_until_target', 'is_overdue']
    date_hierarchy = 'start_date'
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'title', 'description', 'category', 'goal_type')
        }),
        ('Target and Progress', {
            'fields': ('target_value', 'current_value', 'unit_of_measurement', 'target_frequency', 'frequency_period', 'current_frequency')
        }),
        ('Timeline', {
            'fields': ('start_date', 'target_date', 'completed_date', 'status', 'priority')
        }),
        ('Progress Tracking', {
            'fields': ('progress_percentage', 'current_streak', 'longest_streak', 'last_activity_date', 'total_updates')
        }),
        ('Reminders', {
            'fields': ('reminder_enabled', 'reminder_frequency', 'reminder_time')
        }),
        ('Motivation', {
            'fields': ('motivation_note', 'reward_for_completion', 'accountability_partner')
        }),
        ('Healthcare Professional', {
            'fields': ('recommended_by_professional', 'professional_name', 'professional_notes')
        }),
        ('Calculated Fields', {
            'fields': ('days_since_start', 'days_until_target', 'is_overdue'),
            'classes': ('collapse',)
        })
    )

# Daily Health Log Admin
@admin.register(DailyHealthLog)
class DailyHealthLogAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['womens_health_profile', 'date', 'mood', 'energy_level', 'exercise_performed', 'menstrual_flow', 'health_score', 'data_completeness_score']
    list_filter = ['mood', 'energy_level', 'exercise_performed', 'menstrual_flow', 'stress_level', 'sleep_quality']
    search_fields = ['womens_health_profile__user__first_name', 'womens_health_profile__user__last_name']
    readonly_fields = ['health_score', 'bmi', 'sleep_efficiency', 'data_completeness_score']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'date')
        }),
        ('Physical Health', {
            'fields': ('weight_kg', 'body_fat_percentage', 'muscle_mass_kg')
        }),
        ('Vital Signs', {
            'fields': ('systolic_bp', 'diastolic_bp', 'heart_rate_bpm', 'resting_heart_rate', 'body_temperature')
        }),
        ('Sleep', {
            'fields': ('sleep_bedtime', 'sleep_wake_time', 'sleep_duration_hours', 'sleep_quality', 'sleep_interrupted')
        }),
        ('Nutrition', {
            'fields': ('water_intake_liters', 'water_goal_met', 'meals_count', 'vegetables_servings', 'fruits_servings')
        }),
        ('Exercise', {
            'fields': ('exercise_performed', 'exercise_duration_minutes', 'exercise_intensity', 'steps_count', 'calories_burned')
        }),
        ('Mental Health', {
            'fields': ('mood', 'stress_level', 'anxiety_level', 'energy_level', 'emotional_wellbeing_score')
        }),
        ('Women\'s Health', {
            'fields': ('menstrual_flow', 'menstrual_cramps', 'cramp_severity', 'breast_tenderness', 'pms_symptoms')
        }),
        ('Medications', {
            'fields': ('medications_taken', 'supplements_taken', 'prenatal_vitamin', 'folic_acid', 'birth_control')
        }),
        ('Calculated Fields', {
            'fields': ('health_score', 'bmi', 'sleep_efficiency', 'data_completeness_score'),
            'classes': ('collapse',)
        })
    )

# Health Screening Admin
@admin.register(HealthScreening)
class HealthScreeningAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['womens_health_profile', 'screening_type', 'scheduled_date', 'completed_date', 'status', 'result_status', 'next_due_date']
    list_filter = ['screening_type', 'status', 'result_status', 'provider_type', 'follow_up_required', 'risk_assessment']
    search_fields = ['womens_health_profile__user__first_name', 'womens_health_profile__user__last_name', 'provider_name', 'clinic_hospital_name']
    readonly_fields = ['is_due_soon', 'days_until_due', 'days_since_last', 'age_at_screening']
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('womens_health_profile', 'screening_type', 'custom_screening_name')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'appointment_time', 'completed_date', 'next_due_date', 'status')
        }),
        ('Healthcare Provider', {
            'fields': ('provider_name', 'clinic_hospital_name', 'provider_type')
        }),
        ('Results', {
            'fields': ('result_status', 'result_details', 'result_values', 'abnormal_findings', 'recommendations')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_type', 'follow_up_date', 'follow_up_notes')
        }),
        ('Risk Assessment', {
            'fields': ('risk_assessment', 'risk_factors_identified')
        }),
        ('Frequency and Recurrence', {
            'fields': ('recommended_frequency_months', 'is_routine', 'reason_for_screening')
        }),
        ('Experience', {
            'fields': ('comfort_level', 'pain_level', 'patient_experience_notes')
        }),
        ('Reminders', {
            'fields': ('reminder_enabled', 'reminder_advance_days', 'last_reminder_sent')
        }),
        ('Calculated Fields', {
            'fields': ('is_due_soon', 'days_until_due', 'days_since_last', 'age_at_screening'),
            'classes': ('collapse',)
        })
    )

# Pharmacy Admin
@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    list_display = ['name', 'phb_pharmacy_code', 'city', 'postcode', 'phone', 'electronic_prescriptions_enabled', 'is_active', 'verified']
    list_filter = ['electronic_prescriptions_enabled', 'is_active', 'verified', 'city', 'state']
    search_fields = ['name', 'phb_pharmacy_code', 'city', 'postcode', 'phone', 'email']
    ordering = ['name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('phb_pharmacy_code', 'name', 'description', 'hospital')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Services', {
            'fields': ('electronic_prescriptions_enabled', 'opening_hours', 'services_offered')
        }),
        ('Status', {
            'fields': ('is_active', 'verified')
        })
    )

# Nominated Pharmacy Admin
@admin.register(NominatedPharmacy)
class NominatedPharmacyAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]
    list_display = ['user', 'pharmacy', 'nomination_type', 'is_current', 'nominated_at', 'ended_at']
    list_filter = ['is_current', 'nomination_type', 'nominated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'user__hpn', 'pharmacy__name', 'pharmacy__phb_pharmacy_code']
    date_hierarchy = 'nominated_at'
    ordering = ['-nominated_at']

    fieldsets = (
        ('Nomination Details', {
            'fields': ('user', 'pharmacy', 'nomination_type')
        }),
        ('Status', {
            'fields': ('is_current', 'nominated_at', 'ended_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


# Pharmacy Access Log Admin (Audit Trail)
@admin.register(PharmacyAccessLog)
class PharmacyAccessLogAdmin(admin.ModelAdmin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMedicalStaff]

    list_display = [
        'patient_hpn',
        'pharmacist_user',
        'pharmacy',
        'access_type',
        'prescription_count',
        'controlled_substance_count',
        'access_granted',
        'patient_verified',
        'access_time'
    ]

    list_filter = [
        'access_granted',
        'access_type',
        'verification_method',
        'patient_verified',
        'access_time'
    ]

    search_fields = [
        'patient_hpn',
        'pharmacist_user__email',
        'pharmacist_user__first_name',
        'pharmacist_user__last_name',
        'patient_user__email',
        'ip_address'
    ]

    date_hierarchy = 'access_time'
    ordering = ['-access_time']

    readonly_fields = [
        'access_time',
        'created_at',
        'updated_at',
        'prescriptions_accessed',
        'ip_address',
        'user_agent'
    ]

    fieldsets = (
        ('Patient Information', {
            'fields': (
                'patient_hpn',
                'patient_user'
            )
        }),
        ('Pharmacy & Pharmacist', {
            'fields': (
                'pharmacy',
                'pharmacist_user'
            )
        }),
        ('Access Details', {
            'fields': (
                'access_type',
                'access_time',
                'access_granted',
                'denial_reason'
            )
        }),
        ('Prescriptions Accessed', {
            'fields': (
                'prescriptions_accessed',
                'prescription_count',
                'controlled_substance_count'
            )
        }),
        ('Patient Verification', {
            'fields': (
                'patient_verified',
                'verification_method'
            )
        }),
        ('Technical Details', {
            'fields': (
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        """Prevent manual creation - logs are auto-generated"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion for audit compliance"""
        return False


# ======================== PROFESSIONAL REGISTRY ADMIN ========================

@admin.register(ProfessionalApplication)
class ProfessionalApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for Professional Registry Applications.
    Includes custom actions to reset stuck applications to draft status.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'application_reference',
        'user_email',
        'applicant_name',
        'professional_type',
        'status',
        'submitted_date',
        'document_count',
        'created_at'
    ]
    list_filter = [
        'status',
        'professional_type',
        'specialization',
        'home_registration_body',
        'created_at',
        'submitted_date'
    ]
    search_fields = [
        'application_reference',
        'user__email',
        'user__first_name',
        'user__last_name',
        'first_name',
        'last_name',
        'email',
        'phone',
        'home_registration_number',
        'phb_license_number'
    ]
    readonly_fields = [
        'id',
        'application_reference',
        'created_at',
        'updated_at',
        'submitted_date',
        'under_review_date',
        'decision_date'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Application Status', {
            'fields': ('id', 'application_reference', 'status', 'user')
        }),
        ('Personal Information', {
            'fields': ('title', 'first_name', 'middle_name', 'last_name', 'email', 'phone', 'alternate_phone')
        }),
        ('Professional Details', {
            'fields': ('professional_type', 'specialization', 'subspecialization', 'years_of_experience')
        }),
        ('Regulatory Information', {
            'fields': ('home_registration_body', 'home_registration_number', 'home_registration_date')
        }),
        ('PHB License', {
            'fields': ('phb_license_number',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_date', 'under_review_date', 'decision_date'),
            'classes': ('collapse',)
        })
    )

    actions = ['reset_to_draft', 'request_additional_documents']

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'User Email'

    def applicant_name(self, obj):
        """Display applicant full name"""
        return f"{obj.first_name} {obj.last_name}"
    applicant_name.short_description = 'Applicant Name'

    def document_count(self, obj):
        """Display number of documents uploaded"""
        return obj.documents.count()
    document_count.short_description = 'Documents'

    @admin.action(description='🔄 Reset selected applications to draft status (allows document uploads)')
    def reset_to_draft(self, request, queryset):
        """
        Reset applications to draft status to allow document uploads.
        This fixes applications that were auto-submitted before documents were uploaded.
        """
        # Only reset non-draft applications
        eligible = queryset.exclude(status='draft')
        count = eligible.update(
            status='draft',
            submitted_date=None,
            under_review_date=None
        )

        if count > 0:
            self.message_user(
                request,
                f'✅ Successfully reset {count} application(s) to draft status. Users can now upload documents.',
                level='SUCCESS'
            )
        else:
            self.message_user(
                request,
                '⚠️ No applications were reset. Selected applications may already be in draft status.',
                level='WARNING'
            )

    @admin.action(description='📎 Request additional documents from applicants')
    def request_additional_documents(self, request, queryset):
        """
        Change status to 'documents_requested' to allow additional document uploads.
        """
        # Only update submitted or under_review applications
        eligible = queryset.filter(status__in=['submitted', 'under_review'])
        count = eligible.update(status='documents_requested')

        if count > 0:
            self.message_user(
                request,
                f'✅ Successfully requested additional documents for {count} application(s). Users can now upload more documents.',
                level='SUCCESS'
            )
        else:
            self.message_user(
                request,
                '⚠️ No applications updated. Only submitted or under_review applications can have documents requested.',
                level='WARNING'
            )


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    """Admin interface for application documents."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'get_application_ref',
        'document_type',
        'original_filename',
        'verification_status',
        'created_at',
        'verified_date'
    ]
    list_filter = [
        'document_type',
        'verification_status',
        'created_at',
        'verified_date'
    ]
    search_fields = [
        'application__application_reference',
        'application__user__email',
        'original_filename',
        'document_type'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'verified_date',
        'verified_by'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_application_ref(self, obj):
        """Display application reference"""
        return obj.application.application_reference
    get_application_ref.short_description = 'Application'


@admin.register(PHBProfessionalRegistry)
class PHBProfessionalRegistryAdmin(admin.ModelAdmin):
    """Admin interface for approved professionals in the registry."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'phb_license_number',
        'get_full_name',
        'professional_type',
        'specialization',
        'license_status',
        'license_expiry_date',
        'is_searchable'
    ]
    list_filter = [
        'professional_type',
        'license_status',
        'specialization',
        'is_searchable',
        'license_issue_date'
    ]
    search_fields = [
        'phb_license_number',
        'first_name',
        'last_name',
        'home_registration_number'
    ]
    readonly_fields = [
        'id',
        'application',
        'license_issue_date',
        'created_at',
        'updated_at'
    ]
    date_hierarchy = 'license_issue_date'
    ordering = ['-license_issue_date']

    def get_full_name(self, obj):
        """Display professional's full name"""
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Name'


# ============================================================================
# Professional Practice Pages
# ============================================================================

@admin.register(ProfessionalPracticePage)
class ProfessionalPracticePageAdmin(admin.ModelAdmin):
    """Admin interface for professional practice pages."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'practice_name',
        'get_owner_name',
        'get_professional_type',
        'service_type',
        'city',
        'state',
        'is_published',
        'verification_status',
        'view_count',
        'nomination_count',
        'created_at'
    ]
    list_filter = [
        'service_type',
        'is_published',
        'verification_status',
        'state',
        'created_at'
    ]
    search_fields = [
        'practice_name',
        'slug',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
        'city',
        'state'
    ]
    readonly_fields = [
        'id',
        'owner',
        'linked_registry_entry',
        'slug',
        'view_count',
        'nomination_count',
        'verified_by',
        'verified_date',
        'created_at',
        'updated_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'owner', 'linked_registry_entry', 'practice_name', 'slug', 'tagline', 'about')
        }),
        ('Service Type', {
            'fields': ('service_type',)
        }),
        ('Physical Location', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country', 'latitude', 'longitude')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website', 'whatsapp_number')
        }),
        ('Opening Hours', {
            'fields': ('opening_hours',)
        }),
        ('Virtual Services', {
            'fields': ('virtual_consultation_hours', 'online_booking_url', 'video_platform')
        }),
        ('Services & Details', {
            'fields': ('services_offered', 'payment_methods', 'additional_certifications', 'languages_spoken')
        }),
        ('Publication & Verification', {
            'fields': ('is_published', 'verification_status', 'verification_notes', 'verified_by', 'verified_date')
        }),
        ('Statistics', {
            'fields': ('view_count', 'nomination_count')
        }),
        ('SEO', {
            'fields': ('meta_keywords',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_owner_name(self, obj):
        """Display owner's full name"""
        return obj.owner.get_full_name()
    get_owner_name.short_description = 'Owner'

    def get_professional_type(self, obj):
        """Display professional type"""
        return obj.linked_registry_entry.professional_type
    get_professional_type.short_description = 'Type'


@admin.register(PhysicalLocation)
class PhysicalLocationAdmin(admin.ModelAdmin):
    """Admin interface for physical locations."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'name',
        'get_practice_page',
        'city',
        'state',
        'is_primary',
        'created_at'
    ]
    list_filter = [
        'is_primary',
        'state',
        'created_at'
    ]
    search_fields = [
        'name',
        'practice_page__practice_name',
        'city',
        'state'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-is_primary', 'name']

    def get_practice_page(self, obj):
        """Display practice page name"""
        return obj.practice_page.practice_name
    get_practice_page.short_description = 'Practice Page'


@admin.register(VirtualServiceOffering)
class VirtualServiceOfferingAdmin(admin.ModelAdmin):
    """Admin interface for virtual service offerings."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    list_display = [
        'service_name',
        'get_practice_page',
        'duration_minutes',
        'price',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active',
        'created_at'
    ]
    search_fields = [
        'service_name',
        'practice_page__practice_name',
        'description'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['service_name']

    def get_practice_page(self, obj):
        """Display practice page name"""
        return obj.practice_page.practice_name
    get_practice_page.short_description = 'Practice Page'

@admin.register(AdminSignature)
class AdminSignatureAdmin(admin.ModelAdmin):
    """Admin interface for managing signature for hospital approval certificates."""
    list_display = ['name', 'is_active', 'signature_preview', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'signature_preview']
    fields = ['name', 'signature_image', 'signature_preview', 'is_active', 'created_at', 'updated_at']
    
    def signature_preview(self, obj):
        """Display a preview of the signature image."""
        if obj.signature_image:
            from django.utils.html import format_html
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 300px;" />',
                obj.signature_image.url
            )
        return "No signature uploaded"
    signature_preview.short_description = 'Signature Preview'
    
    def has_add_permission(self, request):
        """Allow adding if no active signature exists, or allow adding inactive ones."""
        return True
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure only one active signature."""
        if obj.is_active:
            # Deactivate all other signatures
            AdminSignature.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)
