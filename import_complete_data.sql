-- Complete sample data import script with all required fields
BEGIN;

-- Add sample departments with all required fields
INSERT INTO api_department (name, hospital_id, code, description, created_at, updated_at, department_type) VALUES
('Emergency', 1, 'EMER', 'Emergency Department', NOW(), NOW(), 'emergency'),
('Cardiology', 1, 'CARD', 'Cardiology Department', NOW(), NOW(), 'specialty'),
('Neurology', 1, 'NEUR', 'Neurology Department', NOW(), NOW(), 'specialty'),
('Pediatrics', 1, 'PEDS', 'Pediatrics Department', NOW(), NOW(), 'specialty'),
('Orthopedics', 1, 'ORTH', 'Orthopedics Department', NOW(), NOW(), 'specialty'),
('Obstetrics & Gynecology', 1, 'OBGY', 'Obstetrics & Gynecology Department', NOW(), NOW(), 'specialty'),
('Internal Medicine', 1, 'INTM', 'Internal Medicine Department', NOW(), NOW(), 'specialty'),
('Surgery', 1, 'SURG', 'Surgery Department', NOW(), NOW(), 'specialty'),
('Radiology', 1, 'RADI', 'Radiology Department', NOW(), NOW(), 'diagnostic'),
('Pharmacy', 1, 'PHAR', 'Pharmacy Department', NOW(), NOW(), 'support');

-- Add sample doctors with all required fields
INSERT INTO api_doctor (created_at, updated_at, first_name, last_name, email, phone, specialty, hospital_id, status, license_number, gender) VALUES
(NOW(), NOW(), 'John', 'Smith', 'john.smith@hospital.com', '+1234567890', 'Cardiology', 1, 'active', 'MD12345', 'male'),
(NOW(), NOW(), 'Jane', 'Doe', 'jane.doe@hospital.com', '+1234567891', 'Neurology', 1, 'active', 'MD12346', 'female'),
(NOW(), NOW(), 'Michael', 'Johnson', 'michael.johnson@hospital.com', '+1234567892', 'Pediatrics', 1, 'active', 'MD12347', 'male'),
(NOW(), NOW(), 'Sarah', 'Williams', 'sarah.williams@hospital.com', '+1234567893', 'Orthopedics', 1, 'active', 'MD12348', 'female'),
(NOW(), NOW(), 'Robert', 'Brown', 'robert.brown@hospital.com', '+1234567894', 'Surgery', 1, 'active', 'MD12349', 'male'),
(NOW(), NOW(), 'Emily', 'Jones', 'emily.jones@hospital.com', '+1234567895', 'Obstetrics', 1, 'active', 'MD12350', 'female'),
(NOW(), NOW(), 'David', 'Miller', 'david.miller@hospital.com', '+1234567896', 'Internal Medicine', 1, 'active', 'MD12351', 'male'),
(NOW(), NOW(), 'Jennifer', 'Davis', 'jennifer.davis@hospital.com', '+1234567897', 'Emergency Medicine', 1, 'active', 'MD12352', 'female'),
(NOW(), NOW(), 'James', 'Wilson', 'james.wilson@hospital.com', '+1234567898', 'Radiology', 1, 'active', 'MD12353', 'male'),
(NOW(), NOW(), 'Linda', 'Moore', 'linda.moore@hospital.com', '+1234567899', 'Anesthesiology', 1, 'active', 'MD12354', 'female');

-- Add sample medications (if medical_record_id exists)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM api_medicalrecord LIMIT 1) THEN
    INSERT INTO api_medication (created_at, updated_at, name, dose, frequency, start_date, end_date, instructions, medical_record_id, is_active) VALUES
    (NOW(), NOW(), 'Lisinopril', '10mg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take with water in the morning', 1, true),
    (NOW(), NOW(), 'Atorvastatin', '20mg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take with evening meal', 1, true);
  END IF;
END
$$;

-- Fix sequences
SELECT setval('public.api_customuser_id_seq', COALESCE((SELECT MAX(id) FROM api_customuser), 1), true);
SELECT setval('public.api_hospital_id_seq', COALESCE((SELECT MAX(id) FROM api_hospital), 1), true);
SELECT setval('public.api_department_id_seq', COALESCE((SELECT MAX(id) FROM api_department), 1), true);
SELECT setval('public.api_doctor_id_seq', COALESCE((SELECT MAX(id) FROM api_doctor), 1), true);
SELECT setval('public.api_medicalrecord_id_seq', COALESCE((SELECT MAX(id) FROM api_medicalrecord), 1), true);
SELECT setval('public.api_medication_id_seq', COALESCE((SELECT MAX(id) FROM api_medication), 1), true);

COMMIT;
