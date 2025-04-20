def perform_create(self, serializer):
    """
    Set the patient to the current user when creating an appointment
    """
    # Check if doctor_id is provided
    doctor = serializer.validated_data.get("doctor")
    
    if not doctor:
        # Prepare appointment data for ML assignment
        appointment_data = {
            "patient": self.request.user,
            "department": serializer.validated_data.get("department"),
            "hospital": serializer.validated_data.get("hospital"),
            "appointment_type": serializer.validated_data.get("appointment_type", "consultation"),
            "priority": serializer.validated_data.get("priority", "normal"),
            "appointment_date": serializer.validated_data.get("appointment_date")
        }

        # Use ML to assign the best doctor
        try:
            from api.utils.doctor_assignment import assign_doctor
            assigned_doctor = assign_doctor(appointment_data)
            
            if not assigned_doctor:
                raise ValidationError("No suitable doctor available for this appointment.")
            
            # Save with assigned doctor
            appointment = serializer.save(
                patient=self.request.user,
                doctor=assigned_doctor
            )
        except ImportError:
            # If ML module is not available, raise error
            raise ValidationError("Doctor assignment service is currently unavailable.")
    else:
        # Save with provided doctor
        appointment = serializer.save(patient=self.request.user)
    
    # Send confirmation
    self._send_appointment_confirmation(appointment)
    
    return appointment
