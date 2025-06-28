# Women's Health Agents API Documentation

## Overview

This document provides comprehensive API documentation for the Women's Health Agents system, including endpoint specifications, request/response formats, authentication requirements, and testing procedures.

## Base URL

```
Development: http://localhost:8000/api/agents/
Production: https://yourdomain.com/api/agents/
```

## Authentication

All agent endpoints require JWT authentication. Include the bearer token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints
- `POST /api/auth/login/` - Login to get JWT token
- `POST /api/auth/refresh/` - Refresh JWT token

## Common Response Format

All agent endpoints return responses in the following format:

```json
{
    "success": true|false,
    "data": {...},
    "agent": "AgentName",
    "operation": "operation_name",
    "error": "error_message"  // Only present if success is false
}
```

## Analytics Agent API

### Base Path: `/api/agents/analytics/`

The Analytics Agent provides advanced data analytics, predictive health insights, and AI-driven recommendations.

#### 1. Get Agent Status

```http
GET /api/agents/analytics/status/
```

**Headers:**
```http
Authorization: Bearer <token>
```

**Response:**
```json
{
    "name": "Analytics",
    "version": "1.0.0",
    "initialized": true,
    "services": {
        "cycle_analytics": {
            "service": "CycleAnalyticsService",
            "status": "active",
            "last_check": "2024-01-15T10:30:00Z"
        },
        "health_predictions": {
            "service": "HealthPredictionService",
            "status": "active",
            "last_check": "2024-01-15T10:30:00Z"
        },
        "recommendations": {
            "service": "RecommendationService",
            "status": "active",
            "last_check": "2024-01-15T10:30:00Z"
        }
    },
    "last_check": "2024-01-15T10:30:00Z"
}
```

#### 2. Analyze Cycle Irregularities

Detects menstrual cycle irregularities and provides analysis.

```http
POST /api/agents/analytics/cycle-irregularities/
```

**Request Body:**
```json
{
    "user_id": 1,          // Optional: defaults to authenticated user
    "months_back": 6       // Optional: defaults to 6 months
}
```

**Response (Sufficient Data):**
```json
{
    "success": true,
    "data": {
        "sufficient_data": true,
        "regularity_score": 85,
        "cycle_count": 6,
        "average_length": 28.5,
        "variability": 2.1,
        "irregularities": [
            {
                "type": "long_cycles",
                "severity": "moderate",
                "description": "2 cycles longer than 35 days",
                "recommendation": "Consider consulting healthcare provider"
            }
        ],
        "analysis_date": "2024-01-15T10:30:00Z"
    },
    "agent": "Analytics",
    "operation": "analyze_cycle_irregularities"
}
```

**Response (Insufficient Data):**
```json
{
    "success": true,
    "data": {
        "sufficient_data": false,
        "message": "Need at least 3 cycles for analysis",
        "cycles_count": 1
    },
    "agent": "Analytics",
    "operation": "analyze_cycle_irregularities"
}
```

#### 3. Predict Next Period

Predicts the user's next menstrual period based on historical data.

```http
POST /api/agents/analytics/predict-period/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "predicted_date": "2024-02-15T00:00:00Z",
        "confidence": 0.85,
        "prediction_window": {
            "earliest": "2024-02-13",
            "latest": "2024-02-17"
        },
        "based_on_cycles": 8,
        "average_cycle_length": 28.5,
        "prediction_method": "weighted_average"
    },
    "agent": "Analytics",
    "operation": "predict_next_period"
}
```

#### 4. Predict Fertility Window

Calculates the fertility window and ovulation timing.

```http
POST /api/agents/analytics/predict-fertility/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "fertile_window": {
            "start": "2024-01-25",
            "end": "2024-01-30",
            "peak_day": "2024-01-28"
        },
        "ovulation_date": "2024-01-28",
        "confidence": 0.78,
        "fertility_score": "high",
        "recommendations": [
            "Track basal body temperature for better accuracy",
            "Consider ovulation test kits during fertile window"
        ]
    },
    "agent": "Analytics",
    "operation": "predict_fertility_window"
}
```

