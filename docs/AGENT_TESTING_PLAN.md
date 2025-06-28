# Comprehensive Agent Testing Plan

## Overview

This document outlines a comprehensive testing strategy for all women's health agents, including API endpoints, test scenarios, and validation procedures.

## Testing Architecture

### Test Environment Setup
- **Base URL**: `http://localhost:8000/api/agents/`
- **Authentication**: JWT token-based authentication
- **Database**: SQLite for testing (isolated from production)
- **Cache**: Redis test instance
- **Background Tasks**: Celery test workers

### Test Categories

1. **Unit Tests**: Individual agent methods and services
2. **Integration Tests**: Agent interactions and data flow
3. **API Tests**: HTTP endpoint validation
4. **Performance Tests**: Load testing and optimization validation
5. **End-to-End Tests**: Complete user workflows

## Agent Testing Breakdown

### 1. Analytics Agent Testing

#### API Endpoints
```
Base: /api/agents/analytics/

GET    /status/                           # Agent status
POST   /cycle-irregularities/             # Detect irregularities
POST   /predict-period/                   # Period prediction
POST   /predict-fertility/                # Fertility window
POST   /health-insights/                  # Generate insights
POST   /recommendations/                  # Get recommendations
POST   /health-risks/                     # Risk assessment
POST   /analyze-patterns/                 # Pattern analysis
```

#### Test Scenarios

**1. Cycle Irregularity Detection**
```json
POST /api/agents/analytics/cycle-irregularities/
{
    "user_id": 1,
    "months_back": 6
}

Expected Response:
{
    "success": true,
    "data": {
        "sufficient_data": true,
        "regularity_score": 85,
        "irregularities": [],
        "cycle_count": 6,
        "analysis_date": "2024-01-15T10:30:00Z"
    },
    "agent": "Analytics",
    "operation": "analyze_cycle_irregularities"
}
```

**2. Period Prediction**
```json
POST /api/agents/analytics/predict-period/
{
    "user_id": 1
}

Expected Response:
{
    "success": true,
    "data": {
        "predicted_date": "2024-02-15T00:00:00Z",
        "confidence": 0.85,
        "prediction_window": {
            "earliest": "2024-02-13",
            "latest": "2024-02-17"
        },
        "based_on_cycles": 8
    },
    "agent": "Analytics",
    "operation": "predict_next_period"
}
```

**3. Health Insights Generation**
```json
POST /api/agents/analytics/health-insights/
{
    "user_id": 1
}

Expected Response:
{
    "success": true,
    "data": {
        "cycle_analysis": {
            "regularity_score": 88,
            "average_length": 28.5,
            "variability": 2.1
        },
        "predictions": {
            "period_prediction": {...},
            "fertility_prediction": {...}
        },
        "recommendations": {
            "lifestyle": [...],
            "health_screenings": [...]
        }
    },
    "agent": "Analytics",
    "operation": "generate_health_insights"
}
```

#### Error Test Cases
```json
// Invalid user
POST /api/agents/analytics/predict-period/
{
    "user_id": 99999
}

Expected Response:
{
    "success": false,
    "error": "Invalid user or user not verified",
    "agent": "Analytics",
    "operation": "predict_next_period"
}

// Insufficient data
POST /api/agents/analytics/cycle-irregularities/
{
    "user_id": 2  // User with < 3 cycles
}

Expected Response:
{
    "success": true,
    "data": {
        "sufficient_data": false,
        "message": "Need at least 3 cycles for analysis",
        "cycles_count": 1
    }
}
```

### 2. Performance Agent Testing

#### API Endpoints
```
Base: /api/agents/performance/

GET    /status/                           # Agent status
POST   /optimize-database/                # Database optimization
POST   /refresh-cache/                    # Cache refresh
POST   /schedule-task/                    # Background task scheduling
GET    /monitor-performance/              # Performance metrics
POST   /optimize-user-data/               # User-specific optimization
POST   /cleanup-expired/                  # Data cleanup
POST   /analyze-queries/                  # Query analysis
GET    /resource-utilization/             # Resource metrics
POST   /optimize-peak-load/               # Peak load preparation
```

#### Test Scenarios

**1. Database Optimization**
```json
POST /api/agents/performance/optimize-database/
{
    "optimization_type": "cycles"
}

Expected Response:
{
    "success": true,
    "data": {
        "optimization_type": "cycles",
        "optimizations_applied": [
            {
                "optimization_area": "menstrual_cycles",
                "queries_count": 3,
                "improvement_percentage": 25.0
            }
        ],
        "performance_improvement": 25.0,
        "queries_optimized": 3
    },
    "agent": "Performance",
    "operation": "optimize_database_queries"
}
```

