from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from users.views import CustomLoginView, AdminLoginView, CustomLogoutView, verify_email, profile_view

# Override the default admin login
admin.site.login = AdminLoginView.as_view()

def home_view(request):
    return render(request, 'home.html')

urlpatterns = [
    path('admin/', admin.site.urls),  # Make sure there's a trailing slash
    
    # Home
    path('', home_view, name='home'),
    
    # Authentication
    path('login/', CustomLoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile
    path('profile/', profile_view, name='profile'),
    
    # Apps
    path('vet-supplies/', include('vet_supplies.urls')),
    path('office-supplies/', include('office_supplies.urls')),
    path('reports/', include('reports.urls')),
    path('users/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)