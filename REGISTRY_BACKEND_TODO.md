# Professional Registry Backend - TODO

**Date**: November 5, 2025
**Status**: ⚠️ FRONTEND READY, BACKEND ENDPOINTS MISSING

---

## Current Situation

### ✅ What's Complete

1. **RBAC System (Phase 1)** - DONE
   - Role model with granular permissions
   - User management API endpoints (`/registry/admin/users/`)
   - Permission checks
   - Platform Admin user created

2. **Frontend Auth (Phase 2)** - DONE
   - useAuth hook with role/permission support
   - registryService for API calls
   - Profile endpoint returning registry_role ✅

3. **Admin UI Pages (Phase 4)** - DONE
   - ApplicationsList.jsx (✅ Fixed to handle missing backend)
   - ApplicationDetail.jsx
   - UserManagement.jsx
   - Sidebar navigation added

### ❌ What's Missing

**Phase 3: Backend Registry API Endpoints**

The frontend is calling these endpoints, but they don't exist yet:

```
/api/registry/admin/applications/          - List professional applications
/api/registry/admin/applications/{id}/     - Application detail
/api/registry/admin/applications/{id}/start-review/
/api/registry/admin/applications/{id}/approve/
/api/registry/admin/applications/{id}/reject/
/api/registry/admin/applications/{id}/request-documents/
/api/registry/admin/registry/              - List registry entries
/api/registry/admin/registry/{license}/suspend/
/api/registry/admin/registry/{license}/reactivate/
/api/registry/admin/registry/{license}/revoke/
```

---

## What Needs to Be Built

### 1. Database Models

**File**: `api/models/professional_registration.py`

```python
from django.db import models
import uuid

class ProfessionalApplication(models.Model):
    """Professional registration application"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PROFESSIONAL_TYPES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('pharmacist', 'Pharmacist'),
        ('lab_technician', 'Lab Technician'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    application_reference = models.CharField(max_length=20, unique=True)

    # Applicant info
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Professional details
    professional_type = models.CharField(max_length=50, choices=PROFESSIONAL_TYPES)
    regulatory_body = models.CharField(max_length=200)
    regulatory_body_registration_number = models.CharField(max_length=100)

    # Qualification
    qualification = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    graduation_year = models.IntegerField()

    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RegistryEntry(models.Model):
    """PHB Professional Registry"""
    LICENSE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    license_number = models.CharField(max_length=20, unique=True)  # PHB-DOC-12345

    # Link to application
    application = models.OneToOneField(ProfessionalApplication, on_delete=models.PROTECT)

    # Professional info
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    professional_type = models.CharField(max_length=50)

    # License details
    license_status = models.CharField(max_length=20, choices=LICENSE_STATUS_CHOICES)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Public profile
    public_email = models.EmailField(blank=True)
    public_phone = models.CharField(max_length=20, blank=True)
    biography = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. API Views

**File**: `api/views/registry_admin_views.py`

```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.permissions import RegistryPermission
from api.models.professional_registration import ProfessionalApplication, RegistryEntry

class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated, RegistryPermission]
    required_permission = 'view_applications'

    def get(self, request):
        """List all professional applications"""
        applications = ProfessionalApplication.objects.all()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)

        professional_type = request.query_params.get('professional_type')
        if professional_type:
            applications = applications.filter(professional_type=professional_type)

        search = request.query_params.get('search')
        if search:
            applications = applications.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(application_reference__icontains=search)
            )

        # Serialize
        data = [{
            'id': str(app.id),
            'application_reference': app.application_reference,
            'first_name': app.first_name,
            'last_name': app.last_name,
            'professional_type': app.professional_type,
            'regulatory_body_registration_number': app.regulatory_body_registration_number,
            'status': app.status,
            'submitted_at': app.submitted_at,
            'created_at': app.created_at,
        } for app in applications]

        return Response(data)


