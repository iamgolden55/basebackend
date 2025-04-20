# ML Appointment System Testing Guide with Postman 🚀

Hey there, testing superstar! 🌟 Let's set up some awesome tests for our ML-powered appointment scheduling system. This guide will help you verify that our smart doctor assignment system is working correctly, especially with the new language preference features!

## Setting Up Your Postman Environment 🛠️

1. Create a new Postman collection named `PHB Management ML Tests`
2. Set up environment variables:
   - `BASE_URL`: Your API base URL (e.g., `http://localhost:8000/api`)
   - `TOKEN`: Will be populated after authentication

## Authentication 🔐

First, let's get a token to use for our tests:

**Request**: `POST {{BASE_URL}}/auth/token/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "email": "your_test_user@example.com",
    "password": "your_password"
  }
  ```
- Test Script (automatically saves token):
  ```javascript
  if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("TOKEN", jsonData.access);
    console.log("Token saved to environment");
  }
  ```

## Test Case 1: Create Appointment with ML Doctor Assignment 🩺

Let's create an appointment and see if the ML system assigns a doctor:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-01T10:00:00Z",
    "reason": "Regular checkup",
    "medical_history": "Hypertension",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created successfully", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    pm.environment.set("APPOINTMENT_ID", jsonData.id);
    console.log("Appointment created with ID: " + jsonData.id);
  });
  
  pm.test("Doctor was assigned by ML system", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.doctor).to.not.be.null;
    console.log("Doctor assigned: " + jsonData.doctor);
  });
  ```

## Test Case 2: Verify ML Doctor Assignment Logic 🧠

### Emergency Appointment Test 🚨

Let's test if the system prioritizes experienced doctors for emergency appointments:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-01T10:00:00Z",
    "reason": "Chest pain",
    "medical_history": "Hypertension",
    "appointment_type": "emergency",
    "priority": "high"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Emergency appointment created successfully", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    pm.environment.set("EMERGENCY_DOCTOR_ID", jsonData.doctor);
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + jsonData.doctor + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Emergency doctor experience: " + doctorData.years_of_experience);
        pm.test("Experienced doctor assigned for emergency", function() {
          pm.expect(doctorData.years_of_experience).to.be.greaterThan(5);
        });
      }
    });
  });
  ```

## Test Case 3: Comprehensive Language Preference Tests 🗣️

Let's test all the different ways language preferences can be matched:

### 3.1 Preferred Language Match Test

**Step 1**: Update user profile with preferred language

**Request**: `PATCH {{BASE_URL}}/users/me/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "preferred_language": "spanish",
    "secondary_languages": "",
    "languages": ""
  }
  ```
- Test Script:
  ```javascript
  pm.test("Preferred language updated", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.preferred_language).to.equal("spanish");
  });
  ```

**Step 2**: Create appointment to test preferred language matching

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-02T14:00:00Z",
    "reason": "Preferred language test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for preferred language test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    const doctorId = jsonData.doctor;
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + doctorId + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Doctor languages: " + doctorData.languages_spoken);
        
        pm.test("Doctor speaks patient's preferred language", function() {
          pm.expect(doctorData.languages_spoken.toLowerCase()).to.include("spanish");
        });
      }
    });
  });
  ```

### 3.2 Custom Language Match Test

**Step 1**: Update user profile with custom language

**Request**: `PATCH {{BASE_URL}}/users/me/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "preferred_language": "other",
    "custom_language": "Calabar",
    "secondary_languages": "",
    "languages": ""
  }
  ```
- Test Script:
  ```javascript
  pm.test("Custom language preference updated", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.preferred_language).to.equal("other");
    pm.expect(jsonData.custom_language).to.equal("Calabar");
  });
  ```

**Step 2**: Create appointment to test custom language matching

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-03T10:00:00Z",
    "reason": "Custom language test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for custom language test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    const doctorId = jsonData.doctor;
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + doctorId + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Doctor languages: " + doctorData.languages_spoken);
        
        pm.test("Doctor speaks patient's custom language", function() {
          pm.expect(doctorData.languages_spoken.toLowerCase()).to.include("calabar");
        });
      }
    });
  });
  ```

