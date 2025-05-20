from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class ApprovalBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                if user.is_superuser or user.is_staff:
                    return user
                if user.is_verified and user.is_active:
                    return user
        except User.DoesNotExist:
            return None