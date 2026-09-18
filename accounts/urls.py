from django.urls import path
from django.contrib.auth import views as auth_views
from .import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),  # Admin-only user creation
    path('request-access/', views.request_access, name='request_access'),  # Public access request form
    path('system-settings/', views.system_settings, name='system_settings'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Access Request Management (Admin-only)
    path('access-requests/', views.access_request_list, name='access_request_list'),
    path('access-request/<int:pk>/', views.access_request_detail, name='access_request_detail'),
    path('access-request/<int:pk>/approve/', views.approve_access_request, name='approve_access_request'),
    path('access-request/<int:pk>/reject/', views.reject_access_request, name='reject_access_request'),
    path('email-management/', views.email_management, name='email_management'),

    # Password reset views
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.txt',   # ✅ PLAIN TEXT
            html_email_template_name='accounts/password_reset_email.html',  # ✅ HTML VERSION
            subject_template_name='accounts/password_reset_subject.txt'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
     