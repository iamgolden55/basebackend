from api.models import CustomUser
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.utils.token_utils import build_user_token_data
from api.models.medical.hospital_registration import HospitalRegistration
from api.models import Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from api.models import Department
from .tokens import HospitalAdminToken
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)

from api.models import Appointment, Doctor, AppointmentFee
from datetime import datetime, timedelta
from django.utils import timezone

# Import MedicalRecord model
from api.models.medical.medical_record import MedicalRecord
from api.models.medical.medication import Medication, MedicationCatalog
from api.models.medical.patient_admission import PatientAdmission
from api.models.medical.patient_transfer import PatientTransfer
from api.models.medical.payment_transaction import PaymentTransaction

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
            'nin', 'hpn', 'consent_terms', 'consent_hipaa', 'consent_data_processing', 'full_name',
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
    date_of_birth = serializers.DateField(required=False)  # Add this! 
    gender = serializers.CharField(required=False)  # Add this too! 
    phone = serializers.CharField(
        min_length=10,  # Minimum length 
        allow_blank=False,  # Can't be empty! 
        error_messages={
            'min_length': 'Phone number must be at least 10 digits long! ',
            'blank': 'Phone number cannot be empty! ',
            'required': 'Phone number is required! '
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
        },
        required=False
    )
    custom_language = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={
            'invalid': 'Please enter a valid language name.'
        }
    )
    role = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'email',
            'phone', 'country', 
            'state', 'city', 'hpn', 'nin', 'date_of_birth', 'gender',
            'preferred_language', 'secondary_languages', 'custom_language', 'role'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
        
    def to_representation(self, instance):
        """Properly convert secondary_languages from various formats to a list"""
        data = super().to_representation(instance)
        
        # Handle secondary_languages conversion
        if 'secondary_languages' in data:
            secondary_languages = instance.secondary_languages
            
            # Handle the case when it's None
            if secondary_languages is None:
                data['secondary_languages'] = []
            # Handle the case when it's already a list (but stored as a string representation)
            elif isinstance(secondary_languages, str):
                # Check if it's a string representation of a list like "['yo', 'en']"
                if secondary_languages.startswith('[') and secondary_languages.endswith(']'):
                    # Remove brackets and split by comma
                    langs = secondary_languages.strip('[]')
                    # Handle empty list case
                    if not langs:
                        data['secondary_languages'] = []
                    else:
                        # Split by comma and remove quotes and whitespace
                        data['secondary_languages'] = [
                            lang.strip().strip("'").strip('"') 
                            for lang in langs.split(',')
                        ]
                # Handle the case when it's a comma-separated string like "yoruba,hausa"
                else:
                    data['secondary_languages'] = [
                        lang.strip() for lang in secondary_languages.split(',') if lang.strip()
                    ]
                    
        return data

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
            'custom_language': user.custom_language
        }
        
        # Handle secondary_languages conversion
        secondary_languages = user.secondary_languages
        if secondary_languages is None:
            user_data['secondary_languages'] = []
        elif isinstance(secondary_languages, str):
            # Check if it's a string representation of a list like "['yo', 'en']"
            if secondary_languages.startswith('[') and secondary_languages.endswith(']'):
                # Remove brackets and split by comma
                langs = secondary_languages.strip('[]')
                # Handle empty list case
                if not langs:
                    user_data['secondary_languages'] = []
                else:
                    # Split by comma and remove quotes and whitespace
                    user_data['secondary_languages'] = [
                        lang.strip().strip("'").strip('"') 
                        for lang in langs.split(',')
                    ]
            # Handle the case when it's a comma-separated string like "yoruba,hausa"
            else:
                user_data['secondary_languages'] = [
                    lang.strip() for lang in secondary_languages.split(',') if lang.strip()
                ]
        
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
            'min_length': 'Password must be at least 8 characters long! '
        }
    )
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match! ")
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
    date_of_birth = serializers.DateField(required=True, error_messages={
        'required': 'Date of birth is required.',
        'invalid': 'Please enter a valid date.'
    })
    gender = serializers.CharField(required=True, error_messages={
        'required': 'Gender is required.',
        'blank': 'Gender cannot be empty.'
    })
    phone = serializers.CharField(required=True, error_messages={
        'required': 'Phone number is required.',
        'blank': 'Phone number cannot be empty.',
        'invalid': 'Please enter a valid phone number.'
    })
    country = serializers.CharField(required=True, error_messages={
        'required': 'Country is required.',
        'blank': 'Country cannot be empty.'
    })
    state = serializers.CharField(required=True, error_messages={
        'required': 'State is required.',
        'blank': 'State cannot be empty.'
    })
    city = serializers.CharField(required=True, error_messages={
        'required': 'City is required.',
        'blank': 'City cannot be empty.'
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
    
    class Meta:
        model = HospitalAdmin
        fields = [
            'email', 'password', 'full_name', 'date_of_birth', 'gender', 
            'phone', 'country', 'state', 'city', 'preferred_language', 
            'secondary_languages', 'custom_language', 'consent_terms', 
            'consent_hipaa', 'consent_data_processing', 'hospital', 'position'
        ]
        
    def create(self, validated_data):
        # Extract user data from validated_data
        full_name = validated_data.pop('full_name', '')
        name_parts = full_name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Create the HospitalAdmin instance with required fields only
        admin = HospitalAdmin(
            email=validated_data['email'],
            name=full_name,
            hospital=validated_data['hospital'],
            position=validated_data['position'],
            password=validated_data['password']
        )
        
        # Set the _user_data attribute after initialization
        admin._user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': validated_data.get('date_of_birth'),
            'gender': validated_data.get('gender'),
            'phone': validated_data.get('phone'),
            'country': validated_data.get('country'),
            'state': validated_data.get('state'),
            'city': validated_data.get('city'),
            'preferred_language': validated_data.get('preferred_language'),
            'secondary_languages': validated_data.get('secondary_languages', []),
            'custom_language': validated_data.get('custom_language', ''),
            'consent_terms': validated_data.get('consent_terms', False),
            'consent_hipaa': validated_data.get('consent_hipaa', False),
            'consent_data_processing': validated_data.get('consent_data_processing', False)
        }
        
        admin.save()  # This will trigger the save method that creates the CustomUser
        return admin

class ExistingUserToAdminSerializer(serializers.Serializer):
    user_email = serializers.EmailField(required=True, error_messages={
        'required': 'User email is required.',
        'invalid': 'Please enter a valid email address.',
        'blank': 'User email cannot be empty.'
    })
    hospital = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        error_messages={
            'required': 'Hospital selection is required.',
            'does_not_exist': 'Selected hospital does not exist.',
            'incorrect_type': 'Invalid hospital selection.'
        }
    )
    position = serializers.CharField(required=True, error_messages={
        'required': 'Position is required.',
        'blank': 'Position cannot be empty.'
    })
    
    def validate_user_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
            if hasattr(user, 'hospital_admin_profile'):
                raise serializers.ValidationError("This user is already a hospital admin")
            return value
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
            
    def create(self, validated_data):
        user = CustomUser.objects.get(email=validated_data['user_email'])
        admin = HospitalAdmin.objects.create(
            user=user,
            hospital=validated_data['hospital'],
            position=validated_data['position'],
            email=user.email,
            name=f"{user.first_name} {user.last_name}"
        )
        # Update user role
        user.role = 'hospital_admin'
        user.is_staff = True
        user.save()
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
    
    # New fields to match email template format
    formatted_date = serializers.SerializerMethodField(read_only=True)
    formatted_time = serializers.SerializerMethodField(read_only=True)
    formatted_date_time = serializers.SerializerMethodField(read_only=True)
    appointment_duration_display = serializers.SerializerMethodField(read_only=True)
    important_notes = serializers.SerializerMethodField(read_only=True)
    formatted_appointment_type = serializers.SerializerMethodField(read_only=True)
    formatted_priority = serializers.SerializerMethodField(read_only=True)
    doctor_full_name = serializers.SerializerMethodField(read_only=True)
    
    def to_internal_value(self, data):
        """
        Preprocess data before validation.
        Add detailed debug logging.
        """
        logger.debug("Appointment serializer to_internal_value called")
        logger.debug(f"Incoming data: {data}")
        
        # Make a copy of the data to avoid modifying the original
        data_dict = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # Check for required fields and log warnings
        required_fields = ['hospital', 'department', 'appointment_date', 'appointment_type']
        for field in required_fields:
            if field not in data_dict or data_dict[field] is None:
                logger.warning(f"Required field '{field}' is missing or null")
        
        # More detailed field logging
        logger.debug("Field values:")
        for key, value in data_dict.items():
            logger.debug(f"  - {key}: {value} (type: {type(value).__name__})")
        
        try:
            result = super().to_internal_value(data_dict)
            logger.debug(f"Internal value result: {result}")
            logger.debug("to_internal_value completed successfully - validate() should be called next")
            return result
        except Exception as e:
            logger.error(f"Error in to_internal_value: {e}")
            logger.error("to_internal_value failed - validate() will NOT be called")
            raise
    
    class Meta:
        model = Appointment
        fields = [
            'id', 
            'appointment_id',
            'doctor', 
            'doctor_id',
            'doctor_full_name',
            'patient',
            'patient_name',
            'hospital',
            'hospital_name',
            'department',
            'department_name',
            'appointment_date',
            'formatted_date',
            'formatted_time',
            'formatted_date_time',
            'duration',
            'appointment_duration_display',
            'appointment_type',
            'formatted_appointment_type',
            'priority',
            'formatted_priority',
            'status',
            'status_display',
            'chief_complaint',
            'symptoms',
            'symptoms_data',
            'medical_history',
            'allergies',
            'current_medications',
            'is_insurance_based',
            'insurance_details',
            'payment_status',
            'notes',
            'important_notes',
            'cancellation_reason',
            'created_at',
            'updated_at'
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
    
    # New getter methods for formatted fields
    def get_formatted_date(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%B %d, %Y")
        return None
    
    def get_formatted_time(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%I:%M %p")
        return None
    
    def get_formatted_date_time(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%A, %B %d, %Y at %I:%M %p")
        return None
    
    def get_appointment_duration_display(self, obj):
        return f"{obj.duration} minutes"
    
    def get_important_notes(self, obj):
        notes = [
            "Please arrive 15 minutes before your appointment time",
            "Bring any relevant medical records or test results",
            "If you need to cancel or reschedule, please do so at least 24 hours in advance",
            "Wear a face mask during your visit"
        ]
        
        # Add payment note if applicable
        if obj.payment_required and obj.payment_status == 'pending':
            notes.append("Please complete your payment to confirm the appointment")
            
        return notes
    
    def get_formatted_appointment_type(self, obj):
        appointment_types = {
            'first_visit': 'First Visit',
            'follow_up': 'Follow-up',
            'emergency': 'Emergency',
            'consultation': 'Consultation',
            'check_up': 'Routine Check-up',
            'specialist': 'Specialist Consultation'
        }
        return appointment_types.get(obj.appointment_type, obj.appointment_type)
    
    def get_formatted_priority(self, obj):
        priorities = {
            'low': 'Low Priority',
            'normal': 'Normal Priority',
            'high': 'High Priority',
            'emergency': 'Emergency'
        }
        return priorities.get(obj.priority, obj.priority)
    
    def get_doctor_full_name(self, obj):
        if obj.doctor and obj.doctor.user:
            return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"
        return None
    
    def is_valid(self, *, raise_exception=False):
        """Override is_valid to add debugging"""
        logger.debug("Appointment serializer is_valid() called")
        logger.debug(f"raise_exception: {raise_exception}")
        result = super().is_valid(raise_exception=raise_exception)
        logger.debug(f"is_valid() result: {result}")
        if hasattr(self, '_errors'):
            logger.debug(f"Validation errors: {self._errors}")
        return result

    def validate(self, data):
        """
        Validate appointment data
        """
        logger.debug("Appointment serializer validation called")
        logger.debug(f"Data being validated: {data}")
        
        # List required fields that are missing
        required_fields = ['hospital', 'department', 'appointment_date', 'appointment_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            error_message = f"Missing required fields: {', '.join(missing_fields)}"
            raise serializers.ValidationError(error_message)
        
        # Check data types of important fields
        logger.debug("Field types:")
        for field, value in data.items():
            logger.debug(f"  - {field}: {type(value).__name__}")
        
        # Get appointment date from data
        appointment_date = data.get('appointment_date')
        logger.debug(f"Appointment date: {appointment_date}")
        
        # Check if appointment date is in the past
        if appointment_date and appointment_date < timezone.now():
            logger.error("Appointment date is in the past")
            raise serializers.ValidationError("Cannot create appointments in the past.")
        
        # CRITICAL: Check for duplicate appointments in same specialty on same date
        # This prevents users from reaching payment stage with invalid appointments
        logger.debug("Starting duplicate appointment check")
        department = data.get('department')
        appointment_type = data.get('appointment_type')
        priority = data.get('priority')
        
        if appointment_date and department:
            logger.debug(f"Checking for duplicate specialty appointments: Department {department.id} ({department.name}) on {appointment_date.date()}")
            
            # Skip duplicate check for emergency appointments
            is_emergency = (
                priority == 'emergency' or 
                appointment_type == 'emergency'
            )
            
            logger.debug(f"Appointment type: {appointment_type}, Priority: {priority}, Is emergency: {is_emergency}")
            
            if is_emergency:
                logger.info("Skipping duplicate check for emergency appointment")
            else:
                # Get current user from context - patient will be set in perform_create
                request = self.context.get('request')
                patient = request.user if request else None
                
                logger.debug(f"Patient from context: {patient} (ID: {patient.id if patient else 'None'})")
                
                if patient:
                    # First, let's see ALL appointments for this patient on this date
                    all_patient_appointments = Appointment.objects.filter(
                        patient=patient,
                        appointment_date__date=appointment_date.date()
                    )
                    logger.debug(f"All patient appointments on {appointment_date.date()}: {all_patient_appointments.count()}")
                    for app in all_patient_appointments:
                        logger.debug(f"  - ID={app.id}, Dept={app.department.name}, Status={app.status}, Date={app.appointment_date}")
                    
                    # Use EXACT same logic as model validation for consistency
                    logger.debug(f"Building query: patient={patient.id}, date={appointment_date.date()}, department={department.id}")
                    
                    # Use the globally imported Appointment model
                    same_specialty_appointments = Appointment.objects.filter(
                        patient=patient,
                        appointment_date__date=appointment_date.date(),
                        department=department,
                        status__in=['pending', 'confirmed', 'in_progress', 'scheduled']
                    ).exclude(
                        status__in=['cancelled', 'completed', 'no_show']
                    )
                    
                    logger.debug(f"Count before instance exclusion: {same_specialty_appointments.count()}")
                    
                    # Exclude current appointment if updating (use same logic as model)
                    if self.instance and self.instance.pk:
                        logger.debug(f"Excluding current instance: {self.instance.pk}")
                        same_specialty_appointments = same_specialty_appointments.exclude(pk=self.instance.pk)
                        logger.debug(f"Count after instance exclusion: {same_specialty_appointments.count()}")
                    
                    # Force evaluation of the queryset to ensure it's current
                    duplicate_count = same_specialty_appointments.count()
                    logger.debug(f"Final duplicate count: {duplicate_count}")
                    
                    if duplicate_count > 0:
                        existing_appointment = same_specialty_appointments.first()
                        logger.warning(f"Found duplicate appointment {existing_appointment.appointment_id} in {department.name}")
                        logger.debug(f"Existing appointment details: Date={existing_appointment.appointment_date}, Status={existing_appointment.status}")
                        
                        # Use exact same error message format as model validation
                        error_message = f"You already have a {department.name} appointment on {appointment_date.date().strftime('%B %d, %Y')}. Please choose another date or specialty."
                        raise serializers.ValidationError({
                            'appointment_date': error_message
                        })
                    else:
                        logger.debug("No duplicate specialty appointments found")
                else:
                    logger.warning("No patient found in context - skipping duplicate check")
        
        # Check if doctor is available at the requested time
        doctor = data.get('doctor')
        if doctor and appointment_date:
            logger.debug(f"Checking doctor availability: Doctor ID {doctor.id}")
            
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
                logger.warning(f"Doctor is not available at the requested time. Found {overlapping_appointments.count()} overlapping appointments")
                for app in overlapping_appointments:
                    logger.debug(f"  - Existing appointment: {app.id} at {app.appointment_date}")
                raise serializers.ValidationError(
                    "Doctor is not available at the requested time. Please choose another time."
                )
        
        logger.debug("Validation passed successfully")
        return data

class AppointmentListSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    hospital_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField(read_only=True)
    formatted_time = serializers.SerializerMethodField(read_only=True)
    formatted_date_time = serializers.SerializerMethodField(read_only=True)
    doctor_full_name = serializers.SerializerMethodField(read_only=True)
    formatted_appointment_type = serializers.SerializerMethodField(read_only=True)
    formatted_priority = serializers.SerializerMethodField(read_only=True)
    patient_full_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_id',
            'doctor',
            'doctor_full_name',
            'hospital',
            'hospital_name',
            'department',
            'department_name',
            'appointment_date',
            'formatted_date',
            'formatted_time',
            'formatted_date_time',
            'duration',
            'appointment_type',
            'formatted_appointment_type',
            'priority',
            'formatted_priority',
            'status',
            'status_display',
            'chief_complaint',
            'created_at',
            'patient_full_name'
        ]
    
    def get_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_formatted_date(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%B %d, %Y")
        return None
    
    def get_formatted_time(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%I:%M %p")
        return None
    
    def get_formatted_date_time(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%A, %B %d, %Y at %I:%M %p")
        return None
    
    def get_formatted_appointment_type(self, obj):
        appointment_types = {
            'first_visit': 'First Visit',
            'follow_up': 'Follow-up',
            'emergency': 'Emergency',
            'consultation': 'Consultation',
            'check_up': 'Routine Check-up',
            'specialist': 'Specialist Consultation'
        }
        return appointment_types.get(obj.appointment_type, obj.appointment_type)
    
    def get_formatted_priority(self, obj):
        priorities = {
            'low': 'Low Priority',
            'normal': 'Normal Priority',
            'high': 'High Priority',
            'emergency': 'Emergency'
        }
        return priorities.get(obj.priority, obj.priority)
    
    def get_doctor_full_name(self, obj):
        if obj.doctor and obj.doctor.user:
            return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"
        return None
    
    def get_patient_full_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient.first_name and obj.patient.last_name else obj.patient.first_name if obj.patient.first_name else obj.patient.last_name
        return None

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

class AppointmentReferSerializer(serializers.ModelSerializer):
    referred_to_hospital = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        required=False
    )
    referred_to_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False
    )
    referral_reason = serializers.CharField(required=True)

    class Meta:
        model = Appointment
        fields = ['referred_to_hospital', 'referred_to_department', 'referral_reason']

    def validate(self, data):
        if not data.get('referred_to_hospital') and not data.get('referred_to_department'):
            raise serializers.ValidationError(
                "Either referred_to_hospital or referred_to_department must be specified"
            )
        return data

class PatientMedicalRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for patient-facing medical record data with appropriate data protection
    """
    diagnoses = serializers.SerializerMethodField()
    treatments = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = [
            'hpn', 
            'blood_type', 
            'allergies', 
            'chronic_conditions',
            'emergency_contact_name',
            'emergency_contact_phone',
            'last_visit_date',
            'diagnoses',
            'treatments'
        ]
    
    def get_diagnoses(self, obj):
        # Only return active diagnoses
        diagnoses = obj.diagnoses.filter(is_active=True).order_by('-diagnosis_date')
        return [{
            'code': diagnosis.diagnosis_code,
            'name': diagnosis.diagnosis_name,
            'date': diagnosis.diagnosis_date,
            'is_chronic': diagnosis.is_chronic,
            'severity': diagnosis.severity_rating,
            # Exclude notes - these are for medical staff only
        } for diagnosis in diagnoses]
    
    def get_treatments(self, obj):
        # Only return active treatments
        treatments = obj.treatments.filter(is_active=True).order_by('-start_date')
        return [{
            'type': treatment.treatment_type,
            'name': treatment.treatment_name,
            'start_date': treatment.start_date,
            'end_date': treatment.end_date,
            'dosage': treatment.dosage,
            'frequency': treatment.frequency,
            # Exclude notes - these are for medical staff only
        } for treatment in treatments]     

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        # Check that the new password and confirm password match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "New passwords don't match."
            })
        return data


class MedicationSerializer(serializers.ModelSerializer):
    """Serializer for the Medication model"""
    medication_name = serializers.CharField(required=True)
    strength = serializers.CharField(required=True)
    form = serializers.CharField(required=True)
    route = serializers.CharField(required=True)
    dosage = serializers.CharField(required=True)
    frequency = serializers.CharField(required=True)
    start_date = serializers.DateField(required=False)  
    end_date = serializers.DateField(required=False, allow_null=True)
    duration = serializers.CharField(required=False, allow_null=True)
    patient_instructions = serializers.CharField(required=False, allow_null=True)
    pharmacy_instructions = serializers.CharField(required=False, allow_null=True)
    indication = serializers.CharField(required=False, allow_null=True)
    refills_authorized = serializers.IntegerField(default=0)
    pharmacy_name = serializers.CharField(required=False, allow_null=True)
    prescribed_by = DoctorSerializer(read_only=True)

    class Meta:
        model = Medication
        fields = [
            'id', 'medication_name', 'generic_name', 'strength', 'form', 'route',
            'dosage', 'frequency', 'start_date', 'end_date', 'is_ongoing',
            'duration', 'patient_instructions', 'pharmacy_instructions', 'indication',
            'prescription_number', 'refills_authorized', 'refills_remaining',
            'status', 'pharmacy_name', 'priority', 'prescribed_by'
        ]
        read_only_fields = ['id', 'generic_name', 'prescription_number', 'refills_remaining', 'prescribed_by']


class PrescriptionSerializer(serializers.Serializer):
    """Serializer for creating multiple medications as prescriptions"""
    appointment_id = serializers.CharField(required=False)
    medications = MedicationSerializer(many=True)


class HospitalAdminLoginSerializer(serializers.Serializer):
    """
    Serializer for hospital administrator login with domain validation
    """
    email = serializers.EmailField(
        error_messages={
            'required': 'Hospital admin email is required',
            'invalid': 'Please enter a valid hospital email address'
        }
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required'
        }
    )
    hospital_code = serializers.CharField(
        required=True,
        error_messages={
            'required': 'Hospital code is required for administrator login'
        }
    )
    
    def validate_email(self, value):
        """
        Validate that the email follows hospital domain patterns.
        Environment-aware validation that's more permissive in development.
        """
        import re
        from django.conf import settings
        
        # Get approved domains from settings or use defaults
        # This allows for easy configuration in production without code changes
        approved_domains = getattr(settings, 'APPROVED_HEALTHCARE_DOMAINS', [
            'medicare.com', 'hospital.org', 'health.gov', 'care.org', 
            'medical.net', 'clinic.com', 'healthcare.org', 'example.com'
        ])
        
        # Define healthcare-related suffixes for pattern matching
        healthcare_suffixes = getattr(settings, 'HEALTHCARE_DOMAIN_SUFFIXES', [
            'hospital', 'medical', 'health', 'care', 'clinic', 'healthcare',
            'med', 'doctors', 'physicians', 'nursing', 'pharmacy'
        ])
        
        # In development, accept any valid email
        if settings.DEBUG:
            # Optional basic validation (ensure it's at least a .com, .org, etc.)
            if not re.match(r'.+@.+\..+', value):
                raise serializers.ValidationError("Please enter a valid email address")
            return value
            
        # Extract domain from email
        domain = value.split('@')[-1]
        
        # More comprehensive validation for production:
        # 1. Check against approved domains list
        domain_valid = any(domain.endswith(valid_d) for valid_d in approved_domains)
        
        # 2. Check against healthcare domain pattern
        pattern_string = r'.*\.(' + '|'.join(healthcare_suffixes) + r')\.(com|org|net|gov|edu)$'
        pattern_valid = re.match(pattern_string, domain)
        
        # 3. Check hospital-specific domains (hospital.org, somehospital.org, etc.)
        hospital_domain_valid = ('hospital' in domain)
        
        if not (domain_valid or pattern_valid or hospital_domain_valid):
            raise serializers.ValidationError(
                "Email must use an approved healthcare domain. "
                "Contact system administrator if your hospital domain needs to be approved."
            )
        
        return value


class Hospital2FAVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying hospital admin 2FA codes
    """
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=8)
    device_id = serializers.CharField(required=False, allow_blank=True)
    remember_device = serializers.BooleanField(default=False)


# Staff Management Serializers
class DoctorProfileSerializer(serializers.Serializer):
    """Serializer for doctor-specific profile information"""
    specialization = serializers.CharField(required=True)
    medical_license_number = serializers.CharField(required=True)
    license_expiry_date = serializers.DateField(required=True)
    years_of_experience = serializers.IntegerField(required=True)
    is_active = serializers.BooleanField(default=True)
    status = serializers.CharField(default='active')
    available_for_appointments = serializers.BooleanField(default=True)
    consultation_hours_start = serializers.TimeField(required=False)
    consultation_hours_end = serializers.TimeField(required=False)

    def to_representation(self, instance):
        """Custom representation to format consultation hours"""
        data = super().to_representation(instance)
        if 'consultation_hours_start' in data:
            data['consultation_hours_start'] = data['consultation_hours_start'].strftime('%H:%M:%S')
        if 'consultation_hours_end' in data:
            data['consultation_hours_end'] = data['consultation_hours_end'].strftime('%H:%M:%S')
        return data

    def validate_medical_license_number(self, value):
        """Ensure medical license number is unique"""
        if Doctor.objects.filter(medical_license_number=value).exists():
            raise serializers.ValidationError("This medical license number is already in use")
        return value

    def validate_license_expiry_date(self, value):
        """Ensure license expiry date is in the future"""
        if value <= timezone.now().date():
            raise serializers.ValidationError("License expiry date must be in the future")
        return value

    def create(self, validated_data, user, hospital, department):
        """Create doctor profile"""
        return Doctor.objects.create(
            user=user,
            hospital=hospital,
            department=department,
            **validated_data
        )

class StaffCreationSerializer(serializers.ModelSerializer):
    """Serializer for creating new staff members"""
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=['doctor', 'nurse', 'staff'], required=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=True
    )
    doctor_profile = DoctorProfileSerializer(required=False)
    role_display = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone',
            'role', 'role_display', 'department', 'department_name', 'date_of_birth', 'gender',
            'preferred_language', 'secondary_languages', 'custom_language',
            'doctor_profile',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone': {'required': True},
            'role': {'required': True},
            'department': {'required': True},
            'secondary_languages': {'required': False, 'default': []}
        }

    def get_role_display(self, obj):
        """Get the display value for the role field"""
        return obj.get_role_display()

    def get_department_name(self, obj):
        """Get the name of the department"""
        return obj.department.name if obj.department else None

    def create(self, validated_data):
        user = self.context['request'].user
        hospital = user.hospital_admin_profile.hospital
        
        # Extract and validate doctor profile if present
        doctor_profile_data = validated_data.pop('doctor_profile', None)
        if validated_data['role'] == 'doctor' and not doctor_profile_data:
            raise serializers.ValidationError("Doctor role requires doctor_profile data")
        
        try:
            # First create the base user
            staff_user = CustomUser.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data['phone'],
                role=validated_data['role'],
                date_of_birth=validated_data.get('date_of_birth'),
                gender=validated_data.get('gender'),
                preferred_language=validated_data.get('preferred_language', 'en'),
                secondary_languages=validated_data.get('secondary_languages', []),
                custom_language=validated_data.get('custom_language', '')
            )
            
            # Create hospital registration
            HospitalRegistration.objects.create(
                user=staff_user,
                hospital=hospital,
                status='approved'
            )
            
            # Create role-specific profile
            if validated_data['role'] == 'doctor':
                doctor_serializer = DoctorProfileSerializer(data=doctor_profile_data)
                doctor_serializer.is_valid(raise_exception=True)
                doctor_serializer.create(
                    doctor_serializer.validated_data,
                    user=staff_user,
                    hospital=hospital,
                    department=validated_data['department']
                )
            elif validated_data['role'] == 'nurse':
                Nurse.objects.create(
                    user=staff_user,
                    hospital=hospital,
                    department=validated_data['department']
                )
            elif validated_data['role'] == 'staff':
                Staff.objects.create(
                    user=staff_user,
                    hospital=hospital,
                    department=validated_data['department']
                )
            logger.debug(f"Successfully created base user: {staff_user}")
            return staff_user
        except Exception as e:
            logger.error(f"Error creating staff member: {str(e)}")
            raise serializers.ValidationError(f"Failed to create staff member: {str(e)}")

    
    def validate(self, data):
        """
        Validate that the department belongs to the user's hospital
        """
        logger.debug(f"Validating staff creation data: {data}")
        user = self.context['request'].user
        logger.debug(f"Current user: {user}, is admin: {hasattr(user, 'hospital_admin_profile')}")
        
        if not hasattr(user, 'hospital_admin_profile'):
            raise serializers.ValidationError("Only hospital admins can create staff")
            
        department = data.get('department')
        logger.debug(f"Selected department: {department}, department hospital: {department.hospital if department else None}")
        logger.debug(f"User's hospital: {user.hospital_admin_profile.hospital if hasattr(user, 'hospital_admin_profile') else None}")
        
        if not department.hospital == user.hospital_admin_profile.hospital:
            raise serializers.ValidationError("Department must belong to your hospital")
        
        return data


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for hospital staff members"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    
    class Meta:
        model = get_user_model()
        fields = [
            'id', 'email', 'full_name', 'role', 'role_display',
            'department_name', 'is_available', 'availability_status',
            'phone', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'last_login', 'date_joined']
        
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}" if obj.first_name and obj.last_name else obj.email
    
    def get_role_display(self, obj):
        """Get display name for role"""
        return obj.get_role_display()
    
    def get_department_name(self, obj):
        """Get department name if user is a doctor"""
        if hasattr(obj, 'doctor_profile') and obj.doctor_profile.department:
            return obj.doctor_profile.department.name
        return None
    
    def get_is_available(self, obj):
        """Check if staff member is currently available"""
        # For doctors, check their availability flag
        if hasattr(obj, 'doctor_profile'):
            return obj.doctor_profile.available_for_appointments
        # For other staff, check their active status
        return obj.is_active
    
    def get_availability_status(self, obj):
        """Get detailed availability status"""
        if hasattr(obj, 'doctor_profile') and obj.doctor_profile:
            consultation_hours_start = obj.doctor_profile.consultation_hours_start or datetime.strptime('09:00:00', '%H:%M:%S').time()
            consultation_hours_end = obj.doctor_profile.consultation_hours_end or datetime.strptime('17:00:00', '%H:%M:%S').time()
            
            current_time = datetime.now().strftime('%H:%M:%S')
            start_time = consultation_hours_start.strftime('%H:%M:%S')
            end_time = consultation_hours_end.strftime('%H:%M:%S')
            is_active = current_time >= start_time and current_time <= end_time
            
            return {
                'is_available': obj.doctor_profile.available_for_appointments,
                'consultation_hours_start': start_time,
                'consultation_hours_end': end_time,
                'next_available_slot': self._get_next_available_slot(obj),
                'is_active': is_active
            }
        return {
            'is_available': obj.is_active,
            'is_active': True,
            'next_available_slot': None,
            'consultation_hours_start': None,
            'consultation_hours_end': None
        }
    
    def _get_next_available_slot(self, obj):
        """Get next available time slot for doctor"""
        if not hasattr(obj, 'doctor_profile'):
            return None
            
        try:
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            # Get current time
            now = timezone.now()
            
            # Get doctor's consultation hours
            start = obj.doctor_profile.consultation_hours_start
            end = obj.doctor_profile.consultation_hours_end
            
            # Calculate next available slot
            if now.time() < start:
                return datetime.combine(now.date(), start)
            elif now.time() < end:
                return datetime.combine(now.date(), end)
            else:
                return datetime.combine(now.date() + timedelta(days=1), start)
                
        except Exception as e:
            logger.error(f"Error calculating next slot: {e}")
            return None