#### 5. Generate Health Insights

Generates comprehensive health insights combining multiple data sources.

```http
POST /api/agents/analytics/health-insights/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "cycle_analysis": {
            "regularity_score": 88,
            "average_length": 28.5,
            "variability": 2.1,
            "trends": "stable"
        },
        "predictions": {
            "period_prediction": {
                "predicted_date": "2024-02-15",
                "confidence": 0.85
            },
            "fertility_prediction": {
                "next_fertile_window": "2024-01-25 to 2024-01-30",
                "confidence": 0.78
            }
        },
        "patterns": {
            "mood_patterns": {
                "stability": "moderate",
                "cycle_correlation": "strong"
            },
            "symptom_patterns": {
                "common_symptoms": ["bloating", "cramps"],
                "timing": "pre-menstrual"
            }
        },
        "recommendations": {
            "lifestyle": [...],
            "health_screenings": [...],
            "tracking": [...]
        }
    },
    "agent": "Analytics",
    "operation": "generate_health_insights"
}
```

#### 6. Get Personalized Recommendations

Provides personalized health recommendations based on user data.

```http
POST /api/agents/analytics/recommendations/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "lifestyle": [
            {
                "category": "nutrition",
                "title": "Increase Iron Intake",
                "description": "Based on your cycle patterns, consider iron-rich foods",
                "priority": "medium",
                "evidence": "cycle_analysis"
            }
        ],
        "health_screenings": [
            {
                "screening_type": "cervical_cancer_screening",
                "due_date": "2024-06-15",
                "priority": "routine",
                "reason": "Age-based recommendation"
            }
        ],
        "tracking": [
            {
                "category": "symptoms",
                "recommendation": "Track mood changes during pre-menstrual phase",
                "benefit": "Better pattern recognition"
            }
        ]
    },
    "agent": "Analytics",
    "operation": "get_personalized_recommendations"
}
```

#### 7. Assess Health Risks

Analyzes health risks based on user data and medical history.

```http
POST /api/agents/analytics/health-risks/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "overall_risk_score": 25,
        "risk_level": "low",
        "risk_factors": [
            {
                "category": "family_history",
                "factor": "breast_cancer",
                "risk_level": "moderate",
                "description": "Family history of breast cancer"
            }
        ],
        "protective_factors": [
            "regular_exercise",
            "healthy_diet",
            "normal_bmi"
        ],
        "recommendations": [
            {
                "category": "screening",
                "recommendation": "Earlier breast cancer screening",
                "priority": "high"
            }
        ]
    },
    "agent": "Analytics",
    "operation": "assess_health_risks"
}
```

#### 8. Analyze Patterns

Analyzes specific patterns in health data.

```http
POST /api/agents/analytics/analyze-patterns/
```

**Request Body:**
```json
{
    "user_id": 1,                // Optional: defaults to authenticated user
    "data_type": "mood",         // Options: mood, energy, symptoms, sleep
    "days_back": 90              // Optional: defaults to 90 days
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "pattern_type": "mood",
        "analysis_period": "90 days",
        "patterns_detected": [
            {
                "pattern": "pre_menstrual_mood_changes",
                "frequency": "consistent",
                "timing": "5-7 days before period",
                "severity": "moderate"
            }
        ],
        "correlations": [
            {
                "correlation_type": "cycle_phase",
                "strength": "strong",
                "description": "Mood patterns strongly correlate with menstrual cycle"
            }
        ],
        "recommendations": [
            "Track mood daily for better pattern recognition",
            "Consider stress management techniques during pre-menstrual phase"
        ]
    },
    "agent": "Analytics",
    "operation": "analyze_patterns"
}
```

## Performance Agent API (Admin Only)

### Base Path: `/api/agents/performance/`

