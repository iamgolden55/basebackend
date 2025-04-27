from api.models import CustomUser
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.utils.token_utils import build_user_token_data
from api.models.medical.hospital_registration import HospitalRegistration
from api.models import Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from .tokens import HospitalAdminToken
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Appointment, Doctor, AppointmentFee
from datetime import datetime, timedelta
from django.utils import timezone

CustomUser = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=True, error_messages={
        'required': 'Please provide your full name.',
        'blank': 'Full name cannot be empty.'
    })
    email = serializers.EmailField(error_messages={
        'required': 'Email address is required.',
        'invalid': 'Please enter a valid email address.',
        'blank': 'Email address cannot be empty.'
    })
    password = serializers.CharField(write_only=True, error_messages={
        'required': 'Password is required.',
        'blank': 'Password cannot be empty.'
    })
    phone = serializers.CharField(error_messages={
        'required': 'Phone number is required.',
        'blank': 'Phone number cannot be empty.',
        'invalid': 'Please enter a valid phone number.'
    })
    consent_terms = serializers.BooleanField(error_messages={
        'required': 'You must accept the terms and conditions.',
        'invalid': 'You must accept the terms and conditions.'
    })
    consent_hipaa = serializers.BooleanField(error_messages={
        'required': 'You must accept the HIPAA acknowledgment.',
        'invalid': 'You must accept the HIPAA acknowledgment.'
    })
    consent_data_processing = serializers.BooleanField(error_messages={
        'required': 'You must accept the data processing consent.',
        'invalid': 'You must accept the data processing consent.'
    })
    preferred_language = serializers.CharField(error_messages={
        'invalid_choice': 'Please select a valid language.',
        'required': 'Preferred language is required.'
    })
    secondary_languages = serializers.ListField(
        child=serializers.CharField(error_messages={
            'invalid_choice': 'Please enter a valid language.',
            'required': 'Secondary language is required.'
        }),
        error_messages={
            'required': 'Secondary languages are required.'
        }
    )
    custom_language = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={
            'invalid': 'Please enter a valid language name.'
        }
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'date_of_birth', 'gender', 'country', 'city', 'phone', 'state',
            'nin', 'consent_terms', 'consent_hipaa', 'consent_data_processing', 'full_name',
            'preferred_language', 'secondary_languages', 'custom_language'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'date_of_birth': {
                'error_messages': {
                    'invalid': 'Please enter a valid date in YYYY-MM-DD format.',
                    'required': 'Date of birth is required.'
                }
            },
            'gender': {
                'error_messages': {
                    'invalid': 'Please select a valid gender.',
                    'required': 'Gender is required.'
                }
            },
            'country': {
                'error_messages': {
                    'required': 'Country is required.',
                    'blank': 'Country cannot be empty.'
                }
            },
            'preferred_language': {
                'error_messages': {
                    'invalid_choice': 'Please select a valid language.',
                    'required': 'Preferred language is required.'
                }
            }
        }

    def validate_nin(self, value):
        if value:
            # Remove any spaces or special characters
            value = ''.join(filter(str.isdigit, value))
            
            if CustomUser.objects.filter(nin=value).exists():
                raise serializers.ValidationError("This NIN is already registered. Please provide a unique NIN.")
            
            if len(value) != 11:
                raise serializers.ValidationError("NIN must be exactly 11 digits long.")
            
            if not value.isdigit():
                raise serializers.ValidationError("NIN must contain only numbers.")
        return value

    def validate_phone(self, value):
        # Remove any spaces or special characters
        value = ''.join(filter(lambda x: x.isdigit() or x in ['+'], value))
        
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        if not (value.startswith('+') and len(value) >= 10):
            raise serializers.ValidationError("Please enter a valid phone number with country code (e.g., +234...).")
        
        return value

    def validate(self, data):
        # Validate country-specific requirements
        country = data.get('country', '').strip().lower()
        
        if country == 'nigeria':
            if not data.get('nin'):
                raise serializers.ValidationError({
                    'nin': "NIN is required for users from Nigeria."
                })
            
            # NIN validation is handled in validate_nin method
        
        # Validate full name
        full_name = data.get('full_name', '')
        if len(full_name.split()) < 2:
            raise serializers.ValidationError({
                'full_name': "Please provide both first and last name."
            })

        # Validate date of birth
        dob = data.get('date_of_birth')
        if dob:
            from datetime import date
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise serializers.ValidationError({
                    'date_of_birth': "You must be at least 18 years old to register."
                })

        # Validate custom language when "other" is selected
        if data.get('preferred_language') == 'other' and not data.get('custom_language'):
            raise serializers.ValidationError({
                'custom_language': "Please specify your preferred language."
            })

        return data

    def create(self, validated_data):
        # Split full_name into first_name and last_name
        full_name = validated_data.pop('full_name')
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create user with the validated data
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)
    date_of_birth = serializers.DateField(required=False)  # Add this! 📅
    gender = serializers.CharField(required=False)  # Add this too! 👥
    phone = serializers.CharField(
        min_length=10,  # Minimum length 📏
        allow_blank=False,  # Can't be empty! ❌
        error_messages={
            'min_length': 'Phone number must be at least 10 digits long! 📱',
            'blank': 'Phone number cannot be empty! ☎️',
            'required': 'Phone number is required! 📞'
        }
    )
    hpn = serializers.CharField(read_only=True)
    nin = serializers.CharField(read_only=True)
    preferred_language = serializers.CharField(error_messages={
        'invalid_choice': 'Please select a valid language.',
        'required': 'Preferred language is required.'
    })
    secondary_languages = serializers.ListField(
        child=serializers.CharField(error_messages={
            'invalid_choice': 'Please enter a valid language.',
            'required': 'Secondary language is required.'
        }),
        error_messages={
            'required': 'Secondary languages are required.'
        }
    )
    custom_language = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={
            'invalid': 'Please enter a valid language name.'
        }
    )

    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'email',
            'phone', 'country', 
            'state', 'city', 'hpn', 'nin', 'date_of_birth', 'gender',
            'preferred_language', 'secondary_languages', 'custom_language'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        # Create user_data dictionary
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'is_verified': user.is_email_verified,
            'role': user.role,
            'hpn': user.hpn,
            'nin': user.nin,
            'phone': user.phone,
            'country': user.country,
            'state': user.state,
            'city': user.city,
            'date_of_birth': user.date_of_birth,
            'gender': user.gender,
            'has_completed_onboarding': user.has_completed_onboarding,
            'preferred_language': user.preferred_language,
            'secondary_languages': user.secondary_languages,
            'custom_language': user.custom_language
        }
        
        # Add user_data to the response
        data['user_data'] = user_data
        
        return data

