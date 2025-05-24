-- Fixed sample data import script generated from backup
BEGIN;

-- Add sample departments with proper timestamps
INSERT INTO api_department (name, hospital_id, code, description, created_at, updated_at) VALUES
('Emergency', 1, 'EMER', 'Emergency Department', NOW(), NOW()),
('Cardiology', 1, 'CARD', 'Cardiology Department', NOW(), NOW()),
('Neurology', 1, 'NEUR', 'Neurology Department', NOW(), NOW()),
('Pediatrics', 1, 'PEDS', 'Pediatrics Department', NOW(), NOW()),
('Orthopedics', 1, 'ORTH', 'Orthopedics Department', NOW(), NOW()),
('Obstetrics & Gynecology', 1, 'OBGY', 'Obstetrics & Gynecology Department', NOW(), NOW()),
('Internal Medicine', 1, 'INTM', 'Internal Medicine Department', NOW(), NOW()),
('Surgery', 1, 'SURG', 'Surgery Department', NOW(), NOW()),
('Radiology', 1, 'RADI', 'Radiology Department', NOW(), NOW()),
('Pharmacy', 1, 'PHAR', 'Pharmacy Department', NOW(), NOW());

-- Add sample doctors
INSERT INTO api_doctor (created_at, updated_at, first_name, last_name, email, phone, specialty, hospital_id) VALUES
(NOW(), NOW(), 'John', 'Smith', 'john.smith@hospital.com', '+1234567890', 'Cardiology', 1),
(NOW(), NOW(), 'Jane', 'Doe', 'jane.doe@hospital.com', '+1234567891', 'Neurology', 1),
(NOW(), NOW(), 'Michael', 'Johnson', 'michael.johnson@hospital.com', '+1234567892', 'Pediatrics', 1),
(NOW(), NOW(), 'Sarah', 'Williams', 'sarah.williams@hospital.com', '+1234567893', 'Orthopedics', 1),
(NOW(), NOW(), 'Robert', 'Brown', 'robert.brown@hospital.com', '+1234567894', 'Surgery', 1),
(NOW(), NOW(), 'Emily', 'Jones', 'emily.jones@hospital.com', '+1234567895', 'Obstetrics', 1),
(NOW(), NOW(), 'David', 'Miller', 'david.miller@hospital.com', '+1234567896', 'Internal Medicine', 1),
(NOW(), NOW(), 'Jennifer', 'Davis', 'jennifer.davis@hospital.com', '+1234567897', 'Emergency Medicine', 1),
(NOW(), NOW(), 'James', 'Wilson', 'james.wilson@hospital.com', '+1234567898', 'Radiology', 1),
(NOW(), NOW(), 'Linda', 'Moore', 'linda.moore@hospital.com', '+1234567899', 'Anesthesiology', 1),
(NOW(), NOW(), 'Richard', 'Taylor', 'richard.taylor@hospital.com', '+1234567900', 'Cardiology', 1),
(NOW(), NOW(), 'Patricia', 'Anderson', 'patricia.anderson@hospital.com', '+1234567901', 'Neurology', 1),
(NOW(), NOW(), 'Charles', 'Thomas', 'charles.thomas@hospital.com', '+1234567902', 'Pediatrics', 1),
(NOW(), NOW(), 'Barbara', 'Jackson', 'barbara.jackson@hospital.com', '+1234567903', 'Orthopedics', 1),
(NOW(), NOW(), 'Joseph', 'White', 'joseph.white@hospital.com', '+1234567904', 'Surgery', 1),
(NOW(), NOW(), 'Elizabeth', 'Harris', 'elizabeth.harris@hospital.com', '+1234567905', 'Obstetrics', 1),
(NOW(), NOW(), 'Thomas', 'Martin', 'thomas.martin@hospital.com', '+1234567906', 'Internal Medicine', 1),
(NOW(), NOW(), 'Margaret', 'Thompson', 'margaret.thompson@hospital.com', '+1234567907', 'Emergency Medicine', 1),
(NOW(), NOW(), 'Christopher', 'Garcia', 'christopher.garcia@hospital.com', '+1234567908', 'Radiology', 1),
(NOW(), NOW(), 'Susan', 'Martinez', 'susan.martinez@hospital.com', '+1234567909', 'Anesthesiology', 1);

-- Add sample medications
INSERT INTO api_medication (created_at, updated_at, name, dose, frequency, start_date, end_date, instructions, medical_record_id, is_active) VALUES
(NOW(), NOW(), 'Lisinopril', '10mg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take with water in the morning', 1, true),
(NOW(), NOW(), 'Atorvastatin', '20mg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take with evening meal', 1, true),
(NOW(), NOW(), 'Metformin', '500mg', 'Twice daily', NOW(), NOW() + INTERVAL '30 days', 'Take with meals', 2, true),
(NOW(), NOW(), 'Amlodipine', '5mg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take in the morning', 2, true),
(NOW(), NOW(), 'Levothyroxine', '100mcg', 'Once daily', NOW(), NOW() + INTERVAL '30 days', 'Take on an empty stomach', 3, true);

-- Fix sequences
SELECT setval('public.api_customuser_id_seq', COALESCE((SELECT MAX(id) FROM api_customuser), 1), true);
SELECT setval('public.api_hospital_id_seq', COALESCE((SELECT MAX(id) FROM api_hospital), 1), true);
SELECT setval('public.api_department_id_seq', COALESCE((SELECT MAX(id) FROM api_department), 1), true);
SELECT setval('public.api_doctor_id_seq', COALESCE((SELECT MAX(id) FROM api_doctor), 1), true);
SELECT setval('public.api_medicalrecord_id_seq', COALESCE((SELECT MAX(id) FROM api_medicalrecord), 1), true);
SELECT setval('public.api_medication_id_seq', COALESCE((SELECT MAX(id) FROM api_medication), 1), true);

COMMIT;