# Patient Admission System Serializers


class PatientAdmissionListSerializer(serializers.ModelSerializer):
    """Serializer for listing patient admissions"""
    patient_name = serializers.SerializerMethodField()
    patient_age = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    attending_doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientAdmission
        fields = [
            'id', 'admission_id', 'patient_name', 'patient_age', 'status', 
            'admission_date', 'department_name', 'attending_doctor_name',
            'is_icu_bed', 'priority', 'reason_for_admission', 'bed_identifier',
            'is_registered_patient', 'temp_patient_details'
        ]
    
    def get_patient_name(self, obj):
        # Handle both registered patients and emergency admissions
        if obj.patient:
            return obj.patient.get_full_name()
        elif obj.temp_patient_details:
            first_name = obj.temp_patient_details.get('first_name', '')
            last_name = obj.temp_patient_details.get('last_name', '')
            return f"{first_name} {last_name}".strip()
        else:
            return "Unknown Patient"
    
    def get_patient_age(self, obj):
        """Calculate patient age from different sources"""
        if obj.patient and obj.patient.date_of_birth:
            # Calculate age from registered patient's date of birth
            from datetime import date
            today = date.today()
            dob = obj.patient.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        elif obj.temp_patient_details:
            # Use age from temp patient details if available
            if obj.temp_patient_details.get('age'):
                return obj.temp_patient_details.get('age')
            # Or calculate from date_of_birth if available
            elif obj.temp_patient_details.get('date_of_birth'):
                from datetime import date
                try:
                    dob = date.fromisoformat(obj.temp_patient_details.get('date_of_birth'))
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    return age
                except:
                    pass
        return None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_attending_doctor_name(self, obj):
        return obj.attending_doctor.user.get_full_name() if obj.attending_doctor else None