**2. Cache Refresh**
```json
POST /api/agents/performance/refresh-cache/
{
    "cache_type": "user_data"
}

Expected Response:
{
    "success": true,
    "data": {
        "cache_type": "user_data",
        "operations": [
            {
                "cache_area": "user_data",
                "keys_cleared": 25,
                "hit_rate_improvement": 15.0
            }
        ],
        "cache_hit_improvement": 15.0
    },
    "agent": "Performance",
    "operation": "refresh_cache_layer"
}
```

**3. Performance Monitoring**
```json
GET /api/agents/performance/monitor-performance/

Expected Response:
{
    "success": true,
    "data": {
        "database": {
            "connection_pool": {
                "active_connections": 5,
                "utilization_percentage": 5.0
            },
            "query_performance": {
                "avg_query_time": "45ms",
                "optimization_score": 85
            }
        },
        "cache": {
            "hit_rate": "87%",
            "memory_usage": {
                "percentage": 50
            }
        },
        "background_tasks": {
            "active_tasks": 5,
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

### 3. Clinical Agent Testing

#### API Endpoints
```
Base: /api/agents/clinical/

GET    /status/                           # Agent status
POST   /screening-recommendations/        # Health screening recommendations
POST   /schedule-appointment/             # Schedule medical appointment
POST   /update-medical-history/           # Update medical history
GET    /medical-history-summary/          # Medical history summary
POST   /connect-provider/                 # Connect healthcare provider
GET    /upcoming-appointments/            # Get upcoming appointments
POST   /analyze-health-risks/             # Health risk analysis
POST   /generate-health-report/           # Generate health report
GET    /track-medication-compliance/      # Medication compliance
POST   /sync-provider-data/               # Sync provider data
POST   /clinical-insights/                # Clinical insights
```

#### Test Scenarios

**1. Health Screening Recommendations**
```json
POST /api/agents/clinical/screening-recommendations/
{
    "user_id": 1
}

Expected Response:
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
                "next_due": "2024-06-15",
                "reasons": ["Prevent cervical cancer", "Early detection"]
            }
        ],
        "urgent_screenings": [],
        "routine_screenings": [...],
        "lifestyle_recommendations": [...]
    },
    "agent": "Clinical",
    "operation": "get_health_screening_recommendations"
}
```

**2. Schedule Medical Appointment**
```json
POST /api/agents/clinical/schedule-appointment/
{
    "user_id": 1,
    "appointment_data": {
        "type": "gynecology_checkup",
        "date": "2024-02-20T14:00:00Z",
        "provider": "Dr. Smith",
        "notes": "Annual checkup"
    }
}

Expected Response:
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

**3. Medical History Update**
```json
POST /api/agents/clinical/update-medical-history/
{
    "user_id": 1,
    "medical_data": {
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
        }
    }
}

Expected Response:
{
    "success": true,
    "data": {
        "user_id": 1,
        "updated_fields": ["medical_conditions", "medications", "allergies", "family_history"],
        "new_records_created": 0,
        "update_timestamp": "2024-01-15T10:30:00Z"
    },
    "agent": "Clinical",
    "operation": "update_medical_history"
}
```

## Test Data Setup

### Required Test Users
```json
// User 1: Complete data for full testing
{
    "id": 1,
    "email": "test1@example.com",
    "womens_health_verified": true,
    "birth_date": "1995-06-15",
    "profile": {
        "cycles": 8,
        "health_logs": 60,
        "has_medical_history": true
    }
}

// User 2: Minimal data for insufficient data testing
{
    "id": 2,
    "email": "test2@example.com",
    "womens_health_verified": true,
    "birth_date": "1990-03-10",
    "profile": {
        "cycles": 1,
        "health_logs": 5,
        "has_medical_history": false
    }
}

// User 3: Risk factors for clinical testing
{
    "id": 3,
    "email": "test3@example.com",
    "womens_health_verified": true,
    "birth_date": "1985-09-22",
    "profile": {
        "cycles": 12,
        "health_logs": 90,
        "has_medical_history": true,
        "risk_factors": ["family_history_breast_cancer", "pcos"]
    }
}
```

### Test Data Generation Scripts

#### 1. Menstrual Cycle Data
```python
def create_test_cycles(user_id, count=8):
    cycles = []
    start_date = timezone.now().date() - timedelta(days=count * 30)
    
    for i in range(count):
        cycle = MenstrualCycle.objects.create(
            womens_health_profile_id=user_id,
            cycle_start_date=start_date + timedelta(days=i * 28 + random.randint(-3, 3)),
            cycle_length=random.randint(26, 32),
            flow_intensity=random.choice(['light', 'medium', 'heavy']),
            pain_level=random.randint(1, 5)
        )
        cycles.append(cycle)
    
    return cycles
```

