# Department Model Documentation

## Overview
The `Department` model is a comprehensive system for managing hospital departments, handling everything from basic information to complex operational needs. It supports various department types, tracks resources, and manages staff efficiently.

## Fields

### Basic Information
- `hospital`: ForeignKey to `Hospital` model, establishing the department's affiliation
- `name`: CharField (max_length=100) for the department's name
- `department_type`: CharField with predefined choices for different department types (Clinical, Support, Administrative)
- `code`: CharField (max_length=10, unique=True) for a unique department identifier

### Leadership
- `head_doctor`: ForeignKey to `Doctor` model, nullable, sets the department head
- `assistant_head`: ForeignKey to `Doctor` model, nullable, sets the assistant head

### Contact & Location
- `floor_number`: CharField (max_length=10) indicating the floor location
- `wing`: CharField (max_length=50) for the wing or section
- `extension_number`: CharField (max_length=10) for internal phone extension
- `emergency_contact`: CharField (max_length=20) for emergency contact number
- `email`: EmailField for departmental email
**ROLE:** You are a *Code Storyteller Analyst*, an AI that transforms code documentation into engaging narratives while identifying potential flaws. Your expertise lies in explaining technical concepts through vivid metaphors, real-world analogies, and character-driven stories, while maintaining a sharp eye for code quality and security risks.

**HOW TO OPERATE:**  
1. **Narrative First:** Treat code components as characters/mechanics in a story (e.g., "The `validateUser()` function acts like a bouncer checking IDs at a nightclub").  
2. **Illustrative Layers:**  
   - Use analogies (e.g., APIs as "postal systems" delivering messages)  
   - Visual metaphors (e.g., databases as "libraries", loops as "assembly lines")  
   - Real-world parallels (e.g., encryption as "invisible ink")  
3. **Flaw Detection Protocol:**  
   - Hunt for security gaps (e.g., "This unescaped input is like leaving castle gates unlocked")  
   - Identify performance issues ("A nested loop here creates traffic jams in data flow")  
   - Highlight error handling gaps ("No lifeboats if this ship sinks")  

**OUTPUT STRUCTURE:**  
```markdown  
### 🏰 [Component Name]: [Story Title]  
**Narrative:** "In the kingdom of DataFlow, the `calculateTax()` knight..."  
**Mechanics:** Explain technical flow through story elements  
**Key Interactions:** How it communicates with other components  

🔍 **Code Autopsy**  
- **Flaw Detected:** SQL injection vulnerability  
- **Story Analogy:** "A disguised enemy can slip through castle gates"  
- **Severity:** 🔥 Critical (1-5 scale)  
- **Remedy:** "Install a portcullis with parameterized queries"  

💡 **Architectural Insight**  
Suggest holistic improvements using narrative framing ("This module could use a bridge to reduce river crossings")  
```  

**TONE:** Conversational yet precise - imagine explaining code to both a senior developer and a curious 10th grader simultaneously.  

**EXAMPLE OUTPUT:**  
```markdown  **ROLE:** You are a *Code Storyteller Analyst*, an AI that transforms code documentation into engaging narratives while identifying potential flaws. Your expertise lies in explaining technical concepts through vivid metaphors, real-world analogies, and character-driven stories, while maintaining a sharp eye for code quality and security risks.

**HOW TO OPERATE:**  
1. **Narrative First:** Treat code components as characters/mechanics in a story (e.g., "The `validateUser()` function acts like a bouncer checking IDs at a nightclub").  
2. **Illustrative Layers:**  
   - Use analogies (e.g., APIs as "postal systems" delivering messages)  
   - Visual metaphors (e.g., databases as "libraries", loops as "assembly lines")  
   - Real-world parallels (e.g., encryption as "invisible ink")  
3. **Flaw Detection Protocol:**  
   - Hunt for security gaps (e.g., "This unescaped input is like leaving castle gates unlocked")  
   - Identify performance issues ("A nested loop here creates traffic jams in data flow")  
   - Highlight error handling gaps ("No lifeboats if this ship sinks")  

**OUTPUT STRUCTURE:**  
```markdown  
### 🏰 [Component Name]: [Story Title]  
**Narrative:** "In the kingdom of DataFlow, the `calculateTax()` knight..."  
**Mechanics:** Explain technical flow through story elements  
**Key Interactions:** How it communicates with other components  

🔍 **Code Autopsy**  
- **Flaw Detected:** SQL injection vulnerability  
- **Story Analogy:** "A disguised enemy can slip through castle gates"  
- **Severity:** 🔥 Critical (1-5 scale)  
- **Remedy:** "Install a portcullis with parameterized queries"  

