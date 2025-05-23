from api.models import CustomUser
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.utils.token_utils import build_user_token_data
from api.models.medical.hospital_registration import HospitalRegistration
from api.models import Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from api.models.medical.department import Department
from .tokens import HospitalAdminToken
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Appointment, Doctor, AppointmentFee
from datetime import datetime, timedelta
from django.utils import timezone

# Import MedicalRecord model
from api.models.medical.medical_record import MedicalRecord
from api.models.medical.medication import Medication, MedicationCatalog

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
            'preferred_language', 'secondary_languages', 'custom_language',
            'role'
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

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']

class HospitalSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    class Meta:
        model = Hospital
        fields = ['id', 'name', 'departments']

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
        required=False,
        allow_null=True
    )
    hospital_name = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    
    # Make appointment_type have a default value
    appointment_type = serializers.CharField(default='consultation', required=False)
    
    # Make chief_complaint required
    chief_complaint = serializers.CharField(required=True, error_messages={
        'required': 'Chief complaint is required to determine the appropriate department.',
        'blank': 'Chief complaint cannot be empty.'
    })
    
    # Set default for symptoms_data
    symptoms_data = serializers.JSONField(required=False, default=list)
    
    # Make appointment_id read-only since it's generated by the model
    appointment_id = serializers.CharField(read_only=True)
    
    # Make patient read-only since it's set from the current user
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # New fields to match email template format
    formatted_date = serializers.SerializerMethodField(read_only=True)
    formatted_time = serializers.SerializerMethodField(read_only=True)
    formatted_date_time = serializers.SerializerMethodField(read_only=True)
    appointment_duration_display = serializers.SerializerMethodField(read_only=True)
    important_notes = serializers.SerializerMethodField(read_only=True)
    formatted_appointment_type = serializers.SerializerMethodField(read_only=True)
    formatted_priority = serializers.SerializerMethodField(read_only=True)
    doctor_full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_id',
            'patient',
            'doctor',
            'doctor_id',
            'hospital',
            'department',
            'appointment_type',
            'priority',
            'status',
            'appointment_date',
            'duration',
            'chief_complaint',
            'symptoms',
            'symptoms_data',
            'medical_history',
            'allergies',
            'current_medications',
            'is_insurance_based',
            'insurance_details',
            'payment_required',
            'payment_status',
            'notes',
            'cancellation_reason',
            'reminder_sent',
            'last_reminder_sent',
            'cancelled_at',
            'completed_at',
            'hospital_name',
            'department_name',
            'patient_name',
            'status_display',
            'formatted_date',
            'formatted_time',
            'formatted_date_time',
            'appointment_duration_display',
            'important_notes',
            'formatted_appointment_type',
            'formatted_priority',
            'doctor_full_name'
        ]

    def create(self, validated_data):
        # Extract symptoms_data if present
        symptoms_data = validated_data.get('symptoms_data', [])
        
        # Generate symptoms text from symptoms_data
        if symptoms_data:
            symptoms_text = []
            for symptom in symptoms_data:
                body_part = symptom.get('body_part_name', '')
                symptom_name = symptom.get('symptom_name', '')
                description = symptom.get('description', '')
                symptom_text = f"{body_part} - {symptom_name}: {description}"
                symptoms_text.append(symptom_text)
            
            # Join all symptoms into a single string and add to validated_data
            validated_data['symptoms'] = "\n".join(symptoms_text)
        else:
            # If no symptoms_data provided, ensure symptoms field is at least an empty string
            validated_data['symptoms'] = ''
        
        # Create the appointment
        appointment = super().create(validated_data)
        
        # Create and send notifications immediately
        try:
            from api.models.medical.appointment_notification import AppointmentNotification
            
            # Create notifications
            email_notification = AppointmentNotification.create_booking_confirmation(appointment)
            
            # Send all pending notifications for this appointment immediately
            notifications = AppointmentNotification.objects.filter(
                appointment=appointment,
                status='pending'
            )
            
            for notification in notifications:
                notification.send()
                
            # Create reminders for future dates (these will be sent later)
            reminder_schedule = [
                {'days_before': 2, 'type': 'email'},
                {'days_before': 1, 'type': 'sms'},
                {'hours_before': 2, 'type': 'sms'}
            ]
            AppointmentNotification.create_reminders(appointment, reminder_schedule)
            
        except Exception as e:
            # Log the error but don't fail appointment creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send appointment notifications: {e}")
        
        return appointment

    def update(self, instance, validated_data):
        # Generate symptoms text from symptoms_data if present
        if 'symptoms_data' in validated_data and validated_data['symptoms_data']:
            symptoms_data = validated_data['symptoms_data']
            symptoms_text = []
            for symptom in symptoms_data:
                body_part = symptom.get('body_part_name', '')
                symptom_name = symptom.get('symptom_name', '')
                description = symptom.get('description', '')
                symptom_text = f"{body_part} - {symptom_name}: {description}"
                symptoms_text.append(symptom_text)
            validated_data['symptoms'] = "\n".join(symptoms_text)
        
        return super().update(instance, validated_data)

    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() if obj.patient else None

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_formatted_date(self, obj):
        return obj.appointment_date.strftime('%B %d, %Y') if obj.appointment_date else None

    def get_formatted_time(self, obj):
        return obj.appointment_date.strftime('%I:%M %p') if obj.appointment_date else None

    def get_formatted_date_time(self, obj):
        return obj.appointment_date.strftime('%B %d, %Y at %I:%M %p') if obj.appointment_date else None

    def get_appointment_duration_display(self, obj):
        return f"{obj.duration} minutes"

    def get_important_notes(self, obj):
        notes = []
        if obj.allergies:
            notes.append(f"Allergies: {obj.allergies}")
        if obj.medical_history:
            notes.append(f"Medical History: {obj.medical_history}")
        if obj.current_medications:
            notes.append(f"Current Medications: {obj.current_medications}")
        return "\n".join(notes) if notes else None

    def get_formatted_appointment_type(self, obj):
        return obj.get_appointment_type_display()

    def get_formatted_priority(self, obj):
        return obj.get_priority_display()

    def get_doctor_full_name(self, obj):
        if obj.doctor and obj.doctor.user:
            return obj.doctor.user.get_full_name()
        return "No Doctor Assigned"

class AppointmentListSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    hospital_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    # Add new formatted fields for list view
    formatted_date = serializers.SerializerMethodField(read_only=True)
    formatted_time = serializers.SerializerMethodField(read_only=True)
    formatted_date_time = serializers.SerializerMethodField(read_only=True)
    doctor_full_name = serializers.SerializerMethodField(read_only=True)
    formatted_appointment_type = serializers.SerializerMethodField(read_only=True)
    formatted_priority = serializers.SerializerMethodField(read_only=True)
    
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
            'created_at'
        ]
    
    def get_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    # Add the same getter methods as in AppointmentSerializer
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

class MedicationCatalogSerializer(serializers.ModelSerializer):
    """Serializer for medication catalog entries"""
    
    class Meta:
        model = MedicationCatalog
        fields = [
            'id', 'generic_name', 'brand_names', 'drug_class', 
            'available_forms', 'available_strengths', 'standard_routes',
            'indications', 'contraindications', 'side_effects',
            'warnings', 'high_alert_medication', 'is_controlled_substance'
        ]
        
class MedicationSerializer(serializers.ModelSerializer):
    """Serializer for patient medications/prescriptions"""
    catalog_details = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Medication
        fields = [
            'id', 'medication_name', 'generic_name', 'strength', 'form', 
            'route', 'dosage', 'frequency', 'start_date', 'end_date',
            'is_ongoing', 'duration', 'patient_instructions', 'indication',
            'refills_authorized', 'refills_remaining', 'status', 'status_display',
            'prescribed_by', 'doctor_name', 'catalog_details', 'patient_name',
            'pharmacy_name', 'side_effects_experienced', 'prescription_number'
        ]
        read_only_fields = ['id', 'catalog_details', 'doctor_name', 'status_display', 'patient_name']
    
    def get_catalog_details(self, obj):
        if obj.catalog_entry:
            return {
                'generic_name': obj.catalog_entry.generic_name,
                'brand_names': obj.catalog_entry.brand_names,
                'drug_class': obj.catalog_entry.drug_class,
                'is_controlled': obj.catalog_entry.is_controlled_substance,
                'high_alert': obj.catalog_entry.high_alert_medication,
                'warnings': obj.catalog_entry.warnings[:100] + '...' if len(obj.catalog_entry.warnings) > 100 else obj.catalog_entry.warnings
            }
        return None
    
    def get_doctor_name(self, obj):
        if obj.prescribed_by:
            return f"Dr. {obj.prescribed_by.user.get_full_name()}"
        return None
    
    def get_status_display(self, obj):
        return dict(Medication.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_patient_name(self, obj):
        if obj.medical_record and obj.medical_record.user:
            return obj.medical_record.user.get_full_name()
        return None

class PrescriptionSerializer(serializers.Serializer):
    """Serializer for creating new prescriptions"""
    appointment_id = serializers.CharField(required=True)
    medications = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1
    )
    
    def validate_appointment_id(self, value):
        try:
            appointment = Appointment.objects.get(appointment_id=value)
            if appointment.status not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Prescriptions can only be added to in-progress or completed appointments"
                )
            return value
        except Appointment.DoesNotExist:
            raise serializers.ValidationError(f"Appointment with ID {value} not found")
    
    def validate_medications(self, value):
        if not value:
            raise serializers.ValidationError("At least one medication is required")
        
        required_fields = ['medication_name', 'strength', 'form', 'route', 'dosage', 'frequency']
        
        for medication in value:
            for field in required_fields:
                if field not in medication:
                    raise serializers.ValidationError(f"Field '{field}' is required for each medication")
            
            # Validate start_date if provided
            if 'start_date' in medication:
                try:
                    start_date = datetime.strptime(medication['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    raise serializers.ValidationError("start_date must be in YYYY-MM-DD format")
            
            # Validate end_date if provided
            if 'end_date' in medication:
                try:
                    end_date = datetime.strptime(medication['end_date'], '%Y-%m-%d').date()
                    
                    # If start_date is also provided, validate end_date is after start_date
                    if 'start_date' in medication:
                        start_date = datetime.strptime(medication['start_date'], '%Y-%m-%d').date()
                        if end_date < start_date:
                            raise serializers.ValidationError("end_date must be after start_date")
                except ValueError:
                    raise serializers.ValidationError("end_date must be in YYYY-MM-DD format")
        
        return value     