The Performance Agent handles system optimization, caching, and monitoring. **All endpoints require admin privileges.**

#### 1. Get Agent Status

```http
GET /api/agents/performance/status/
```

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "name": "Performance",
    "version": "1.0.0",
    "initialized": true,
    "services": {
        "db_optimizer": {
            "service": "DatabaseOptimizationService",
            "status": "active"
        },
        "cache_service": {
            "service": "CachingService",
            "status": "active"
        },
        "task_service": {
            "service": "BackgroundTaskService",
            "status": "active"
        }
    },
    "last_check": "2024-01-15T10:30:00Z"
}
```

#### 2. Optimize Database Queries

```http
POST /api/agents/performance/optimize-database/
```

**Request Body:**
```json
{
    "optimization_type": "cycles"  // Options: general, cycles, health_logs, indexes
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "optimization_type": "cycles",
        "optimizations_applied": [
            {
                "optimization_area": "menstrual_cycles",
                "queries_count": 3,
                "improvement_percentage": 25.0,
                "optimizations": [
                    "Added indexes on cycle_start_date",
                    "Optimized date range queries"
                ]
            }
        ],
        "performance_improvement": 25.0,
        "queries_optimized": 3
    },
    "agent": "Performance",
    "operation": "optimize_database_queries"
}
```

#### 3. Refresh Cache Layer

```http
POST /api/agents/performance/refresh-cache/
```

**Request Body:**
```json
{
    "cache_type": "user_data"  // Options: all, user_data, predictions, analytics
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "cache_type": "user_data",
        "operations": [
            {
                "cache_area": "user_data",
                "keys_cleared": 25,
                "hit_rate_improvement": 15.0,
                "description": "Refreshed user profile and health data cache"
            }
        ],
        "cache_hit_improvement": 15.0
    },
    "agent": "Performance",
    "operation": "refresh_cache_layer"
}
```

#### 4. Monitor System Performance

```http
GET /api/agents/performance/monitor-performance/
```

**Response:**
```json
{
    "success": true,
    "data": {
        "database": {
            "connection_pool": {
                "active_connections": 5,
                "max_connections": 100,
                "utilization_percentage": 5.0
            },
            "query_performance": {
                "avg_query_time": "45ms",
                "slow_queries_count": 2,
                "optimization_score": 85
            }
        },
        "cache": {
            "hit_rate": "87%",
            "miss_rate": "13%",
            "memory_usage": {
                "used": "256MB",
                "total": "512MB",
                "percentage": 50
            }
        },
        "background_tasks": {
            "active_tasks": 5,
            "pending_tasks": 12,
            "worker_utilization": "65%",
            "queue_health": "good"
        },
        "overall_health": {
            "overall_score": 87.3,
            "level": "good"
        }
    },
    "agent": "Performance",
    "operation": "monitor_system_performance"
}
```

## Clinical Agent API

### Base Path: `/api/agents/clinical/`

The Clinical Agent handles healthcare provider integrations, medical appointments, and health screening recommendations.

#### 1. Get Agent Status

```http
GET /api/agents/clinical/status/
```

**Response:**
```json
{
    "name": "Clinical",
    "version": "1.0.0",
    "initialized": true,
    "services": {
        "health_screening": {
            "service": "HealthScreeningService",
            "status": "active"
        },
        "medical_history": {
            "service": "MedicalHistoryService",
            "status": "active"
        },
        "provider_integration": {
            "service": "ProviderIntegrationService",
            "status": "active"
        }
    },
    "last_check": "2024-01-15T10:30:00Z"
}
```

#### 2. Get Health Screening Recommendations

```http
POST /api/agents/clinical/screening-recommendations/
```

**Request Body:**
```json
{
    "user_id": 1  // Optional: defaults to authenticated user
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "age": 28,
        "screening_recommendations": [
            {
                "screening_type": "cervical_cancer_screening",
                "recommended_frequency": "every_3_years",
                "priority": "routine",
                "description": "Pap smear for cervical cancer screening",
                "last_completed": null,
                "next_due": "2024-06-15",
                "reasons": [
                    "Prevent cervical cancer",
                    "Early detection of abnormal cells"
                ]
            },
            {
                "screening_type": "blood_pressure_check",
                "recommended_frequency": "annually",
                "priority": "routine",
                "description": "Regular blood pressure monitoring",
                "next_due": "2024-12-01",
                "reasons": [
                    "Monitor cardiovascular health",
                    "Detect hypertension early"
                ]
            }
        ],
        "urgent_screenings": [],
        "routine_screenings": [...],
        "lifestyle_recommendations": [
            {
                "category": "nutrition",
                "title": "Calcium and Vitamin D",
                "description": "Ensure adequate calcium (1000-1200mg) and vitamin D (600-800 IU) daily",
                "priority": "medium",
                "reasons": ["Bone health", "Hormonal balance"]
            }
        ]
    },
    "agent": "Clinical",
    "operation": "get_health_screening_recommendations"
}
```

#### 3. Schedule Medical Appointment

```http
POST /api/agents/clinical/schedule-appointment/
```

**Request Body:**
```json
{
    "user_id": 1,  // Optional: defaults to authenticated user
    "appointment_data": {
        "type": "gynecology_checkup",
        "date": "2024-02-20T14:00:00Z",
        "provider": "Dr. Smith",
        "notes": "Annual checkup"
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "appointment_id": 123,
        "scheduled_date": "2024-02-20T14:00:00Z",
        "provider": "Dr. Smith",
        "type": "gynecology_checkup",
        "status": "successfully_scheduled"
    },
    "agent": "Clinical",
    "operation": "schedule_medical_appointment"
}
```

#### 4. Update Medical History

```http
POST /api/agents/clinical/update-medical-history/
```

**Request Body:**
```json
{
    "user_id": 1,  // Optional: defaults to authenticated user
    "medical_data": {
        "medical_conditions": ["PCOS", "Hypothyroidism"],
        "medications": [
            {
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice_daily"
            }
        ],
        "allergies": ["Penicillin"],
        "family_history": {
            "breast_cancer": ["maternal_grandmother"],
            "diabetes": ["father"]
        },
        "surgical_history": []
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "updated_fields": [
            "medical_conditions",
            "medications", 
            "allergies",
            "family_history"
        ],
        "new_records_created": 0,
        "update_timestamp": "2024-01-15T10:30:00Z"
    },
    "agent": "Clinical",
    "operation": "update_medical_history"
}
```

#### 5. Get Medical History Summary

```http
GET /api/agents/clinical/medical-history-summary/?user_id=1
```

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "summary_generated": "2024-01-15T10:30:00Z",
        "medical_history": {
            "medical_conditions": ["PCOS"],
            "medications": [
                {
                    "name": "Metformin",
                    "dosage": "500mg",
                    "frequency": "twice_daily"
                }
            ],
            "allergies": ["Penicillin"],
            "family_history": {
                "breast_cancer": ["maternal_grandmother"],
                "diabetes": ["father"]
            },
            "surgical_history": [],
            "last_updated": "2024-01-15T09:00:00Z"
        },
        "recent_health_data": {
            "recent_cycles": [
                {
                    "start_date": "2024-01-01",
                    "length": 28,
                    "flow_intensity": "medium"
                }
            ],
            "recent_symptoms": [
                {
                    "date": "2024-01-14",
                    "mood": "happy",
                    "energy_level": 8,
                    "symptoms": ["bloating"]
                }
            ]
        },
        "health_trends": {
            "cycle_regularity": {
                "average_length": 28.5,
                "variability": 2.1,
                "regularity_assessment": "regular"
            }
        },
        "risk_assessment": {
            "cardiovascular_risk": "low",
            "reproductive_health_risk": "low",
            "metabolic_risk": "low",
            "overall_assessment": "Low risk profile based on available data"
        }
    },
    "agent": "Clinical",
    "operation": "get_medical_history_summary"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "success": false,
    "error": "Invalid request parameters",
    "agent": "AgentName",
    "operation": "operation_name"
}
```

