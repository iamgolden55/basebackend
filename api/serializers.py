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
    full_name = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'date_of_birth', 'gender', 'country', 'city', 'phone', 'state',
            'nin', 'consent_terms', 'consent_hipaa', 'consent_data_processing', 'full_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_nin(self, value):
        if CustomUser.objects.filter(nin=value).exists():
            raise serializers.ValidationError("This NIN is already registered. Please provide a unique NIN.")
        return value

    def validate(self, data):
        # Check if the country is Nigeria and NIN is required
        if data.get('country', '').strip().lower() == 'nigeria':
            if not data.get('nin'):
                raise serializers.ValidationError({
                    'nin': "NIN is required for users from Nigeria."
                })
            # Optional: Validate NIN format here if needed (e.g., length, digits)
            if len(data['nin']) != 11 or not data['nin'].isdigit():
                raise serializers.ValidationError({
                    'nin': "NIN must be an 11-digit number."
                })
        return data

    def create(self, validated_data):
        # Split full_name into first_name and last_name
        full_name = validated_data.pop('full_name')
        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')

        # Create user with the validated data
        user = CustomUser.objects.create_user(
        first_name=first_name,  # Add this! 🌟
        last_name=last_name,    # And this! 🌟
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