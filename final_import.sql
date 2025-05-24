-- Final complete sample data import script with all required fields
BEGIN;

-- Add sample departments with all required fields
INSERT INTO api_department (name, hospital_id, code, description, created_at, updated_at, department_type, is_active) VALUES
('Emergency', 1, 'EMER', 'Emergency Department', NOW(), NOW(), 'emergency', true),
('Cardiology', 1, 'CARD', 'Cardiology Department', NOW(), NOW(), 'specialty', true),
('Neurology', 1, 'NEUR', 'Neurology Department', NOW(), NOW(), 'specialty', true),
('Pediatrics', 1, 'PEDS', 'Pediatrics Department', NOW(), NOW(), 'specialty', true),
('Orthopedics', 1, 'ORTH', 'Orthopedics Department', NOW(), NOW(), 'specialty', true),
('Obstetrics & Gynecology', 1, 'OBGY', 'Obstetrics & Gynecology Department', NOW(), NOW(), 'specialty', true),
('Internal Medicine', 1, 'INTM', 'Internal Medicine Department', NOW(), NOW(), 'specialty', true),
('Surgery', 1, 'SURG', 'Surgery Department', NOW(), NOW(), 'specialty', true),
('Radiology', 1, 'RADI', 'Radiology Department', NOW(), NOW(), 'diagnostic', true),
('Pharmacy', 1, 'PHAR', 'Pharmacy Department', NOW(), NOW(), 'support', true);

-- Add sample doctors with all required fields
INSERT INTO api_doctor (created_at, updated_at, first_name, last_name, email, phone, specialty, hospital_id, status, license_number, gender, is_verified) VALUES
(NOW(), NOW(), 'John', 'Smith', 'john.smith@hospital.com', '+1234567890', 'Cardiology', 1, 'active', 'MD12345', 'male', true),
(NOW(), NOW(), 'Jane', 'Doe', 'jane.doe@hospital.com', '+1234567891', 'Neurology', 1, 'active', 'MD12346', 'female', true),
(NOW(), NOW(), 'Michael', 'Johnson', 'michael.johnson@hospital.com', '+1234567892', 'Pediatrics', 1, 'active', 'MD12347', 'male', true),
(NOW(), NOW(), 'Sarah', 'Williams', 'sarah.williams@hospital.com', '+1234567893', 'Orthopedics', 1, 'active', 'MD12348', 'female', true),
(NOW(), NOW(), 'Robert', 'Brown', 'robert.brown@hospital.com', '+1234567894', 'Surgery', 1, 'active', 'MD12349', 'male', true),
(NOW(), NOW(), 'Emily', 'Jones', 'emily.jones@hospital.com', '+1234567895', 'Obstetrics', 1, 'active', 'MD12350', 'female', true),
(NOW(), NOW(), 'David', 'Miller', 'david.miller@hospital.com', '+1234567896', 'Internal Medicine', 1, 'active', 'MD12351', 'male', true),
(NOW(), NOW(), 'Jennifer', 'Davis', 'jennifer.davis@hospital.com', '+1234567897', 'Emergency Medicine', 1, 'active', 'MD12352', 'female', true),
(NOW(), NOW(), 'James', 'Wilson', 'james.wilson@hospital.com', '+1234567898', 'Radiology', 1, 'active', 'MD12353', 'male', true),
(NOW(), NOW(), 'Linda', 'Moore', 'linda.moore@hospital.com', '+1234567899', 'Anesthesiology', 1, 'active', 'MD12354', 'female', true);

-- Fix sequences
SELECT setval('public.api_customuser_id_seq', COALESCE((SELECT MAX(id) FROM api_customuser), 1), true);
SELECT setval('public.api_hospital_id_seq', COALESCE((SELECT MAX(id) FROM api_hospital), 1), true);
SELECT setval('public.api_department_id_seq', COALESCE((SELECT MAX(id) FROM api_department), 1), true);
SELECT setval('public.api_doctor_id_seq', COALESCE((SELECT MAX(id) FROM api_doctor), 1), true);
SELECT setval('public.api_medicalrecord_id_seq', COALESCE((SELECT MAX(id) FROM api_medicalrecord), 1), true);
SELECT setval('public.api_medication_id_seq', COALESCE((SELECT MAX(id) FROM api_medication), 1), true);

COMMIT;
