"""
Django Admin Interface for Drug Classification and Interaction Models

Provides comprehensive admin interface for managing:
- Drug classifications (NAFDAC, regulatory, risk flags)
- Drug interactions
- Bulk import/export functionality
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from api.models import DrugClassification, DrugInteraction


@admin.register(DrugClassification)
class DrugClassificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Drug Classification model
    """

    # =================================================================
    # LIST VIEW
    # =================================================================

    list_display = [
        'generic_name',
        'brand_names_display',
        'nafdac_schedule_badge',
        'controlled_flag',
        'high_risk_flag',
        'prescribing_authority',
        'therapeutic_class',
        'nafdac_approved_status',
        'active_status',
    ]

    list_filter = [
        'nafdac_schedule',
        'is_controlled',
        'is_high_risk',
        'requires_physician_only',
        'pharmacist_can_prescribe',
        'nafdac_approved',
        'therapeutic_class',
        'pharmacological_class',
        'pregnancy_category',
        'addiction_risk',
        'is_active',
        'discontinued',
        'who_essential_medicine',
    ]

    search_fields = [
        'generic_name',
        'brand_names',
        'search_keywords',
        'therapeutic_class',
        'pharmacological_class',
        'nafdac_registration_number',
    ]

    ordering = ['generic_name']

    list_per_page = 50

    actions = [
        'mark_as_controlled',
        'mark_as_high_risk',
        'mark_as_physician_only',
        'mark_as_pharmacist_prescribable',
        'mark_as_active',
        'mark_as_inactive',
        'export_to_csv',
    ]

    # =================================================================
    # FIELDSETS (Organized Edit Form)
    # =================================================================

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'generic_name',
                'brand_names',
                'active_ingredients',
                'is_active',
                'discontinued',
                'discontinued_date',
            )
        }),
        ('Nigerian Regulatory (NAFDAC)', {
            'fields': (
                'nafdac_approved',
                'nafdac_registration_number',
                'nafdac_schedule',
                'nafdac_schedule_date',
            ),
            'classes': ('wide',),
        }),
        ('International Classifications', {
            'fields': (
                'us_dea_schedule',
                'uk_controlled_drug_class',
                'who_essential_medicine',
            ),
            'classes': ('collapse',),
        }),
        ('Prescribing Requirements', {
            'fields': (
                'requires_special_prescription',
                'requires_physician_only',
                'pharmacist_can_prescribe',
                'maximum_days_supply',
                'requires_photo_id',
            ),
            'classes': ('wide',),
        }),
        ('Clinical Classification', {
            'fields': (
                'therapeutic_class',
                'pharmacological_class',
                'mechanism_of_action',
            ),
        }),
        ('Risk Flags', {
            'fields': (
                'is_controlled',
                'is_high_risk',
                'requires_monitoring',
                'monitoring_type',
                'monitoring_frequency_days',
                'addiction_risk',
                'abuse_potential',
            ),
            'classes': ('wide',),
        }),
        ('Age & Pregnancy Restrictions', {
            'fields': (
                'minimum_age',
                'maximum_age',
                'pregnancy_category',
                'breastfeeding_safe',
            ),
            'classes': ('collapse',),
        }),
        ('Contraindications & Warnings', {
            'fields': (
                'major_contraindications',
                'allergy_cross_reactions',
                'black_box_warning',
                'black_box_warning_text',
            ),
            'classes': ('collapse',),
        }),
        ('Drug Interactions', {
            'fields': (
                'major_drug_interactions',
                'food_interactions',
            ),
            'classes': ('collapse',),
        }),
        ('Search & Matching', {
            'fields': (
                'search_keywords',
                'generic_variations',
                'common_misspellings',
            ),
            'classes': ('collapse',),
            'description': 'Keywords and variations for matching user requests'
        }),
        ('Alternatives', {
            'fields': (
                'safer_alternatives',
                'cheaper_alternatives',
            ),
            'classes': ('collapse',),
        }),
        ('Administrative', {
            'fields': (
                'notes',
                'external_references',
                'last_verified_date',
                'verified_by',
            ),
            'classes': ('collapse',),
        }),
    )

    # =================================================================
    # READONLY FIELDS
    # =================================================================

    readonly_fields = ['created_at', 'updated_at']

    # =================================================================
    # CUSTOM DISPLAY METHODS
    # =================================================================

    @admin.display(description='Brand Names')
    def brand_names_display(self, obj):
        """Display first 2 brand names"""
        if obj.brand_names:
            brands = ', '.join(obj.brand_names[:2])
            if len(obj.brand_names) > 2:
                brands += f' (+{len(obj.brand_names) - 2} more)'
            return brands
        return '-'

    @admin.display(description='Schedule')
    def nafdac_schedule_badge(self, obj):
        """Display NAFDAC schedule with color badge"""
        color_map = {
            'unscheduled': 'green',
            'schedule_4': 'orange',
            'schedule_3': 'darkorange',
            'schedule_2': 'red',
            'schedule_1': 'darkred',
        }
        color = color_map.get(obj.nafdac_schedule, 'gray')
        label = obj.get_nafdac_schedule_display()

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            label
        )

    @admin.display(description='Controlled', boolean=True)
    def controlled_flag(self, obj):
        """Display controlled substance flag"""
        return obj.is_controlled

    @admin.display(description='High Risk', boolean=True)
    def high_risk_flag(self, obj):
        """Display high-risk flag"""
        return obj.is_high_risk

    @admin.display(description='Prescribing')
    def prescribing_authority(self, obj):
        """Display who can prescribe"""
        if obj.requires_physician_only:
            return format_html('<span style="color: red;">⚕️ Physician Only</span>')
        elif obj.pharmacist_can_prescribe:
            return format_html('<span style="color: green;">💊 Pharmacist</span>')
        else:
            return 'Any'

    @admin.display(description='NAFDAC', boolean=True)
    def nafdac_approved_status(self, obj):
        """Display NAFDAC approval status"""
        return obj.nafdac_approved

    @admin.display(description='Active', boolean=True)
    def active_status(self, obj):
        """Display active status"""
        return obj.is_active

    # =================================================================
    # CUSTOM ACTIONS
    # =================================================================

    @admin.action(description='Mark as Controlled Substance')
    def mark_as_controlled(self, request, queryset):
        """Mark selected drugs as controlled"""
        updated = queryset.update(is_controlled=True)
        self.message_user(request, f'{updated} drugs marked as controlled')

    @admin.action(description='Mark as High-Risk')
    def mark_as_high_risk(self, request, queryset):
        """Mark selected drugs as high-risk"""
        updated = queryset.update(is_high_risk=True)
        self.message_user(request, f'{updated} drugs marked as high-risk')

    @admin.action(description='Mark as Physician-Only')
    def mark_as_physician_only(self, request, queryset):
        """Mark selected drugs as requiring physician"""
        updated = queryset.update(
            requires_physician_only=True,
            pharmacist_can_prescribe=False
        )
        self.message_user(request, f'{updated} drugs marked as physician-only')

    @admin.action(description='Mark as Pharmacist Prescribable')
    def mark_as_pharmacist_prescribable(self, request, queryset):
        """Mark selected drugs as pharmacist prescribable"""
        updated = queryset.update(
            pharmacist_can_prescribe=True,
            requires_physician_only=False
        )
        self.message_user(request, f'{updated} drugs marked as pharmacist prescribable')

    @admin.action(description='Mark as Active')
    def mark_as_active(self, request, queryset):
        """Mark selected drugs as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} drugs marked as active')

    @admin.action(description='Mark as Inactive')
    def mark_as_inactive(self, request, queryset):
        """Mark selected drugs as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} drugs marked as inactive')

    @admin.action(description='Export to CSV')
    def export_to_csv(self, request, queryset):
        """Export selected drugs to CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="drugs_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Generic Name', 'Brand Names', 'NAFDAC Schedule',
            'Controlled', 'High Risk', 'Therapeutic Class',
            'Pharmacist Can Prescribe', 'NAFDAC Approved'
        ])

        for drug in queryset:
            writer.writerow([
                drug.generic_name,
                ', '.join(drug.brand_names) if drug.brand_names else '',
                drug.get_nafdac_schedule_display(),
                'Yes' if drug.is_controlled else 'No',
                'Yes' if drug.is_high_risk else 'No',
                drug.therapeutic_class or '',
                'Yes' if drug.pharmacist_can_prescribe else 'No',
                'Yes' if drug.nafdac_approved else 'No',
            ])

        return response


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    """
    Admin interface for Drug Interaction model
    """

    # =================================================================
    # LIST VIEW
    # =================================================================

    list_display = [
        'interaction_pair',
        'severity_badge',
        'clinical_effect_short',
        'management_short',
        'evidence_level_display',
        'active_status',
    ]

    list_filter = [
        'interaction_severity',
        'evidence_level',
        'monitoring_required',
        'onset_timing',
        'frequency_of_occurrence',
        'is_active',
    ]

    search_fields = [
        'drug_a__generic_name',
        'drug_b__generic_name',
        'clinical_effect',
        'management_strategy',
    ]

    ordering = ['-interaction_severity', 'drug_a__generic_name', 'drug_b__generic_name']

    list_per_page = 50

    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'mark_as_contraindicated',
        'export_to_csv',
    ]

    # =================================================================
    # FIELDSETS
    # =================================================================

    fieldsets = (
        ('Drug Pair', {
            'fields': (
                'drug_a',
                'drug_b',
            )
        }),
        ('Interaction Severity', {
            'fields': (
                'interaction_severity',
                'frequency_of_occurrence',
                'onset_timing',
            ),
            'classes': ('wide',),
        }),
        ('Clinical Information', {
            'fields': (
                'clinical_effect',
                'mechanism',
            ),
        }),
        ('Management', {
            'fields': (
                'management_strategy',
                'alternative_recommendation',
                'monitoring_required',
                'monitoring_parameters',
            ),
            'classes': ('wide',),
        }),
        ('Evidence & Documentation', {
            'fields': (
                'evidence_level',
                'references',
                'external_links',
            ),
            'classes': ('collapse',),
        }),
        ('Administrative', {
            'fields': (
                'is_active',
                'notes',
                'last_verified_date',
                'verified_by',
            ),
            'classes': ('collapse',),
        }),
    )

    # =================================================================
    # READONLY FIELDS
    # =================================================================

    readonly_fields = ['created_at', 'updated_at']

    # =================================================================
    # AUTOCOMPLETE FIELDS
    # =================================================================

    autocomplete_fields = ['drug_a', 'drug_b']

    # =================================================================
    # CUSTOM DISPLAY METHODS
    # =================================================================

    @admin.display(description='Interaction')
    def interaction_pair(self, obj):
        """Display drug pair"""
        return f"{obj.drug_a.generic_name} + {obj.drug_b.generic_name}"

    @admin.display(description='Severity')
    def severity_badge(self, obj):
        """Display severity with color badge"""
        color_map = {
            'mild': '#ffc107',  # yellow
            'moderate': '#ff9800',  # orange
            'severe': '#f44336',  # red
            'contraindicated': '#b71c1c',  # dark red
        }
        symbol_map = {
            'mild': '⚠️',
            'moderate': '⚠️⚠️',
            'severe': '🚨',
            'contraindicated': '❌',
        }

        color = color_map.get(obj.interaction_severity, '#999')
        symbol = symbol_map.get(obj.interaction_severity, '')
        label = obj.get_interaction_severity_display()

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{} {}</span>',
            color,
            symbol,
            label
        )

    @admin.display(description='Clinical Effect')
    def clinical_effect_short(self, obj):
        """Display shortened clinical effect"""
        if len(obj.clinical_effect) > 60:
            return obj.clinical_effect[:60] + '...'
        return obj.clinical_effect

    @admin.display(description='Management')
    def management_short(self, obj):
        """Display shortened management strategy"""
        if len(obj.management_strategy) > 50:
            return obj.management_strategy[:50] + '...'
        return obj.management_strategy

    @admin.display(description='Evidence')
    def evidence_level_display(self, obj):
        """Display evidence level"""
        icon_map = {
            'well_documented': '✓✓✓',
            'suspected': '✓✓',
            'theoretical': '✓',
        }
        icon = icon_map.get(obj.evidence_level, '')
        return f"{icon} {obj.get_evidence_level_display()}"

    @admin.display(description='Active', boolean=True)
    def active_status(self, obj):
        """Display active status"""
        return obj.is_active

    # =================================================================
    # CUSTOM ACTIONS
    # =================================================================

    @admin.action(description='Mark as Active')
    def mark_as_active(self, request, queryset):
        """Mark selected interactions as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} interactions marked as active')

    @admin.action(description='Mark as Inactive')
    def mark_as_inactive(self, request, queryset):
        """Mark selected interactions as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} interactions marked as inactive')

    @admin.action(description='Mark as Contraindicated')
    def mark_as_contraindicated(self, request, queryset):
        """Mark selected interactions as contraindicated"""
        updated = queryset.update(interaction_severity='contraindicated')
        self.message_user(request, f'{updated} interactions marked as contraindicated')

    @admin.action(description='Export to CSV')
    def export_to_csv(self, request, queryset):
        """Export selected interactions to CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="drug_interactions_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Drug A', 'Drug B', 'Severity',
            'Clinical Effect', 'Management Strategy',
            'Evidence Level', 'Active'
        ])

        for interaction in queryset:
            writer.writerow([
                interaction.drug_a.generic_name,
                interaction.drug_b.generic_name,
                interaction.get_interaction_severity_display(),
                interaction.clinical_effect,
                interaction.management_strategy,
                interaction.get_evidence_level_display(),
                'Yes' if interaction.is_active else 'No',
            ])

        return response


# Enable autocomplete for drug search in admin
DrugClassificationAdmin.search_fields = ['generic_name', 'brand_names']
