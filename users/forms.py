from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class UserLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_verified:
            raise ValidationError("Email not verified.", code='unverified')
        if not user.is_active:
            raise ValidationError("Account inactive.", code='inactive')

class AdminLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_staff and not user.is_superuser:
            raise ValidationError("Admin access required.", code='not_admin')
        if not user.is_active:
            raise ValidationError("Account inactive.", code='inactive')