from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    CustomLoginView, AdminLoginView, SignupView, CustomLogoutView,
    profile_view, verify_email
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify-email'),
    
    # Password Reset URLs
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
            html_email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            extra_context={'site_name': 'Masbate Provincial Veterinary Office'}
        ),
        name='password_reset'),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'
        ),
        name='password_reset_confirm'),
    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'),
        
    # Admin Password Reset
    path('admin/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/admin_password_reset.html',
            html_email_template_name='users/admin_password_reset_email.html'
        ),
        name='admin_password_reset'),
        
    # Admin Login
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
]