class PatientAdmissionSerializer(serializers.ModelSerializer):
    """Detailed serializer for patient admissions"""
    patient_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    attending_doctor_name = serializers.SerializerMethodField()
    hospital_name = serializers.SerializerMethodField()
    current_length_of_stay = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientAdmission
        fields = [
            'id', 'admission_id', 'patient', 'patient_name',
            'hospital', 'hospital_name',
            'department', 'department_name',
            'status', 'admission_type', 'priority',
            'reason_for_admission', 'is_icu_bed', 'bed_identifier',
            'attending_doctor', 'attending_doctor_name',
            'admission_date', 'expected_discharge_date',
            'actual_discharge_date', 'length_of_stay_days',
            'current_length_of_stay', 'diagnosis', 'secondary_diagnoses',
            'acuity_level', 'isolation_required', 'isolation_type',
            'discharge_destination', 'discharge_summary',
            'followup_instructions', 'insurance_information',
            'admission_notes', 'is_registered_patient',
            'temp_patient_id', 'temp_patient_details',
            'registration_status'
        ]
        read_only_fields = ['id', 'admission_id', 'length_of_stay_days']
        
    def to_internal_value(self, data):
        logger.debug(f"Patient admission incoming data: {data}")
        # Map hospital_id to hospital and department_id to department
        if 'hospital_id' in data:
            data['hospital'] = data.pop('hospital_id')
        if 'department_id' in data:
            data['department'] = data.pop('department_id')
            
        # Handle assign_bed flag
        assign_bed = data.pop('assign_bed', False)
        result = super().to_internal_value(data)
        
        # Set flag for model to handle in save()
        if assign_bed:
            result._assign_bed_on_create = True
            
        logger.debug(f"After internal value: {result}")
        return result
    
    def get_patient_name(self, obj):
        # Handle both registered patients and emergency admissions
        if obj.patient:
            return obj.patient.get_full_name()
        elif obj.temp_patient_details:
            first_name = obj.temp_patient_details.get('first_name', '')
            last_name = obj.temp_patient_details.get('last_name', '')
            return f"{first_name} {last_name}".strip()
        else:
            return "Unknown Patient"
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_attending_doctor_name(self, obj):
        return obj.attending_doctor.user.get_full_name() if obj.attending_doctor else None
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_current_length_of_stay(self, obj):
        return obj.current_length_of_stay
        
    def to_internal_value(self, data):
        logger.debug(f"Patient admission detailed incoming data: {data}")
        result = super().to_internal_value(data)
        logger.debug(f"After internal value: {result}")
        return result

