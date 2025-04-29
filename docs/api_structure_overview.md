# API Folder Structure Overview

Welcome to the backend API codebase! This document provides a high-level overview of the `api/` folder to help new developers quickly understand the structure, responsibilities, and how the main components connect. This will help you find where to add new features, fix bugs, or write tests.

---

## Main Components

### 1. `models/`
- **Purpose:** Contains all the database models representing the core entities of the system (users, hospitals, appointments, doctors, departments, notifications, payments, etc.).
- **Structure:**
  - Organized into subfolders by domain (e.g., `medical/`, `user/`, `medical_staff/`, `notifications/`, `payment_providers/`).
  - Each file defines Django ORM models for a specific concept (e.g., `hospital.py`, `appointment.py`, `doctor.py`).
  - The `__init__.py` file imports all models for easy access throughout the project.
- **How it connects:** Models are the foundation for serializers and are used in views to query and manipulate data.

### 2. `views.py`
- **Purpose:** Contains the API endpoint logic (controllers in MVC terms). Handles HTTP requests, applies business logic, and returns responses.
- **Structure:**
  - Defines class-based and function-based views for user registration, login, hospital registration, appointment management, etc.
  - Uses Django REST Framework (DRF) generics, viewsets, and APIView classes.
- **How it connects:**
  - Imports models to read/write data.
  - Uses serializers to validate and transform data between Python objects and JSON.
  - Connected to URLs via `urls.py`.

### 3. `serializers.py`
- **Purpose:** Defines how model instances are converted to and from JSON for API requests and responses.
- **Structure:**
  - Contains DRF `ModelSerializer` and `Serializer` classes for each major model (e.g., `UserSerializer`, `AppointmentSerializer`, `HospitalSerializer`).
  - Handles validation, custom fields, and complex data transformations.
- **How it connects:**
  - Used by views to validate incoming data and serialize outgoing data.
  - Tightly coupled with models (each serializer usually maps to a model).

### 4. `urls.py`
- **Purpose:** Maps URL patterns to views, defining the API endpoints.
- **Structure:**
  - Uses DRF routers for viewsets (e.g., hospitals, appointments).
  - Explicitly defines paths for custom views (e.g., registration, login, password reset).
- **How it connects:**
  - Connects HTTP endpoints to the appropriate view logic.
  - The entry point for the API from the outside world.

### 5. `utils/`
- **Purpose:** Utility functions and helpers (e.g., email sending, location lookup, token utilities).
- **Structure:**
  - Each file provides reusable logic for a specific concern (e.g., `email.py`, `location_utils.py`).
- **How it connects:**
  - Used by views and sometimes models to perform common tasks.

### 6. `tests/`
- **Purpose:** Automated tests for API endpoints and business logic.
- **Structure:**
  - Contains test files for different flows (e.g., `test_appointment_api.py`, `test_doctor_assignment.py`).
  - Uses Django's and DRF's test frameworks.
- **How it connects:**
  - Ensures the correctness of views, models, and serializers.

### 7. `admin.py`
- **Purpose:** Django admin configuration for managing models via the admin interface.
- **How it connects:**
  - Registers models and customizes their admin display and permissions.

### 8. `permissions.py`
- **Purpose:** Custom permission classes for DRF to control access to endpoints (e.g., `IsMedicalStaff`, `IsPatient`).
- **How it connects:**
  - Used in views to restrict access based on user roles or other logic.

### 9. `middleware/`
- **Purpose:** Custom Django middleware for cross-cutting concerns (e.g., payment security).
- **How it connects:**
  - Applied at the request/response level for all or specific endpoints.

### 10. `management/`
- **Purpose:** Custom Django management commands for tasks like evaluating doctor assignment or running test scenarios.
- **How it connects:**
  - Run from the command line for maintenance, data import/export, or analytics.

### 11. `templates/`
- **Purpose:** Email templates and other HTML templates used for notifications.
- **Structure:**
  - Organized by type (e.g., `email/` for all email-related templates).
- **How it connects:**
  - Used by utility functions and views to render dynamic email content.

---

## How Everything Connects

- **Models** define the data structure and business rules.
- **Serializers** translate between model instances and JSON for the API.
- **Views** handle HTTP requests, use serializers for validation, and interact with models for data.
- **URLs** map incoming requests to the correct view.
- **Utils** provide shared logic for use across views, models, and serializers.
- **Tests** ensure all the above work as expected.

---

## Where to Add or Change Code
- **New data structure?** Add a model in `models/`, a serializer in `serializers.py`, and endpoints in `views.py` and `urls.py`.
- **New API endpoint?** Add a view in `views.py`, a serializer if needed, and map it in `urls.py`.
- **Business logic?** Usually in views or models, sometimes in utils.
- **Permissions?** Add to `permissions.py` and use in your views.
- **Admin interface?** Update `admin.py`.
- **Automated tests?** Add to `tests/`.

---

## Tips for New Developers
- Start by reading the model for the entity you want to work with.
- Check the corresponding serializer and view for how data flows.
- Use the tests as examples for how endpoints are expected to behave.
- Follow existing patterns for consistency.

---

For more details, see the code comments and docstrings in each file. Welcome to the team! 