### 401 Unauthorized
```json
{
    "success": false,
    "error": "Authentication credentials were not provided",
    "agent": "AgentName",
    "operation": "operation_name"
}
```

### 403 Forbidden
```json
{
    "success": false,
    "error": "Unauthorized access to user data",
    "agent": "AgentName",
    "operation": "operation_name"
}
```

### 404 Not Found
```json
{
    "success": false,
    "error": "User not found or not verified for women's health",
    "agent": "AgentName",
    "operation": "operation_name"
}
```

### 500 Internal Server Error
```json
{
    "success": false,
    "error": "Failed to initialize Agent",
    "agent": "AgentName",
    "operation": "operation_name"
}
```

## Testing

### Prerequisites

1. **Set up test data:**
   ```bash
   python test_agent_data_setup.py
   ```

2. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

### Automated Testing

Run the comprehensive API test suite:

```bash
python test_agents_api.py
```

The test script will:
- Test all endpoints with valid data
- Test error scenarios
- Test unauthorized access
- Test insufficient data scenarios
- Generate a detailed test report

### Manual Testing with cURL

#### Analytics Agent Example

```bash
# Get analytics agent status
curl -X GET "http://localhost:8000/api/agents/analytics/status/" \
     -H "Authorization: Bearer <your_token>"

# Analyze cycle irregularities
curl -X POST "http://localhost:8000/api/agents/analytics/cycle-irregularities/" \
     -H "Authorization: Bearer <your_token>" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1, "months_back": 6}'
```