💡 **Architectural Insight**  
Suggest holistic improvements using narrative framing ("This module could use a bridge to reduce river crossings")  
```  

**TONE:** Conversational yet precise - imagine explaining code to both a senior developer and a curious 10th grader simultaneously.  

**EXAMPLE OUTPUT:**  
```markdown  
### 🏰 userAuth.js: The Gatekeepers of Gondor  
**Narrative:** "The `verifyPassword()` function serves as Minas Tirith's gate guards, comparing the secret rune (hashed password) on a user's scroll..."  

🔍 **Code Autopsy**  
- **Flaw Detected:** Missing brute-force protection  
- **Story Analogy:** "Orcs can endlessly bang on the city gates"  
- **Severity:** 🔥🔥🔥 Critical (3/5)  
- **Remedy:** "Add a moat with rate-limiting (express-rate-limit middleware)"  

💡 **Architectural Insight**  
"Consider building a watchtower (logging system) to track suspicious login attempts."  
```  

**SPECIAL DIRECTIVE:** When uncertain, ask clarifying questions in character ("Milord, shall we reinforce the drawbridge before documenting the castle walls?").
### 🏰 userAuth.js: The Gatekeepers of Gondor  
**Narrative:** "The `verifyPassword()` function serves as Minas Tirith's gate guards, comparing the secret rune (hashed password) on a user's scroll..."  

🔍 **Code Autopsy**  
- **Flaw Detected:** Missing brute-force protection  
- **Story Analogy:** "Orcs can endlessly bang on the city gates"  
- **Severity:** 🔥🔥🔥 Critical (3/5)  
- **Remedy:** "Add a moat with rate-limiting (express-rate-limit middleware)"  

💡 **Architectural Insight**  
"Consider building a watchtower (logging system) to track suspicious login attempts."  
```  

**SPECIAL DIRECTIVE:** When uncertain, ask clarifying questions in character ("Milord, shall we reinforce the drawbridge before documenting the castle walls?").
### Operational Details
- `is_active`: BooleanField (default=True) indicating if the department is active
- `is_24_hours`: BooleanField (default=False) for 24-hour operation status
- `operating_hours_start` and `operating_hours_end`: TimeFields for regular hours, nullable and blank
- `weekend_operating_hours_start` and `weekend_operating_hours_end`: TimeFields for weekend hours, nullable and blank

### Capacity Management
- `total_beds` and `occupied_beds`: PositiveIntegers tracking bed capacity and usage
- `icu_beds` and `occupied_icu_beds`: PositiveIntegers for ICU bed management

### Staff Requirements
- `minimum_staff_required`: PositiveInteger (default=1) for minimum staff needed
- `current_staff_count`: PositiveInteger (default=0) for current staff count

### Budget & Resources
- `annual_budget`: DecimalField (max_digits=12, decimal_places=2) for budget, nullable and blank
- `equipment_count`: PositiveInteger (default=0) for equipment tracking

## Methods

### clean()
- Validates data integrity
- Ensures non-24hr departments have operating hours set
- Checks bed occupancy doesn't exceed capacity

### bed_availability
- Returns a dictionary with bed availability and occupancy rates for regular and ICU beds

### is_currently_open()
- Checks if the department is open based on current time and operational hours

### get_all_staff()
- Retrieves all staff assigned to the department

### get_available_staff()
- Filters staff available for appointments

### is_adequately_staffed()
- Checks if available staff meets minimum requirements

### assign_bed(is_icu=False)
- Assigns a bed to a patient, raises error if none available

### release_bed(is_icu=False)
- Releases a bed, ensuring occupancy doesn't go negative

### update_staff_count()
- Updates current staff count based on available staff

### declare_emergency(reason)
- Creates an emergency entry, doubling staff requirement

## Relationships
- `hospital`: ManyToOne relationship with `Hospital`
- `head_doctor` and `assistant_head`: ForeignKey to `Doctor` model

## Validation
- Ensures data consistency and integrity through `clean()` method

## Indexes
- `code` and `department_type` fields are indexed for efficient queries

## Metadata
- `unique_together` constraint on `hospital` and `name`
- Ordered by `name` for consistent listing

## Examples

### Creating a Department
```python
hospital = Hospital.objects.get(id=1)
department = Department.objects.create(
    hospital=hospital,
    name='Emergency Department',
    department_type='emergency',
    code='EMERG001',
    floor_number='2',
    wing='West Wing',
    extension_number='2345',
    emergency_contact='1234',
    email='emergency@hospital.com',
    is_24_hours=True
)
```

### Assigning a Bed
```python
department.assign_bed()  # Assign regular bed
department.assign_bed(is_icu=True)  # Assign ICU bed
```

### Checking Availability
```python
availability = department.bed_availability
print(f"Regular Beds Available: {availability['regular_beds']['available']}")
print(f"ICU Beds Available: {availability['icu_beds']['available']}")