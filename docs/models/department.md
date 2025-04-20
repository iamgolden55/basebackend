# Department Model Documentation

## Overview
The Department model represents different medical departments within a hospital. It manages various aspects including capacity, staffing, budgeting, and operational details.

## Model Structure

### Basic Information
| Field | Type | Description |
|-------|------|-------------|
| `hospital` | ForeignKey | Reference to the Hospital model |
| `name` | CharField | Department name |
| `code` | CharField | Unique department code |
| `department_type` | CharField | Type/Category of department |
| `description` | TextField | Department description |
| `is_active` | BooleanField | Department operational status |

### Department Types
Departments are categorized into three main types:

1. **Clinical Departments**
   - Medical Department
   - Surgical Department
   - Emergency Department
   - Critical Care
   - Outpatient Clinic

2. **Support Departments**
   - Laboratory
   - Radiology
   - Pharmacy
   - Physiotherapy

3. **Administrative Departments**
   - Administration
   - Medical Records
   - IT

### Contact and Location
| Field | Type | Description |
|-------|------|-------------|
| `floor_number` | CharField | Physical floor location |
| `wing` | CharField | Hospital wing location |
| `extension_number` | CharField | Internal phone extension |
| `emergency_contact` | CharField | Emergency contact number |
| `email` | EmailField | Department email address |

### Operational Details
| Field | Type | Description |
|-------|------|-------------|
| `is_24_hours` | BooleanField | 24/7 operation status |
| `operating_hours` | JSONField | Operating hours by day |
| `appointment_duration` | PositiveIntegerField | Default duration |
| `max_daily_appointments` | PositiveIntegerField | Daily limit |
| `requires_referral` | BooleanField | Referral requirement |

### Capacity Management
| Field | Type | Description |
|-------|------|-------------|
| `total_beds` | PositiveIntegerField | Total regular beds |
| `occupied_beds` | PositiveIntegerField | Occupied regular beds |
| `icu_beds` | PositiveIntegerField | Total ICU beds |
| `occupied_icu_beds` | PositiveIntegerField | Occupied ICU beds |
| `bed_capacity` | PositiveIntegerField | Total bed capacity |
| `current_patient_count` | PositiveIntegerField | Current patients |

### Staff Management
| Field | Type | Description |
|-------|------|-------------|
| `minimum_staff_required` | PositiveIntegerField | Minimum required staff |
| `current_staff_count` | PositiveIntegerField | Current active staff |
| `recommended_staff_ratio` | FloatField | Staff to patient ratio |

### Budget Management
| Field | Type | Description |
|-------|------|-------------|
| `annual_budget` | DecimalField | Annual budget allocation |
| `budget_year` | PositiveIntegerField | Fiscal year |
| `budget_utilized` | DecimalField | Amount utilized |
| `equipment_budget` | DecimalField | Equipment allocation |
| `staff_budget` | DecimalField | Staff allocation |

### Appointment Settings
| Field | Type | Description |
|-------|------|-------------|
| `max_daily_appointments` | PositiveIntegerField | Daily limit |
| `requires_referral` | BooleanField | Referral requirement |

### Continuity of Care Configuration
| Field | Type | Description |
|-------|------|-------------|
| `continuity_weight` | FloatField | Base weight for continuity of care (0-5) |
| `follow_up_continuity_multiplier` | FloatField | Multiplier for follow-up appointments |
| `max_continuity_appointments` | IntegerField | Maximum appointments to consider for continuity |
| `continuity_decay_days` | IntegerField | Days after which continuity score begins to decay |
| `cross_department_continuity` | BooleanField | Whether to consider cross-department continuity |
| `min_appointments_for_continuity` | IntegerField | Minimum appointments needed for continuity |
| `prioritize_continuity_for_chronic` | BooleanField | Higher continuity weight for chronic conditions |

## Key Properties and Methods

### Capacity Management
```python
@property
def available_beds(self):
    """Get number of available regular beds"""
    return self.total_beds - self.occupied_beds

@property
def available_icu_beds(self):
    """Get number of available ICU beds"""
    return self.icu_beds - self.occupied_icu_beds

@property
def total_available_beds(self):
    """Get total number of available beds"""
    return self.available_beds + self.available_icu_beds
```

### Utilization Metrics
```python
@property
def bed_utilization_rate(self):
    """Calculate bed utilization rate"""
    return (self.occupied_beds + self.occupied_icu_beds) / (self.total_beds + self.icu_beds) * 100

@property
def staff_utilization_rate(self):
    """Calculate staff utilization based on recommended ratio"""
    recommended_staff = self.current_patient_count * self.recommended_staff_ratio
    return (self.current_staff_count / recommended_staff) * 100
```

### Budget Management
```python
@property
def budget_utilization_rate(self):
    """Calculate budget utilization rate"""
    return (self.budget_utilized / self.annual_budget) * 100

@property
def remaining_budget(self):
    """Calculate remaining budget"""
    return self.annual_budget - self.budget_utilized
```

## Business Rules and Validations

### Department Type Rules
1. Only clinical departments can:
   - Assign/release beds
   - Declare emergencies
   - Have bed capacity

2. Administrative departments:
   - Cannot accept appointments
   - Cannot have bed capacity
   - Cannot declare emergencies

### Capacity Rules
1. Occupied beds cannot exceed total beds
2. Current patient count cannot exceed total capacity
3. Administrative departments cannot have beds

### Staff Rules
1. Current staff count cannot be negative
2. Minimum staff required must be at least 1
3. Current staff must meet minimum requirement

### Budget Rules
1. Budget amounts cannot be negative
2. Utilized budget cannot exceed annual budget
3. Sum of category budgets cannot exceed annual budget

### Operating Hours Rules
1. 24-hour departments must have full day operating hours
2. Operating hours must be in valid time format
3. End time must be after start time

## Database Indexes
The model includes optimized indexes for:
1. Primary lookups (code, department_type)
2. Operational status (is_active, is_24_hours)
3. Location-based queries (wing)
4. Common query patterns (hospital + department_type)
5. Capacity monitoring (current_patient_count)
6. Staff monitoring (current_staff_count)

## Usage Examples

### Creating a Department
```python
department = Department.objects.create(
    hospital=hospital,
    name="Emergency Department",
    code="ED-001",
    department_type="emergency",
    is_24_hours=True
)
```

### Managing Beds
```python
# Assign a regular bed
department.assign_bed()

# Assign an ICU bed
department.assign_bed(is_icu=True)

# Release a bed
department.release_bed()
```

### Managing Budget
```python
# Update budget utilization
department.update_budget_utilization(
    amount=5000,
    category='equipment'
)
```

### Checking Availability
```python
# Check if department can accept appointments
if department.is_available_for_appointments:
    slots = department.get_available_slots(date)
```

## Best Practices
1. Always use the model's methods for bed management
2. Validate budget updates through the update_budget_utilization method
3. Check department type before performing type-specific operations
4. Use the provided properties for calculating utilization rates
5. Regularly update staff counts using update_staff_count method

## Security Considerations
1. Implement proper access controls for budget management
2. Restrict bed management to authorized personnel
3. Protect sensitive contact information
4. Implement audit logging for critical operations

## Performance Considerations
1. Use provided indexes for efficient queries
2. Batch update operations when possible
3. Cache frequently accessed properties
4. Use select_related/prefetch_related for related data 