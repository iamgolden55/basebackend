# Appointment Flow Testing Guide 🏥

This guide explains how to test the appointment flow in the PHB Management system. The appointment flow includes creating appointments, notifications, payments, documents, and status transitions.

## 📋 Prerequisites

Before testing the appointment flow, make sure you have:

1. Set up the Django development environment
2. Created test data (hospitals, departments, doctors, etc.)
3. Fixed any import errors or dependencies

## 🚀 Testing Methods

There are three ways to test the appointment flow:

1. **Unit Tests**: Run the built-in test cases
2. **Manual Testing**: Use the provided script to test the flow programmatically
3. **API Testing**: Test the flow through the API endpoints

## 1️⃣ Running Unit Tests

The system includes unit tests for the appointment flow. To run them:

```bash
python manage.py test api.tests.test_appointment_flow
```

This will run the `AppointmentFlowTest` and `MLAppointmentFlowTest` test cases, which test:
- Creating appointments
- Generating notifications
- Processing payments
- Creating and signing documents
- Transitioning appointment status
- ML-based doctor assignment

## 2️⃣ Manual Testing with Script

We've created a script to test the appointment flow manually using the Django ORM. To run it:

```bash
python test_appointment_flow_manual.py
```

This script:
1. Creates an appointment with emergency priority
2. Generates appointment notifications
3. Creates and completes a payment transaction
4. Approves the appointment
5. Creates and signs a document
6. Transitions the appointment through different statuses

## 3️⃣ API Testing

To test the appointment flow through the API endpoints:

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Run the API test script:
   ```bash
   python test_appointment_api.py
   ```

This script uses the API endpoints to:
1. Authenticate as a patient
2. Create an appointment
3. Get appointment details
4. Update the appointment
5. Authenticate as a doctor
6. Approve the appointment
7. List all appointments

## 🔍 Appointment Flow Steps

The complete appointment flow includes:

1. **Creation**: Patient creates an appointment with a doctor
2. **Notification**: System sends notifications to patient and doctor
3. **Payment**: Patient makes a payment for the appointment
4. **Approval**: Doctor approves the appointment
5. **Documentation**: Doctor creates documents (prescriptions, etc.)
6. **Signature**: Patient signs the documents
7. **Execution**: Appointment is marked as in progress
8. **Completion**: Appointment is marked as completed

## 🛠️ Troubleshooting

If you encounter issues during testing:

- **Import Errors**: Make sure all required packages are installed
  ```bash
  pip install -r requirements.txt
  ```

- **Availability Errors**: Set appointment priority to 'emergency' to bypass availability checks
  - In the API, you may still get availability errors even with emergency priority
  - This is a known issue with the API validation
  - Use the manual testing script instead, which correctly handles emergency priority

- **API Validation Errors**: The API has stricter validation than the manual script
  - If you get "Doctor is not available at the requested time" errors, use the manual script
  - The issue is related to how the API validates doctor availability

- **Document Errors**: Ensure you provide a file when creating appointment documents

- **Unique Constraint Errors**: Generate unique IDs for appointments and transactions

## 📊 Expected Results

A successful appointment flow test should:

1. Create an appointment with a valid ID
2. Generate multiple notifications
3. Create and complete a payment transaction
4. Allow document creation and signing
5. Successfully transition through all appointment statuses

## 🔄 Next Steps

After testing the appointment flow, you can:

1. Implement additional features (rescheduling, cancellation, etc.)
2. Improve the ML doctor assignment algorithm
3. Enhance the notification system
4. Add more payment providers
5. Create a comprehensive frontend for the appointment flow 