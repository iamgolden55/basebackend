# Doctor Appointment Summary API Documentation

## Overview
This document describes the API for retrieving aggregated appointment data for doctor dashboards. The endpoint provides summary statistics and lists of appointments to enable a comprehensive view of a doctor's appointments.

## Endpoint
```
GET /api/doctor-appointments/summary/
```

### Authentication
This endpoint requires authentication and is only accessible to users with a doctor profile.

### Query Parameters
| Parameter  | Type   | Required | Description                                   |
|------------|--------|----------|-----------------------------------------------|
| start_date | string | No       | Start date for filtering (format: YYYY-MM-DD) |
| end_date   | string | No       | End date for filtering (format: YYYY-MM-DD)   |

## Response Format

### Success Response (200 OK)
```json
{
  "total_appointments": 150,
  "counts": {
    "by_status": {
      "pending": 45,
      "confirmed": 25,
      "cancelled": 10,
      "completed": 70,
      "no_show": 5,
      "in_progress": 2,
      "rescheduled": 3,
      "referred": 0,
      "rejected": 0
    },
    "by_type": {
      "first_visit": 30,
      "follow_up": 60,
      "consultation": 35,
      "procedure": 15,
      "test": 5,
      "vaccination": 3,
      "therapy": 2
    },
    "by_time_period": {
      "today": 8,
      "this_week": 25,
      "this_month": 50,
      "next_week": 15
    },
    "by_department": {
      "Cardiology": 45,
      "Neurology": 35,
      "General Medicine": 70
    }
  },
  "recent_appointments": [
    {
      "appointment_id": "APT-12345678",
      "patient": "John Smith",
      "doctor": "Dr. Jane Doe",
      "department": "Cardiology",
      "hospital": "General Hospital",
      "date": "2023-06-01T10:00:00Z",
      "status": "completed",
      "type": "follow_up",
      "priority": "normal",
      "payment_status": "completed",
      "is_insurance_based": false,
      "is_upcoming": false,
      "can_be_cancelled": false
    },
    // More appointments...
  ],
  "upcoming_appointments": [
    {
      "appointment_id": "APT-87654321",
      "patient": "Alice Johnson",
      "doctor": "Dr. Jane Doe",
      "department": "Cardiology",
      "hospital": "General Hospital",
      "date": "2023-06-15T14:30:00Z",
      "status": "confirmed",
      "type": "consultation",
      "priority": "normal",
      "payment_status": "pending",
      "is_insurance_based": true,
      "is_upcoming": true,
      "can_be_cancelled": true
    },
    // More appointments...
  ],
  "trends": {
    "by_month": [
      {"month": "January", "count": 30},
      {"month": "February", "count": 35},
      {"month": "March", "count": 28},
      {"month": "April", "count": 42},
      {"month": "May", "count": 38},
      {"month": "June", "count": 40}
    ]
  }
}
```

### Error Response (403 Forbidden)
If the user is not a doctor:
```json
{
  "status": "error",
  "message": "You are not registered as a doctor in the system"
}
```

## Usage Examples

### Fetching the complete appointment summary
```bash
curl -X GET \
  https://api.example.com/api/doctor-appointments/summary/ \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### Fetching appointment summary for a specific date range
```bash
curl -X GET \
  'https://api.example.com/api/doctor-appointments/summary/?start_date=2023-01-01&end_date=2023-06-30' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Notes
- This endpoint aggregates data from the doctor's appointments table.
- The response includes statistics as well as limited lists of recent and upcoming appointments.
- Performance considerations: For doctors with a large number of appointments, this endpoint may take longer to respond. Consider implementing caching strategies if performance becomes an issue. 