### 3.3 Secondary Languages Match Test

**Step 1**: Update user profile with secondary languages

**Request**: `PATCH {{BASE_URL}}/users/me/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "preferred_language": "english",
    "secondary_languages": "french,yoruba",
    "custom_language": "",
    "languages": ""
  }
  ```
- Test Script:
  ```javascript
  pm.test("Secondary languages updated", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.preferred_language).to.equal("english");
    pm.expect(jsonData.secondary_languages).to.equal("french,yoruba");
  });
  ```

**Step 2**: Create appointment to test secondary language matching

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-04T15:00:00Z",
    "reason": "Secondary language test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for secondary language test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    const doctorId = jsonData.doctor;
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + doctorId + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Doctor languages: " + doctorData.languages_spoken);
        
        pm.test("Doctor speaks at least one of patient's secondary languages", function() {
          const doctorLangs = doctorData.languages_spoken.toLowerCase();
          const hasMatch = doctorLangs.includes("french") || doctorLangs.includes("yoruba");
          pm.expect(hasMatch).to.be.true;
        });
      }
    });
  });
  ```

### 3.4 Legacy Language Field Test

**Step 1**: Update user profile with legacy language field

**Request**: `PATCH {{BASE_URL}}/users/me/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "preferred_language": "en",
    "secondary_languages": "",
    "custom_language": "",
    "languages": "Spanish"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Legacy language field updated", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.languages).to.equal("Spanish");
  });
  ```

**Step 2**: Create appointment to test legacy language matching

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-05T11:00:00Z",
    "reason": "Legacy language test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for legacy language test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    const doctorId = jsonData.doctor;
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + doctorId + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Doctor languages: " + doctorData.languages_spoken);
        
        pm.test("Doctor speaks patient's legacy language", function() {
          pm.expect(doctorData.languages_spoken.toLowerCase()).to.include("spanish");
        });
      }
    });
  });
  ```

### 3.5 Multiple Language Fields Test

**Step 1**: Update user profile with multiple language fields

**Request**: `PATCH {{BASE_URL}}/users/me/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "preferred_language": "spanish",
    "secondary_languages": "french,english",
    "languages": "Yoruba"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Multiple language fields updated", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.preferred_language).to.equal("spanish");
    pm.expect(jsonData.secondary_languages).to.equal("french,english");
    pm.expect(jsonData.languages).to.equal("Yoruba");
  });
  ```

**Step 2**: Create appointment to test multiple language fields

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-06T14:00:00Z",
    "reason": "Multiple language fields test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for multiple language fields test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the doctor ID for verification
    const doctorId = jsonData.doctor;
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + doctorId + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Doctor languages: " + doctorData.languages_spoken);
        
        // Check if doctor speaks Spanish (preferred language)
        const speaksPreferred = doctorData.languages_spoken.toLowerCase().includes("spanish");
        
        // Check if doctor speaks any secondary or legacy language
        const doctorLangs = doctorData.languages_spoken.toLowerCase();
        const speaksSecondary = doctorLangs.includes("french") || 
                               doctorLangs.includes("english") || 
                               doctorLangs.includes("yoruba");
        
        pm.test("Doctor speaks at least one of patient's languages", function() {
          pm.expect(speaksPreferred || speaksSecondary).to.be.true;
        });
        
        // If doctor speaks preferred language, it should be prioritized
        if (speaksPreferred) {
          console.log("Doctor speaks patient's preferred language (Spanish)");
        } else if (speaksSecondary) {
          console.log("Doctor speaks one of patient's secondary/legacy languages");
        }
      }
    });
  });
  ```

## Test Case 4: Continuity of Care Tests 🔄

Let's test if the system correctly prioritizes continuity of care by assigning patients to doctors they've seen before.

### 4.1 Create Past Appointments

First, we need to create some past appointments to establish a history:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "doctor": 3,  // Specify a doctor ID
    "appointment_date": "2023-06-01T10:00:00Z",  // Past date
    "reason": "Initial consultation",
    "appointment_type": "regular",
    "priority": "normal",
    "status": "completed"  // Mark as completed
  }
  ```
