-- Sample data import script generated from backup
BEGIN;

-- Add sample departments
INSERT INTO api_department (name, hospital_id, code, description) VALUES
('Emergency', 1, 'EMER104', 'emergency'),
('Outpatient', 1, 'OUTP102', 'outpatient'),
('Pharmacy', 1, 'PHAR103', 'pharmacy'),
('Radiology', 1, 'RADI101', 'radiology'),
('Surgery', 1, 'SURG105', 'surgical'),
('Cardiology', 1, 'CARD201', 'medical'),
('Dermatology', 1, 'DERM205', 'medical'),
('ENT', 1, 'ENT206', 'medical'),
('Gastroenterology', 1, 'GAST207', 'medical'),
('General Medicine', 1, 'GENM204', 'medical');

-- Add sample doctors
INSERT INTO api_doctor (created_at, updated_at, first_name, last_name, email, phone, specialty, hospital_id) VALUES
('Cardiology', 'LIC-12809407', '2026-05-03', '21', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7408275', '2027-05-03', '5', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7412555', '2030-05-02', '18', '["MBBS", "FWACP"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7423421', '2028-05-02', '8', '["MBBS", "FMCPath"]', 'FWACP', 't', 1),
('Outpatient', 'LIC-7201128', '2030-05-02', '29', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Outpatient', 'LIC-7213600', '2028-05-02', '20', '["MBBS", "FWACP"]', 'FWACP', 't', 1),
('Outpatient', 'LIC-7227875', '2030-05-02', '9', '["MBBS", "FMCPath"]', 'FWACP', 't', 1),
('Pharmacy', 'LIC-7303691', '2029-05-02', '19', '["MBBS", "FWACS"]', 'FWACP', 't', 1),
('Pharmacy', 'LIC-7315123', '2027-05-03', '10', '["MBBS", "FMCORL"]', 'FWACP', 't', 1),
('Pharmacy', 'LIC-7325864', '2026-05-03', '30', '["MBBS", "FMCP"]', 'FWACP', 't', 1),
('Radiology', 'LIC-7106198', '2029-05-02', '29', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Radiology', 'LIC-7115245', '2028-05-02', '29', '["MBBS", "FMCORL"]', 'FWACP', 't', 1),
('Radiology', 'LIC-7126212', '2030-05-02', '30', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Radiology', 'LIC-14213480', '2028-05-02', '24', '["MBBS", "FWACS"]', 'FWACP', 't', 1),
('Radiology', 'LIC-9026391', '2029-05-02', '20', '["MBBS", "FWACS"]', 'FWACP', 't', 1),
('Cardiology', 'LIC-12808069', '2027-05-03', '8', '["MBBS", "FMCPath"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7406468', '2029-05-02', '11', '["MBBS", "FMCPath"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7412887', '2026-05-03', '23', '["MBBS", "FWACP"]', 'FWACP', 't', 1),
('Emergency', 'LIC-7421038', '2030-05-02', '4', '["MBBS", "FWACS", "MSc"]', 'FWACP', 't', 1),
('Emergency', 'LIC-11608526', '2026-05-03', '24', '["MBBS", "FWACP"]', 'FWACP', 't', 1);

-- Fix sequences
SELECT setval('public.api_customuser_id_seq', COALESCE((SELECT MAX(id) FROM api_customuser), 1), true);
SELECT setval('public.api_hospital_id_seq', COALESCE((SELECT MAX(id) FROM api_hospital), 1), true);
SELECT setval('public.api_department_id_seq', COALESCE((SELECT MAX(id) FROM api_department), 1), true);
SELECT setval('public.api_doctor_id_seq', COALESCE((SELECT MAX(id) FROM api_doctor), 1), true);
SELECT setval('public.api_medicalrecord_id_seq', COALESCE((SELECT MAX(id) FROM api_medicalrecord), 1), true);
SELECT setval('public.api_medication_id_seq', COALESCE((SELECT MAX(id) FROM api_medication), 1), true);

COMMIT;