class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['is_email_verified']
        read_only_fields = ['is_email_verified']   

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long! 🔒'
        }
    )
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match! 🚫")
        return data  

class OnboardingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['has_completed_onboarding']          

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone']

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name']

class HospitalRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        source='hospital',
        write_only=True
    )

    class Meta:
        model = HospitalRegistration
        fields = [
            'id',
            'user',
            'hospital',
            'hospital_id',
            'status',
            'is_primary',
            'created_at',
            'approved_date'
        ]

class HospitalBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name', 'city', 'state', 'country']          

class HospitalAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = HospitalAdmin
        fields = ['email', 'name', 'hospital', 'position', 'password']
        
    def create(self, validated_data):
        # Create the HospitalAdmin instance directly
        admin = HospitalAdmin(
            email=validated_data['email'],
            name=validated_data['name'],
            hospital=validated_data['hospital'],
            position=validated_data['position'],
            password=validated_data['password']
        )
        admin.save()  # This will trigger the save method that creates the CustomUser
        return admin

class HospitalLocationSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'hospital_type', 'address', 
            'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'distance', 'distance_km',
            'emergency_unit', 'icu_unit', 'is_verified',
            'phone', 'email', 'website'
        ]

    def get_distance(self, obj):
        """Returns the distance in meters"""
        if hasattr(obj, 'distance'):
            return round(obj.distance * 1000, 2)  # Convert km to meters
        return None

    def get_distance_km(self, obj):
        """Returns the distance in kilometers"""
        if hasattr(obj, 'distance'):
            return round(obj.distance, 2)
        return None