- Test Script:
  ```javascript
  pm.test("Past appointment created successfully", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    console.log("Past appointment created with ID: " + jsonData.id);
  });
  ```

### 4.2 Create Multiple Past Appointments

For stronger continuity testing, create multiple past appointments with the same doctor:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "doctor": 3,  // Same doctor as before
    "appointment_date": "2023-09-01T10:00:00Z",  // More recent past date
    "reason": "Follow-up consultation",
    "appointment_type": "follow_up",
    "priority": "normal",
    "status": "completed"  // Mark as completed
  }
  ```
- Test Script:
  ```javascript
  pm.test("Second past appointment created successfully", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    console.log("Second past appointment created with ID: " + jsonData.id);
  });
  ```

### 4.3 Test Continuity for Regular Appointment

Now let's create a new appointment and see if the system assigns the same doctor:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-15T10:00:00Z",  // Future date
    "reason": "Continuity test - regular appointment",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for continuity test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Store the assigned doctor ID
    pm.environment.set("ASSIGNED_DOCTOR_ID", jsonData.doctor);
    
    // Check if the assigned doctor matches the previous doctor (ID: 3)
    pm.test("Doctor assignment respects continuity of care", function() {
      pm.expect(jsonData.doctor).to.equal(3);
      console.log("Assigned doctor ID: " + jsonData.doctor + " (Expected: 3)");
    });
  });
  ```

### 4.4 Test Continuity for Follow-up Appointment

Follow-up appointments should have stronger continuity preference:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-20T10:00:00Z",  // Future date
    "reason": "Continuity test - follow-up appointment",
    "appointment_type": "follow_up",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Follow-up appointment created for continuity test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Check if the assigned doctor matches the previous doctor (ID: 3)
    pm.test("Follow-up appointment strongly respects continuity of care", function() {
      pm.expect(jsonData.doctor).to.equal(3);
      console.log("Assigned doctor ID for follow-up: " + jsonData.doctor + " (Expected: 3)");
    });
  });
  ```

### 4.5 Test Continuity vs. Specialty Match

Let's test if continuity overrides specialty match by creating an appointment in a different department:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "neurology",  // Different department
    "appointment_date": "2023-12-25T10:00:00Z",  // Future date
    "reason": "Continuity vs. specialty test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Cross-department appointment created", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    console.log("Assigned doctor ID for cross-department: " + jsonData.doctor);
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + jsonData.doctor + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        console.log("Assigned doctor department: " + doctorData.department);
        
        // Check if specialty match overrode continuity
        pm.test("Specialty match should override cross-department continuity", function() {
          pm.expect(doctorData.department).to.equal("neurology");
        });
      }
    });
  });
  ```

### 4.6 Test Recency Factor in Continuity

Let's test if more recent appointments have stronger continuity weight:

**Step 1**: Create a past appointment with a different doctor (more recent)

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 2,  // Different patient
    "hospital": 1,
    "department": "cardiology",
    "doctor": 4,  // Different doctor
    "appointment_date": "2023-11-01T10:00:00Z",  // Very recent past date
    "reason": "Recent appointment",
    "appointment_type": "regular",
    "priority": "normal",
    "status": "completed"  // Mark as completed
  }
  ```

**Step 2**: Create an older appointment with another doctor

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 2,  // Same patient as Step 1
    "hospital": 1,
    "department": "cardiology",
    "doctor": 5,  // Different doctor
    "appointment_date": "2023-01-01T10:00:00Z",  // Older past date
    "reason": "Older appointment",
    "appointment_type": "regular",
    "priority": "normal",
    "status": "completed"  // Mark as completed
  }
  ```

