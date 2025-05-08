# Medical Records Access Tools

This package contains three Python scripts to help you access and analyze medical records in the system. Each script provides a different way to retrieve and display medical record information.

## Quick Start

1. Make sure your Python environment is set up with the required dependencies
2. Run the scripts from the command line as shown below

## Available Scripts

### 1. Get Medical Records by HPN

Retrieves detailed information for a specific medical record using the Healthcare Provider Number (HPN).

```bash
# List all available HPN numbers
python get_medical_records_by_hpn.py --list

# Get details for a specific HPN
python get_medical_records_by_hpn.py "POR 283 451 5806"
```

### 2. Get All Medical Records

Retrieves all medical records in the system with various output options.

```bash
# View basic list of all records
python get_all_medical_records.py

# View summary information only
python get_all_medical_records.py --summary

# Export all records to a JSON file
python get_all_medical_records.py --output records.json
```

### 3. Find Medical Records

Search for medical records by patient name, email, ID, or HPN.

```bash
# Search by patient name
python find_medical_record.py "Mohammed"

# Search by email fragment
python find_medical_record.py "mohammed.1732"

# Search by HPN
python find_medical_record.py "KAD 226 553 8139"

# Search by user ID (if known)
python find_medical_record.py "552"
```

## Output Formats

The scripts provide information in several formats:

1. **Console Output**: Formatted text displayed in the terminal
2. **JSON Export**: Complete data saved to a file (with `--output` option)
3. **Markdown Summary**: Overview of the system in `medical_records_summary.md`

## Medical Record Structure

Each medical record contains:

- **Basic Information**: HPN, patient details, blood type
- **Medical History**: Diagnoses, treatments, doctor interactions
- **Risk Assessment**: Flags for high-risk patients and complexity metrics

## Notes

- The system contains 1483 medical records
- Most records have minimal data with empty diagnoses and treatments fields
- Records are organized with regional prefixes (ABU, KAD, POR, etc.)
- Patient privacy is maintained through anonymization capabilities

For a comprehensive overview of the medical records system, see `medical_records_summary.md`. 