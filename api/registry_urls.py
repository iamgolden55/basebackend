"""
Professional Registry URLs

Completely separate URL namespace for PHB National Professional Registry.
Nigerian healthcare professional licensing and credentialing system.

MICROSERVICE DESIGN:
This URL configuration is intentionally isolated to make it easy to extract
the registry system into a separate microservice in the future.

All endpoints are under /api/registry/* namespace.
"""

from django.urls import path
from api.views.professional_registration_views import (
    # Public application endpoint (no authentication)
    submit_new_professional_application,

    # Authenticated application submission (for existing users)
    submit_authenticated_professional_application,

    # Professional application endpoints
    professional_applications_list_create,
    professional_application_detail,
    submit_professional_application,

    # Document upload endpoints
    application_documents_list_create,
    application_document_detail,
    get_required_documents,

    # Reference data endpoints only
    get_nigerian_states,
    get_professional_types,
    get_specializations,
)

# Import new secure search views
from api.views.professional_search_views import (
    search_professionals,
    verify_license,
    search_stats,
    get_application_status,
    get_my_professional_info,
)

from api.views.admin_application_review_views import (
    # Admin application management
    admin_list_applications,
    admin_application_detail,
    admin_start_review,
    admin_verify_document,
    admin_reject_document,
    admin_request_clarification,
    admin_request_additional_documents,
    admin_approve_application,
    admin_reject_application,

    # Admin registry management
    admin_list_registry,
    admin_suspend_license,
    admin_reactivate_license,
    admin_revoke_license,
    admin_add_disciplinary_record,
)

# Import user management views for RBAC
from api.views.admin import user_management_views


app_name = 'registry'

urlpatterns = [
    # =====================================================================
    # PUBLIC ENDPOINTS (No authentication required)
    # =====================================================================

    # Public application submission - allows new professionals to apply without login
    path('public/applications/', submit_new_professional_application, name='submit_new_application'),

    # Public registry search - patients and hospitals can verify professionals
    # NEW: Secure search endpoints with rate limiting and SQL injection protection
    path('search/', search_professionals, name='search_registry'),
    path('verify/<str:license_number>/', verify_license, name='verify_license'),
    path('stats/', search_stats, name='registry_statistics'),
    path('application-status/<str:application_id>/', get_application_status, name='application_status'),

    # Reference data endpoints
    path('states/', get_nigerian_states, name='nigerian_states'),
    path('professional-types/', get_professional_types, name='professional_types'),
    path('specializations/', get_specializations, name='specializations'),

    # =====================================================================
    # PROFESSIONAL APPLICATION ENDPOINTS (Authenticated users)
    # =====================================================================

    # Get current user's professional information (for role-based navigation)
    path('my-info/', get_my_professional_info, name='my_professional_info'),

    # Authenticated application submission - for existing PHB users
    path('applications/submit/', submit_authenticated_professional_application, name='submit_authenticated_application'),

    # Application management
    path('applications/', professional_applications_list_create, name='applications_list_create'),
    path('applications/<uuid:application_id>/', professional_application_detail, name='application_detail'),
    path('applications/<uuid:application_id>/submit/', submit_professional_application, name='submit_application'),

    # Document uploads
    path('applications/<uuid:application_id>/documents/', application_documents_list_create, name='application_documents'),
    path('applications/<uuid:application_id>/documents/<uuid:document_id>/', application_document_detail, name='application_document_detail'),
    path('required-documents/', get_required_documents, name='required_documents'),

    # =====================================================================
    # ADMIN ENDPOINTS (Admin users only)
    # =====================================================================

    # Application review
    path('admin/applications/', admin_list_applications, name='admin_list_applications'),
    path('admin/applications/<uuid:application_id>/', admin_application_detail, name='admin_application_detail'),
    path('admin/applications/<uuid:application_id>/start-review/', admin_start_review, name='admin_start_review'),
    path('admin/applications/<uuid:application_id>/approve/', admin_approve_application, name='admin_approve_application'),
    path('admin/applications/<uuid:application_id>/reject/', admin_reject_application, name='admin_reject_application'),
    path('admin/applications/<uuid:application_id>/request-documents/', admin_request_additional_documents, name='admin_request_documents'),

    # Document verification
    path('admin/applications/<uuid:application_id>/documents/<uuid:document_id>/verify/', admin_verify_document, name='admin_verify_document'),
    path('admin/applications/<uuid:application_id>/documents/<uuid:document_id>/reject/', admin_reject_document, name='admin_reject_document'),
    path('admin/applications/<uuid:application_id>/documents/<uuid:document_id>/clarify/', admin_request_clarification, name='admin_request_clarification'),

    # Registry management
    path('admin/registry/', admin_list_registry, name='admin_list_registry'),
    path('admin/registry/<str:license_number>/suspend/', admin_suspend_license, name='admin_suspend_license'),
    path('admin/registry/<str:license_number>/reactivate/', admin_reactivate_license, name='admin_reactivate_license'),
    path('admin/registry/<str:license_number>/revoke/', admin_revoke_license, name='admin_revoke_license'),
    path('admin/registry/<str:license_number>/disciplinary/', admin_add_disciplinary_record, name='admin_add_disciplinary'),

    # =====================================================================
    # ADMIN USER MANAGEMENT (Platform Admin only - RBAC)
    # =====================================================================
    path('admin/users/', user_management_views.list_admin_users, name='admin_list_users'),
    path('admin/users/create/', user_management_views.create_admin_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/role/', user_management_views.update_user_role, name='admin_update_user_role'),
    path('admin/users/<int:user_id>/deactivate/', user_management_views.deactivate_user, name='admin_deactivate_user'),
    path('admin/users/<int:user_id>/reactivate/', user_management_views.reactivate_user, name='admin_reactivate_user'),
    path('admin/roles/', user_management_views.list_roles, name='admin_list_roles'),
]