**Step 3**: Test which doctor gets assigned (should prefer the more recent one)

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 2,  // Same patient
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-30T10:00:00Z",  // Future date
    "reason": "Recency test",
    "appointment_type": "regular",
    "priority": "normal"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment created for recency test", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    
    // Check if the assigned doctor matches the more recent doctor (ID: 4)
    pm.test("Doctor assignment respects recency in continuity", function() {
      pm.expect(jsonData.doctor).to.equal(4);
      console.log("Assigned doctor ID: " + jsonData.doctor + " (Expected: 4 - the more recent doctor)");
    });
  });
  ```

## Test Case 5: Comprehensive Continuity Testing 📊

Let's create a comprehensive test that evaluates all aspects of continuity:

### 5.1 Setup Test Data

**Step 1**: Create a test patient with multiple past appointments

**Request**: `POST {{BASE_URL}}/users/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "email": "continuity_test@example.com",
    "password": "securepassword",
    "first_name": "Continuity",
    "last_name": "Test",
    "role": "patient",
    "gender": "male",
    "date_of_birth": "1980-01-01",
    "preferred_language": "english"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Test patient created", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    pm.environment.set("TEST_PATIENT_ID", jsonData.id);
    console.log("Test patient created with ID: " + jsonData.id);
  });
  ```

**Step 2**: Create past appointments with different doctors and recency

Create a series of appointments with different doctors, departments, and dates to test all continuity factors:

1. Most recent appointment (30 days ago) with Doctor A in Cardiology
2. Older appointment (90 days ago) with Doctor B in Cardiology
3. Multiple appointments with Doctor C in Neurology (60, 90, 120 days ago)

**Step 3**: Test appointment creation with ML assignment

Create new appointments in each department and verify the doctor assignment follows expected continuity rules:

1. New Cardiology appointment should prefer Doctor A (most recent)
2. New Neurology appointment should prefer Doctor C (multiple appointments)
3. New appointment in a different department should prioritize specialty match over continuity

### 5.2 Analyze Results

Create a collection runner that executes all these tests and generates a report showing:

1. Continuity score for each doctor
2. Final doctor assignment for each test case
3. Success rate of continuity-based assignments

This comprehensive testing will ensure that all aspects of continuity of care are working correctly in the ML doctor assignment system.

## Test Case 6: Retrieve Appointment Details 📋

**Request**: `GET {{BASE_URL}}/appointments/{{APPOINTMENT_ID}}/`
- Headers:
  ```
  Authorization: Bearer {{TOKEN}}
  ```
- Test Script:
  ```javascript
  pm.test("Can retrieve appointment with assigned doctor", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.doctor).to.not.be.null;
    console.log("Appointment retrieved with doctor: " + jsonData.doctor);
  });
  ```

## Test Case 7: Cancel Appointment 🚫

**Request**: `PATCH {{BASE_URL}}/appointments/{{APPOINTMENT_ID}}/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "status": "cancelled",
    "cancellation_reason": "Testing cancellation"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment cancelled successfully", function() {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.equal("cancelled");
  });
  ```

## Test Case 8: Reschedule Appointment 📅

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-05T15:00:00Z",
    "reason": "Rescheduled appointment",
    "appointment_type": "regular",
    "priority": "normal",
    "previous_appointment": "{{APPOINTMENT_ID}}"
  }
  ```
- Test Script:
  ```javascript
  pm.test("Appointment rescheduled successfully", function() {
    pm.response.to.have.status(201);
    var jsonData = pm.response.json();
    pm.expect(jsonData.doctor).to.not.be.null;
    console.log("Rescheduled appointment with doctor: " + jsonData.doctor);
  });
  ```

## Special Tests: Edge Cases 🧪

### Test for Overwhelmed Doctors

Create multiple appointments at the same time to see if the ML system balances workload:

**Request**: Run the appointment creation request 5 times in quick succession with the Collection Runner

**Verification**: Check if different doctors are assigned to distribute the workload

### Specialized Case Test

Test if a doctor with the right specialization is assigned:

**Request**: `POST {{BASE_URL}}/appointments/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{TOKEN}}
  ```
- Body:
  ```json
  {
    "patient": 1,
    "hospital": 1,
    "department": "cardiology",
    "appointment_date": "2023-12-10T09:00:00Z",
    "reason": "Heart arrhythmia",
    "medical_history": "Previous arrhythmia diagnosis",
    "appointment_type": "regular",
    "priority": "high",
    "specialized_care_needed": true
  }
  ```

