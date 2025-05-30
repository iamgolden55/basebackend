# Hospital Creation and Registration Guide

## Overview

This document outlines the complete process for creating hospitals in the system, including required fields, department setup, admin account creation, and security features.

## Hospital Creation Methods

There are two primary methods for creating hospitals in the system:

1. **Direct Database Creation** (via scripts or Django ORM)
   - Used primarily for system initialization or testing
   - Creates hospital entities directly using Django models
   - Example: `create_hospital_data.py` or `create_abuja_hospital_fixed.py`

2. **API-based Registration** (via web interface or API endpoints)
   - Used for production hospital onboarding
   - Follows the secure registration and approval flow
   - Requires admin validation
   - Example: Using the `/api/hospitals/register/` endpoint

## Required Fields for Hospital Creation

### Essential Fields (Required)

| Field             | Type      | Description                            | Validation                        |
|-------------------|-----------|----------------------------------------|-----------------------------------|
| `name`            | CharField | Hospital name                          | Required, max 200 chars           |
| `address`         | TextField | Physical address                       | Required                          |
| `hospital_type`   | CharField | Type of hospital                       | Required, choice from predefined list |
| `city`            | CharField | City location                          | Required                          |
| `state`           | CharField | State/province                         | Required                          |
| `country`         | CharField | Country                                | Required                          |
| `email`           | EmailField| Contact email for notifications        | Required, valid email format      |

### Optional but Recommended Fields

| Field             | Type      | Description                            |
|-------------------|-----------|----------------------------------------|
| `registration_number` | CharField | Hospital registration code (auto-generated if not provided) |
| `postal_code`     | CharField | ZIP/Postal code                        |
| `phone`           | CharField | Contact phone number                   |
| `website`         | URLField  | Hospital website                       |
| `emergency_unit`  | BooleanField | Whether hospital has emergency services |
| `icu_unit`        | BooleanField | Whether hospital has ICU facilities |

## Department Requirements

Each hospital must have at least one department. Departments have these key requirements:

1. **Minimum Staff Count**: Each department must have `current_staff_count` >= `minimum_staff_required`
2. **Unique Department Codes**: Each department must have a unique code within the hospital
3. **Required Fields**:
   - `name`: Department name
   - `code`: Unique department code
   - `description`: Department description
   - `current_staff_count`: Number of staff (must meet minimum)
   - `minimum_staff_required`: Minimum required staff (default: 1)
   - `hospital`: Foreign key to the parent Hospital

## Hospital Admin Creation Process

When a new hospital is created, an administrator account is automatically generated:

1. **CustomUser Creation**:
   - Creates a user with role 'hospital_admin'
   - Sets appropriate permissions (is_staff=True)
   - Generates secure credentials
   - Sets email verification to True

2. **HospitalAdmin Creation**:
   - Links the admin to both the hospital and user account
   - Sets position and name
   - Requires password change on first login
   - Stores real contact email for notifications

3. **Security Email Generation**:
   - **Login Email**: A standardized but difficult-to-guess format (`admin.hospitalname@example.com`)
   - **Contact Email**: The real email address for receiving communications

4. **Registration Number**:
   - A unique code is generated for the hospital (format: `H-{random_hex}`)
   - Used for admin verification during the secure login process

## Automated Hospital Admin Setup

The system includes a management command for setting up admin accounts:

```bash
python manage.py setup_hospital_admins [--force] [--prefix admin] [--password Password123!]
```

This command:
- Processes all hospitals without admin accounts
- Generates appropriate credentials
- Creates standardized admin accounts
- Ensures registration numbers exist

## Security Features for Hospital Admins

1. **Secure Login Flow**:
   - Domain validation for hospital email addresses
   - Required hospital code verification (using registration_number)
   - Mandatory 2FA for all hospital admins
   - Enhanced security with trusted device tracking

2. **Additional Security**:
   - Rate limiting: IP-based rate limiting after 3 failed attempts
   - Account lockout: Account lockout for 15 minutes after 5 failed attempts
   - Suspicious login notifications: Email alerts sent after 3 failed login attempts
   - Password reset unlocking: Account lockout is automatically cleared after successful password reset
   - Detailed security logging: Comprehensive logging of security events

## API-based Hospital Registration Flow

For hospital registration through the API:

1. **Initial Registration**:
   - Hospital entity is created with basic information
   - Registration status is set to 'pending'

2. **Department Setup**:
   - Required departments are created
   - Staff counts are set appropriately

3. **Admin Registration**:
   - System generates a secure admin account
   - Welcome email is sent to the real contact email

4. **Verification Process**:
   - Admin may need to complete email verification
   - Hospital verification is performed by system administrators
   - Once verified, `is_verified` flag is set to True

## Testing Hospital Creation

To test hospital creation, use the provided scripts:

```bash
# Create a sample hospital with admin
python create_hospital_data.py

# Create specific hospital (e.g., Abuja General Hospital)
python create_abuja_hospital_fixed.py
```

## Troubleshooting

### Common Issues

1. **Department Creation Failures**:
   - Ensure each department has sufficient staff count
   - Check for duplicate department codes

2. **Admin Creation Failures**:
   - Ensure all required fields are provided (including preferred_language)
   - Verify the contact email is valid

3. **Registration Number Issues**:
   - If registration number is missing, it can be generated using the setup_hospital_admins command

## Best Practices

1. Always ensure real, valid email addresses are used for contact_email
2. Set appropriate staff counts for departments to meet minimum requirements
3. For production, use strong, unique passwords for admin accounts
4. Keep hospital registration numbers secure
5. Ensure hospital types match the predefined choices

---

*This documentation is maintained by the development team. Last updated: May 28, 2025*
