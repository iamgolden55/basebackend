from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # Try to authenticate with email if provided
        if email:
            try:
                user = UserModel.objects.get(email=email)
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None
        
        # Fall back to username authentication
        if username:
            try:
                # Try to find user by username or email
                user = UserModel.objects.get(
                    Q(username=username) | Q(email=username)
                )
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None
        
        return None