class NearbyHospitalSerializer(HospitalLocationSerializer):
    registration_status = serializers.SerializerMethodField()
    is_primary = serializers.SerializerMethodField()
    
    class Meta(HospitalLocationSerializer.Meta):
        fields = HospitalLocationSerializer.Meta.fields + ['registration_status', 'is_primary']
        
    def get_registration_status(self, obj):
        """Check if the current user is registered with this hospital"""
        user = self.context.get('request').user
        if user.is_authenticated:
            registration = obj.hospitalregistration_set.filter(user=user).first()
            if registration:
                return {
                    'status': registration.status,
                    'is_approved': registration.status == 'approved',
                    'registration_date': registration.created_at
                }
        return None
        
    def get_is_primary(self, obj):
        """Check if this is the user's primary hospital"""
        user = self.context.get('request').user
        if user.is_authenticated:
            registration = obj.hospitalregistration_set.filter(
                user=user,
                is_primary=True,
                status='approved'
            ).exists()
            return registration
        return False          
    
class DoctorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'specialization', 'hospital']

class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source='doctor',
        write_only=True,
        required=False
    )
    hospital_name = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    fee_id = serializers.PrimaryKeyRelatedField(
        queryset=AppointmentFee.objects.all(),
        source='fee',
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Appointment
        fields = [
            'id', 
            'appointment_id',
            'doctor', 
            'doctor_id',
            'patient',
            'patient_name',
            'hospital',
            'hospital_name',
            'department',
            'department_name',
            'appointment_date',
            'duration',
            'appointment_type',
            'priority',
            'status',
            'status_display',
            'chief_complaint',
            'symptoms',
            'medical_history',
            'allergies',
            'current_medications',
            'is_insurance_based',
            'insurance_details',
            'payment_status',
            'notes',
            'cancellation_reason',
            'created_at',
            'updated_at',
            'fee',
            'fee_id'
        ]
        read_only_fields = ['patient', 'appointment_id', 'created_at', 'updated_at']
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None
    
    def get_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.status, obj.status)
    
    def validate(self, data):
        """
        Validate appointment data
        """
        # Get appointment date from data
        appointment_date = data.get('appointment_date')
        
        # Check if appointment date is in the past
        if appointment_date and appointment_date < timezone.now():
            raise serializers.ValidationError("Cannot create appointments in the past.")
        
        # Check if doctor is available at the requested time
        doctor = data.get('doctor')
        if doctor and appointment_date:
            # Get appointment duration (default to 30 minutes if not provided)
            duration = data.get('duration', 30)
            
            # Calculate appointment end time
            appointment_end = appointment_date + timedelta(minutes=duration)
            
            # Check for overlapping appointments
            overlapping_appointments = Appointment.objects.filter(
                doctor=doctor,
                status__in=['pending', 'confirmed', 'in_progress'],
                appointment_date__date=appointment_date.date(),  # Only check appointments on the same day
                appointment_date__gte=appointment_date,  # Start time is after or at the requested time
                appointment_date__lt=appointment_end  # Start time is before the end of the requested slot
            ).exclude(id=self.instance.id if self.instance else None)
            
            if overlapping_appointments.exists():
                raise serializers.ValidationError(
                    "Doctor is not available at the requested time. Please choose another time."
                )
        
        return data

class AppointmentListSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    hospital_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_id',
            'doctor',
            'hospital',
            'hospital_name',
            'department',
            'department_name',
            'appointment_date',
            'duration',
            'appointment_type',
            'priority',
            'status',
            'status_display',
            'chief_complaint',
            'created_at'
        ]
    
    def get_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

class AppointmentCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=True)

class AppointmentRescheduleSerializer(serializers.Serializer):
    new_appointment_date = serializers.DateTimeField(required=True)
    
    def validate_new_appointment_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("New appointment date cannot be in the past.")
        return value

class AppointmentApproveSerializer(serializers.Serializer):
    approval_notes = serializers.CharField(required=False, allow_blank=True)

class AppointmentReferSerializer(serializers.Serializer):
    referred_to_hospital = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        required=True
    )
    referral_reason = serializers.CharField(required=True)     