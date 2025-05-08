# Medical Records Summary

## Overview
This document provides a comprehensive summary of all medical records in the system. The records are identified by unique Healthcare Provider Number (HPN) and linked to patients.

## System Statistics
- **Total Medical Records**: 1483
- **HPN Prefix Distribution**: ABU, AKW, ASA, BOR, DEL, EDO, ENU, KAD, KAN, LAG, OYO, PLA, POR, RIV, UNK

## Sample Record Structure
Each medical record contains:
- **Patient Information**: HPN, patient name, ID
- **Medical Details**: Blood type, allergies, chronic conditions
- **Emergency Contact**: Name and phone
- **Risk Assessment**: High risk flag, complexity metrics
- **Medical History**:
  - Diagnoses with ICD-10 codes
  - Treatments (medications, procedures, etc.)
  - Doctor interactions

## Data Observations
From examining the records, we found:
1. Most records contain minimal data, with empty fields for diagnoses and treatments
2. Patient names follow a common pattern (Nigerian names)
3. Records are organized by regional prefixes (KAD, POR, ABU, etc.) suggesting geographical distribution
4. The system includes anonymous records (prefix UNK)

## How to Access Records
Three scripts are available to access the medical records:

1. **get_medical_records_by_hpn.py**
   - Gets detailed information for a specific record
   - Usage: `python get_medical_records_by_hpn.py [HPN]`
   - List all HPNs: `python get_medical_records_by_hpn.py --list`

2. **get_all_medical_records.py**
   - Retrieves all medical records in the system
   - Basic usage: `python get_all_medical_records.py`
   - Summary only: `python get_all_medical_records.py --summary`
   - Save to file: `python get_all_medical_records.py --output records.json`

3. **find_medical_record.py**
   - Searches for records by patient name, email, ID, or HPN
   - Usage: `python find_medical_record.py [search term]`

## Record Field Descriptions

### Main Record Fields
| Field | Description |
|-------|-------------|
| hpn | Healthcare Provider Number (unique identifier) |
| patient_id | User ID linked to the record (may be "Anonymous") |
| patient_name | Full name of the patient |
| blood_type | Patient's blood type (A+, B-, etc.) |
| allergies | Known allergies |
| chronic_conditions | Ongoing medical conditions |
| is_high_risk | Flag for patients requiring special attention |
| last_visit_date | Date of most recent medical visit |

### Complexity Metrics
| Metric | Description |
|--------|-------------|
| comorbidity_count | Number of concurrent diagnoses |
| hospitalization_count | Number of hospital admissions |
| last_hospitalization_date | Date of most recent hospitalization |
| care_plan_complexity | Complexity score (0-10 scale) |
| medication_count | Number of active medications |

### Related Records
Each medical record can have multiple associated:
- **Diagnoses**: With ICD-10 codes, severity, chronicity flags
- **Treatments**: Including medications, procedures, surgeries
- **Doctor Interactions**: Appointments, consultations, follow-ups

## Data Privacy Notes
- Records can be anonymized using the `anonymize_record()` method
- Anonymized records retain medical data but disconnect from user identity
- The system implements security measures including OTP verification for access

## Complete Data Export
A complete export of all medical records has been saved to `medical_records.json` 