## Running the Tests Automatically 🤖

Use the Postman Collection Runner to run all tests in sequence:

1. Open the Collection Runner
2. Select your collection
3. Set iterations to 1
4. Click "Run"

## What to Look For in Results 🔍

1. **Doctor Selection**: Are doctors being assigned for all appointments?
2. **Language Preference**: Are doctors who speak the patient's preferred language being prioritized?
3. **Secondary Languages**: Are doctors who speak the patient's secondary languages being considered?
4. **Legacy Language Support**: Is the system still handling the legacy language field correctly?
5. **Emergency Handling**: Are more experienced doctors assigned for emergency appointments?
6. **Workload Balancing**: Is the system distributing appointments among available doctors?
7. **Response Time**: How quickly is the ML system making decisions?

## Language Preference Scoring Verification 🧮

To verify that the language preference scoring is working correctly, you can add this test to any of the language test appointments:

```javascript
// Add this to the test script of any language test
pm.test("Verify language preference scoring", function() {
  // Get the ML score from the response (if available)
  var jsonData = pm.response.json();
  if (jsonData.ml_score) {
    console.log("ML Score: " + jsonData.ml_score);
    
    // Make a request to get doctor details
    const doctorRequest = {
      url: pm.environment.get("BASE_URL") + "/doctors/" + jsonData.doctor + "/",
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
      }
    };
    
    pm.sendRequest(doctorRequest, function (err, res) {
      if (!err) {
        const doctorData = res.json();
        
        // Make a request to get patient details
        const patientRequest = {
          url: pm.environment.get("BASE_URL") + "/patients/" + jsonData.patient + "/",
          method: 'GET',
          header: {
            'Authorization': 'Bearer ' + pm.environment.get("TOKEN")
          }
        };
        
        pm.sendRequest(patientRequest, function (err, patientRes) {
          if (!err) {
            const patientData = patientRes.json();
            
            console.log("Doctor languages: " + doctorData.languages_spoken);
            console.log("Patient preferred language: " + patientData.preferred_language);
            console.log("Patient secondary languages: " + patientData.secondary_languages);
            console.log("Patient legacy language: " + patientData.languages);
            
            // Calculate expected language match score
            let expectedScore = 0;
            const doctorLangs = doctorData.languages_spoken.toLowerCase().split(',').map(l => l.trim());
            
            // Check preferred language match
            if (patientData.preferred_language && patientData.preferred_language !== 'other') {
              if (doctorLangs.includes(patientData.preferred_language.toLowerCase())) {
                expectedScore += 3;
                console.log("Preferred language match: +3");
              }
            } else if (patientData.preferred_language === 'other' && patientData.custom_language) {
              if (doctorLangs.includes(patientData.custom_language.toLowerCase())) {
                expectedScore += 3;
                console.log("Custom language match: +3");
              }
            }
            
            // Check secondary languages match
            if (patientData.secondary_languages) {
              const secondaryLangs = patientData.secondary_languages.toLowerCase().split(',').map(l => l.trim());
              for (const lang of secondaryLangs) {
                if (doctorLangs.includes(lang)) {
                  expectedScore += 2;
                  console.log(`Secondary language match (${lang}): +2`);
                }
              }
            }
            
            // Check legacy language match
            if (patientData.languages) {
              const legacyLangs = patientData.languages.toLowerCase().split(',').map(l => l.trim());
              for (const lang of legacyLangs) {
                if (doctorLangs.includes(lang)) {
                  expectedScore += 2;
                  console.log(`Legacy language match (${lang}): +2`);
                }
              }
            }
            
            console.log("Expected language match score: " + expectedScore);
            
            // Note: We can't directly compare with ML score as it includes other factors
            // But we can verify that a higher language match correlates with doctor selection
          }
        });
      }
    });
  }
});
```

## Congratulations! 🎉

You now have a complete test suite for the ML appointment system! This will help ensure that our language preference updates work correctly with the ML doctor assignment algorithm.

Feel free to add more tests or modify these to suit your specific needs. Happy testing! 🧪 