class PatientTransferSerializer(serializers.Serializer):
    """Serializer for transferring patients"""
    department_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField(required=False, allow_null=True)
    is_icu_bed = serializers.BooleanField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)

class PatientDischargeSerializer(serializers.Serializer):
    """Serializer for discharging patients"""
    discharge_destination = serializers.CharField(required=False, allow_blank=True)
    discharge_summary = serializers.CharField(required=False, allow_blank=True)
    followup_instructions = serializers.CharField(required=False, allow_blank=True)


class DepartmentSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    doctor_count = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'description',
            'hospital',
            'hospital_name',
            'created_at',
            'updated_at',
            'is_active',
            'doctor_count',
            # Add any other department fields
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'hospital_name', 'doctor_count']
        extra_kwargs = {
            'hospital': {'write_only': True}  # Hospital is write-only since we show hospital_name
        }

    def get_doctor_count(self, obj):
        """Get count of doctors in this department"""
        return obj.doctors.count() if hasattr(obj, 'doctors') else 0

    def validate_name(self, value):
        """Ensure department name is properly formatted"""
        return value.strip().title()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction model"""
    appointment_id = serializers.CharField(source='appointment.id', read_only=True)
    patient_name = serializers.SerializerMethodField()
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'transaction_id',
            'appointment_id',
            'patient_name',
            'hospital_name',
            'amount',
            'amount_display',
            'currency',
            'payment_method',
            'payment_status',
            'status_display',
            'payment_provider',
            'provider_reference',
            'gateway_transaction_id',
            'created_at',
            'completed_at',
            'description'
        ]
        read_only_fields = [
            'transaction_id', 'provider_reference', 'gateway_transaction_id',
            'created_at', 'completed_at'
        ]
    
    def get_patient_name(self, obj):
        """Get patient's full name"""
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None
    
    def get_status_display(self, obj):
        """Get human-readable status"""
        status_map = {
            'pending': 'Pending Payment',
            'processing': 'Processing',
            'completed': 'Payment Successful',
            'failed': 'Payment Failed',
            'refunded': 'Refunded'
        }
        return status_map.get(obj.payment_status, obj.payment_status)
        