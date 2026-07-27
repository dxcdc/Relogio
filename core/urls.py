from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views
from . import views_google
from .docs_view import docs_page, guia_dev_page

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='home'),
    path('login/', views.OrangeLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),

    
    path('forgot-password/', views.password_reset_request, name='password_reset_request'),
    path('forgot-password/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('forgot-password/new-password/', views.password_reset_new, name='password_reset_new'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('docs/', docs_page, name='docs'),
    path('docs/guia-dev/', guia_dev_page, name='guia_dev'),

    
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    
    path('audit-log/', views.audit_log, name='audit_log'),

    
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/new/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/like/', views.announcement_like_toggle, name='announcement_like_toggle'),
    path('announcements/<int:pk>/comment/', views.announcement_comment_add, name='announcement_comment_add'),

    
    path('module-permissions/', views.module_permissions_list, name='module_permissions_list'),
    path('integrations/', views.integrations_dashboard, name='integrations'),
    path('integrations/save-cloudinary/', views.save_cloudinary_integration, name='save_cloudinary_integration'),
    path('integrations/save-s3/', views.save_s3_integration, name='save_s3_integration'),
    
    # Integrações Google OAuth 2.0
    path('google-auth/login/', views_google.google_login_init, name='google_login_init'),
    path('google-auth/callback/', views_google.google_login_callback, name='google_login_callback'),
    path('google-auth/disconnect/', views_google.google_integration_disconnect, name='google_integration_disconnect'),
]
