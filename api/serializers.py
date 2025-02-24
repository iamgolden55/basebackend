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

    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'date_of_birth', 'gender', 'country', 'city', 'phone', 'state',
            'nin', 'consent_terms', 'consent_hipaa', 'consent_data_processing', 'full_name'
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
    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'email',
            'phone', 'country', 
            'state', 'city', 'hpn', 'nin', 'date_of_birth', 'gender'
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
            'has_completed_onboarding': user.has_completed_onboarding
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

    class Meta:
        model = HospitalRegistration
        fields = [
            'id',
            'user',
            'hospital',
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
        password = validated_data.pop('password')
        admin = HospitalAdmin.objects.create_hospital_admin(
            password=password,
            **validated_data
        )
        return admin          