#### Performance Agent Example (Admin only)

```bash
# Monitor system performance
curl -X GET "http://localhost:8000/api/agents/performance/monitor-performance/" \
     -H "Authorization: Bearer <admin_token>"
```

#### Clinical Agent Example

```bash
# Get health screening recommendations
curl -X POST "http://localhost:8000/api/agents/clinical/screening-recommendations/" \
     -H "Authorization: Bearer <your_token>" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}'
```

### Testing with Postman

Import the provided Postman collection for easy testing:

1. **Import Collection:** `Women_Health_Agents_API.postman_collection.json`
2. **Set Environment Variables:**
   - `base_url`: `http://localhost:8000`
   - `token`: Your JWT token
   - `admin_token`: Admin JWT token
   - `user_id`: Test user ID

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Analytics endpoints:** 60 requests per minute per user
- **Performance endpoints:** 10 requests per minute per admin
- **Clinical endpoints:** 30 requests per minute per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642681200
```

## Monitoring

### Health Check Endpoint

```http
GET /api/agents/health/
```

Returns system health status for load balancers and monitoring systems.

### Metrics Endpoint (Admin only)

```http
GET /api/agents/performance/monitor-performance/
```

Provides detailed system metrics for monitoring and alerting.

## Security Considerations

1. **Authentication Required:** All endpoints require valid JWT tokens
2. **User Data Access:** Users can only access their own data
3. **Admin Endpoints:** Performance endpoints restricted to admin users
4. **Input Validation:** All inputs are validated and sanitized
5. **Rate Limiting:** Prevents API abuse
6. **HTTPS Required:** Use HTTPS in production
7. **Token Expiration:** JWT tokens have limited lifetime

## Support

For API support and questions:

- **Documentation:** This document and inline code comments
- **Testing Scripts:** Use provided testing scripts for validation
- **Error Reporting:** Include detailed error messages and request/response data

## Changelog

### Version 1.0.0
- Initial release with Analytics, Performance, and Clinical agents
- Comprehensive endpoint coverage
- Authentication and authorization
- Rate limiting and monitoring
- Automated testing suite