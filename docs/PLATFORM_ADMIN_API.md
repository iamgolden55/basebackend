# Platform Admin API Documentation

This document describes the API endpoints available for the Platform Admin Dashboard.

## Base URL
- **Development:** `http://127.0.0.1:8000/api`
- **Production:** `https://your-domain.com/api`

## Authentication

All platform admin endpoints require authentication with JWT tokens and admin privileges.

### Headers Required
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Authentication Flow
1. Login with admin credentials to get JWT tokens
2. Include `Bearer <access_token>` in all requests
3. Refresh token when needed

---

## Platform Statistics

### Get Platform Overview Stats
**Endpoint:** `GET /admin/platform/stats/`

**Description:** Get comprehensive platform statistics for dashboard overview.

**Response:**
```json
{
  "users": {
    "total": 1250,
    "verified": 1100,
    "new_this_month": 45,
    "growth_rate": 3.6
  },
  "hospitals": {
    "total": 25,
    "verified": 22,
    "pending_registrations": 3,
    "verification_rate": 88.0
  },
  "medical": {
    "total_records": 5400,
    "total_doctors": 180,
    "active_doctors": 165,
    "departments": 75,
    "doctor_utilization": 91.7
  },
  "appointments": {
    "total": 8900,
    "completed": 7200,
    "this_month": 320,
    "completion_rate": 80.9
  },
  "payments": {
    "total_transactions": 6500,
    "successful": 6100,
    "total_revenue": 245000.50,
    "success_rate": 93.8
  },
  "system": {
    "notifications_this_week": 45,
    "last_updated": "2025-01-15T10:30:00Z"
  }
}
```

---

## User Management

### Get Platform Users
**Endpoint:** `GET /admin/platform/users/`

**Query Parameters:**
- `search` (string): Search by email, name, or HPN
- `is_active` (boolean): Filter by active status
- `country` (string): Filter by country
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)

**Response:**
```json
{
  "users": [
    {
      "id": 123,
      "email": "user@example.com",
      "hpn": "HPN001234",
      "full_name": "John Doe",
      "is_active": true,
      "date_joined": "2024-01-15T10:30:00Z",
      "country": "Nigeria",
      "phone": "+234123456789",
      "has_completed_onboarding": true,
      "last_login": "2025-01-14T15:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1250,
    "pages": 63
  }
}
```

### Update User Status
**Endpoint:** `PATCH /admin/platform/users/`

**Request Body:**
```json
{
  "user_id": 123,
  "action": "activate" // or "deactivate"
}
```

**Response:**
```json
{
  "message": "User activated successfully",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "is_active": true
  }
}
```

---

## Hospital Management

### Get Platform Hospitals
**Endpoint:** `GET /admin/platform/hospitals/`

**Query Parameters:**
- `search` (string): Search by name, address, or email
- `is_verified` (boolean): Filter by verification status
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)

**Response:**
```json
{
  "hospitals": [
    {
      "id": 1,
      "name": "General Hospital Lagos",
      "email": "admin@generalhospital.com",
      "phone": "+234123456789",
      "address": "123 Lagos Island, Lagos",
      "is_verified": true,
      "created_at": "2024-01-01T00:00:00Z",
      "stats": {
        "departments": 12,
        "doctors": 45,
        "registrations": 1200
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 25,
    "pages": 2
  }
}
```

### Update Hospital Verification
**Endpoint:** `PATCH /admin/platform/hospitals/`

**Request Body:**
```json
{
  "hospital_id": 1,
  "action": "verify" // or "unverify"
}
```

**Response:**
```json
{
  "message": "Hospital verified successfully",
  "hospital": {
    "id": 1,
    "name": "General Hospital Lagos",
    "is_verified": true
  }
}
```

---

## Payment Analytics

### Get Payment Data
**Endpoint:** `GET /admin/platform/payments/`

**Query Parameters:**
- `start_date` (string): Start date in YYYY-MM-DD format
- `end_date` (string): End date in YYYY-MM-DD format

**Response:**
```json
{
  "stats": {
    "total_transactions": 6500,
    "successful": 6100,
    "failed": 300,
    "pending": 100,
    "total_revenue": 245000.50,
    "success_rate": 93.8
  },
  "recent_transactions": [
    {
      "id": 789,
      "transaction_id": "TXN_123456",
      "patient_email": "patient@example.com",
      "amount": 5000.0,
      "currency": "NGN",
      "payment_status": "completed",
      "payment_method": "card",
      "created_at": "2025-01-15T09:30:00Z",
      "appointment_id": "APT_789123"
    }
  ],
  "daily_revenue": [
    {
      "date": "2025-01-15",
      "revenue": 15000.0
    }
  ]
}
```

---

## Analytics Data

### Get Platform Analytics
**Endpoint:** `GET /admin/platform/analytics/`

**Description:** Get analytics data for charts and trends.

**Response:**
```json
{
  "user_growth": [
    {
      "month": "January 2025",
      "users": 45
    }
  ],
  "hospital_verification": [
    {
      "month": "January 2025",
      "total": 3,
      "verified": 2,
      "rate": 66.7
    }
  ],
  "appointment_trends": [
    {
      "date": "2025-01-15",
      "appointments": 25
    }
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### Authentication Error (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Permission Error (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Not Found Error (404)
```json
{
  "error": "User not found"
}
```

### Server Error (500)
```json
{
  "error": "Failed to fetch platform stats: Database connection error"
}
```

---

## Frontend Integration

### React Hooks Available

The following custom hooks are available for easy integration:

1. **usePlatformStats()** - Get platform statistics
2. **usePlatformUsers(filters)** - Manage users with filtering
3. **usePlatformHospitals(filters)** - Manage hospitals
4. **usePlatformPayments(filters)** - Payment analytics
5. **usePlatformAnalytics()** - Charts and trends data
6. **useDashboardData()** - Combined dashboard data

### Example Usage

```javascript
import { usePlatformStats } from '../hooks/usePlatformData';

function DashboardStats() {
  const { stats, loading, error } = usePlatformStats();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h3>Total Users: {stats.users.total}</h3>
      <h3>Total Revenue: ${stats.payments.total_revenue}</h3>
    </div>
  );
}
```

---

## Security Notes

1. **Admin Only:** All endpoints require `IsAdminUser` permission
2. **JWT Authentication:** Use Bearer tokens for all requests
3. **CORS Configured:** Frontend on port 3000 is allowed
4. **Rate Limiting:** Consider implementing rate limiting in production
5. **HTTPS Required:** All production requests must use HTTPS

---

## Development Setup

1. **Backend:** Run Django server on `http://127.0.0.1:8000`
2. **Frontend:** Run React app on `http://localhost:3000`
3. **CORS:** Already configured for local development
4. **Authentication:** Use Django admin user credentials for testing

---

## Production Deployment

1. Update `API_CONFIG.production.baseURL` in `src/config/api.js`
2. Set proper CORS origins in Django settings
3. Configure HTTPS and security headers
4. Set up proper authentication flow
5. Configure error monitoring and logging