from api.models import CustomUser, MedicalRecord, Medication, Doctor, NominatedPharmacy
  from datetime import date

  # Get your user (REPLACE WITH YOUR EMAIL)
  user = CustomUser.objects.get(email='eruwagolden@gmail.com')

  print(f"✅ Found user: {user.email} (HPN: {user.hpn})")

  # Check your nominated pharmacy
  nomination = NominatedPharmacy.objects.filter(user=user, is_current=True).first()
  if nomination:
      print(f"✅ Your nominated pharmacy: {nomination.pharmacy.name}")
  else:
      print("❌ No nominated pharmacy found! Nominate one first.")
      exit()

  # Get or create medical record
  medical_record, created = MedicalRecord.objects.get_or_create(
      user=user,
      defaults={'hpn': user.hpn or f'PHN-{user.id}'}
  )
  print(f"✅ Medical record: {medical_record.hpn}")

  # Get a doctor (or create a test one)
  doctor = Doctor.objects.first()
  if not doctor:
      print("❌ No doctors found. Need to create one first.")
      exit()

  print(f"✅ Doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}")

  # Create prescription - THIS SHOULD AUTO-ASSIGN YOUR NOMINATED PHARMACY!
  medication = Medication.objects.create(
      medical_record=medical_record,
      prescribed_by=doctor,
      medication_name='Paracetamol',
      strength='500mg',
      form='Tablet',
      route='Oral',
      dosage='1-2 tablets',
      frequency='Every 4-6 hours as needed',
      start_date=date.today(),
      duration='7 days',
      patient_instructions='Take with food or milk. Do not exceed 8 tablets in 24 hours.',
      indication='Pain relief and fever reduction',
      status='active',
      refills_authorized=2
  )

  print(f"\n🎉 CREATED PRESCRIPTION:")
  print(f"  Medication: {medication.medication_name} {medication.strength}")
  print(f"  Status: {medication.status}")
  print(f"  📍 Auto-assigned Pharmacy: {medication.nominated_pharmacy.name if medication.nominated_pharmacy else 'NONE - THIS IS A BUG!'}")
  print(f"  Pharmacy Code: {medication.nominated_pharmacy.phb_pharmacy_code if medication.nominated_pharmacy else 'N/A'}")
  print(f"  Pharmacy Address: {medication.nominated_pharmacy.address_line_1 if medication.nominated_pharmacy else 'N/A'}")
  print(f"\n✨ Prescription ID: {medication.id}")