class ApplicationApproveView(APIView):
    permission_classes = [IsAuthenticated, RegistryPermission]
    required_permission = 'approve_applications'

    def post(self, request, application_id):
        """Approve application and issue PHB license"""
        application = ProfessionalApplication.objects.get(id=application_id)

        if application.status != 'under_review':
            return Response(
                {'error': 'Only applications under review can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate license number
        license_number = f"PHB-{application.professional_type[:3].upper()}-{str(uuid.uuid4())[:8].upper()}"

        # Create registry entry
        registry_entry = RegistryEntry.objects.create(
            license_number=license_number,
            application=application,
            user=application.user,
            professional_type=application.professional_type,
            license_status='active',
            expires_at=timezone.now() + timedelta(days=365),
            public_email=request.data.get('public_email', ''),
            public_phone=request.data.get('public_phone', ''),
            biography=request.data.get('biography', ''),
        )

        # Update application
        application.status = 'approved'
        application.reviewed_by = request.user
        application.review_notes = request.data.get('review_notes', '')
        application.save()

        return Response({
            'message': 'Application approved',
            'license_number': license_number,
            'registry_entry_id': str(registry_entry.id),
        })
```

### 3. URL Configuration

**File**: `api/urls.py`

Add to urlpatterns:

```python
# Professional Registry Admin
path('registry/admin/applications/', ApplicationListView.as_view(), name='registry-applications-list'),
path('registry/admin/applications/<uuid:application_id>/', ApplicationDetailView.as_view(), name='registry-application-detail'),
path('registry/admin/applications/<uuid:application_id>/start-review/', ApplicationStartReviewView.as_view(), name='registry-application-start-review'),
path('registry/admin/applications/<uuid:application_id>/approve/', ApplicationApproveView.as_view(), name='registry-application-approve'),
path('registry/admin/applications/<uuid:application_id>/reject/', ApplicationRejectView.as_view(), name='registry-application-reject'),
```

### 4. Permissions

**File**: `api/permissions.py`

```python
from rest_framework.permissions import BasePermission

class RegistryPermission(BasePermission):
    """Check if user has required registry permission"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Superusers always have access
        if request.user.is_superuser:
            return True

        # Check if view requires specific permission
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        # Check user's registry_role permissions
        if request.user.registry_role:
            return required_permission in request.user.registry_role.permissions

        return False
```

---

## Steps to Implement

### Step 1: Create Models
```bash
cd /Users/new/Newphb/basebackend

# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate
```

### Step 2: Create API Views
- Create `api/views/registry_admin_views.py`
- Implement all view classes

### Step 3: Add URL Routes
- Update `api/urls.py` with registry endpoints

### Step 4: Create Permissions
- Update `api/permissions.py` with RegistryPermission

### Step 5: Test
```bash
# Start server
python manage.py runserver

# Test endpoints
curl -H "Authorization: Bearer {TOKEN}" http://localhost:8000/api/registry/admin/applications/
```

---

## Frontend is Ready!

Once the backend endpoints are created, the frontend will automatically work because:

1. ✅ ApplicationsList.jsx handles empty arrays gracefully
2. ✅ Error handling shows helpful messages
3. ✅ RBAC permission checks are in place
4. ✅ API service is configured correctly
5. ✅ Sidebar navigation is added

**Just implement the backend, and the system will come alive!**

---

## Quick Test After Implementation

1. **Login** as platformadmin@phb.com
2. **Navigate** to Professional Registry → Applications
3. **See** empty list with message "No applications to review"
4. **Create** test application via Django admin or API
5. **Refresh** Applications page
6. **Verify** application appears in list
7. **Click** "View" to see application detail
8. **Test** approve/reject workflow

---

## Summary

**Current Status**:
- Frontend: ✅ 100% Complete
- Backend RBAC: ✅ 100% Complete
- Backend Registry API: ❌ 0% Complete

**Estimated Time**: 2-3 hours to implement all backend endpoints

**Priority**: High - Frontend is complete and waiting for backend
