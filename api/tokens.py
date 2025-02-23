from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.models import TokenUser
from rest_framework_simplejwt.settings import api_settings
from datetime import timedelta

class CustomTokenUser(TokenUser):
    @property
    def is_hospital_admin(self):
        return self.token.get('is_hospital_admin', False)

class HospitalAdminToken(Token):
    token_type = 'access'
    lifetime = api_settings.ACCESS_TOKEN_LIFETIME
    
    @property
    def user(self):
        return CustomTokenUser(self.payload) 