#### 2. Daily Health Log Data
```python
def create_test_health_logs(user_id, count=60):
    logs = []
    start_date = timezone.now().date() - timedelta(days=count)
    
    for i in range(count):
        log = DailyHealthLog.objects.create(
            womens_health_profile_id=user_id,
            log_date=start_date + timedelta(days=i),
            mood=random.choice(['happy', 'neutral', 'sad', 'anxious', 'energetic']),
            energy_level=random.randint(1, 10),
            symptoms=random.choice([
                ['bloating', 'cramps'],
                ['headache'],
                ['mood_swings', 'fatigue'],
                []
            ])
        )
        logs.append(log)
    
    return logs
```

#### 3. Medical History Data
```python
def create_test_medical_history(user_id, risk_profile='normal'):
    conditions = []
    family_history = {}
    
    if risk_profile == 'high_risk':
        conditions = ['PCOS', 'Hypothyroidism']
        family_history = {
            'breast_cancer': ['maternal_grandmother'],
            'diabetes': ['father', 'paternal_grandfather']
        }
    elif risk_profile == 'moderate_risk':
        conditions = ['Iron_deficiency']
        family_history = {
            'heart_disease': ['father']
        }
    
    history = MedicalHistory.objects.create(
        user_id=user_id,
        medical_conditions=conditions,
        medications=[],
        allergies=[],
        family_history=family_history,
        surgical_history=[]
    )
    
    return history
```

## Test Execution Plan

### Phase 1: Unit Testing (Week 1)
- [ ] Test all service methods individually
- [ ] Validate data processing logic
- [ ] Test error handling and edge cases
- [ ] Verify calculation algorithms

### Phase 2: Integration Testing (Week 2)
- [ ] Test agent initialization and dependencies
- [ ] Validate inter-service communication
- [ ] Test database operations
- [ ] Verify cache interactions

### Phase 3: API Testing (Week 3)
- [ ] Create API endpoints for all agents
- [ ] Test HTTP requests/responses
- [ ] Validate authentication and authorization
- [ ] Test rate limiting and security

### Phase 4: Performance Testing (Week 4)
- [ ] Load testing with multiple concurrent users
- [ ] Database performance under load
- [ ] Cache performance validation
- [ ] Background task processing efficiency

### Phase 5: End-to-End Testing (Week 5)
- [ ] Complete user workflows
- [ ] Data consistency across agents
- [ ] Real-world scenario simulation
- [ ] User acceptance testing

## Test Automation

### Automated Test Suite Structure
```
tests/
├── unit/
│   ├── test_analytics_agent.py
│   ├── test_performance_agent.py
│   ├── test_clinical_agent.py
│   └── test_services/
│       ├── test_cycle_analytics.py
│       ├── test_health_predictions.py
│       └── test_database_optimization.py
├── integration/
│   ├── test_agent_interactions.py
│   ├── test_database_operations.py
│   └── test_cache_operations.py
├── api/
│   ├── test_analytics_endpoints.py
│   ├── test_performance_endpoints.py
│   └── test_clinical_endpoints.py
├── performance/
│   ├── test_load_scenarios.py
│   └── test_optimization_results.py
└── e2e/
    ├── test_user_workflows.py
    └── test_complete_scenarios.py
```

### Test Configuration
```python
# test_settings.py
TESTING = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

## Continuous Testing

### GitHub Actions Workflow
```yaml
name: Agent Testing Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=api.agent_modules
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
    
    - name: Run API tests
      run: pytest tests/api/ -v
    
    - name: Generate coverage report
      run: pytest --cov=api.agent_modules --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

## Performance Benchmarks

### Target Metrics
- **Response Time**: < 200ms for 95% of requests
- **Throughput**: > 100 requests/second per agent
- **Memory Usage**: < 512MB per agent instance
- **Database Queries**: < 5 queries per request average
- **Cache Hit Rate**: > 85%

### Load Testing Scenarios
1. **Normal Load**: 50 concurrent users
2. **Peak Load**: 200 concurrent users
3. **Stress Test**: 500 concurrent users
4. **Endurance Test**: 24-hour continuous operation

## Test Reporting

### Test Coverage Requirements
- **Unit Tests**: 95% code coverage
- **Integration Tests**: 90% scenario coverage
- **API Tests**: 100% endpoint coverage
- **Performance Tests**: All critical paths tested

### Reporting Tools
- **Coverage**: coverage.py and codecov
- **Performance**: pytest-benchmark
- **API Testing**: pytest-django
- **Load Testing**: locust.io

## Quality Gates

### Pre-Deployment Checklist
- [ ] All unit tests passing (100%)
- [ ] Integration tests passing (100%)
- [ ] API tests passing (100%)
- [ ] Performance benchmarks met
- [ ] Security scans completed
- [ ] Code coverage > 95%
- [ ] Documentation updated
- [ ] Manual testing scenarios completed

## Monitoring and Alerting

### Production Monitoring
- **Application Performance Monitoring (APM)**
- **Error Rate Monitoring**
- **Response Time Tracking**
- **Resource Utilization Alerts**
- **Health Check Endpoints**

This comprehensive testing plan ensures that all agent implementations are thoroughly validated before deployment and continue to perform optimally in production.