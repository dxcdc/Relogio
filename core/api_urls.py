from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from .api_views import (
    MeView,
    RegisterFCMTokenView,
    UnregisterFCMTokenView,
    AppNotificationView,
    MarkNotificationReadView,
    ForgotPasswordRequestView,
    ForgotPasswordVerifyView,
    ForgotPasswordNewPasswordView
)

urlpatterns = [
    # ...
    path('token/', TokenObtainPairView.as_view(), name='api-token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('token/logout/', TokenBlacklistView.as_view(), name='api-token-logout'),

    # ...
    path('me/', MeView.as_view(), name='api-auth-me'),

    # ...
    path('register-fcm-token/', RegisterFCMTokenView.as_view(), name='api-register-fcm-token'),
    path('unregister-fcm-token/', UnregisterFCMTokenView.as_view(), name='api-unregister-fcm-token'),
    
    path('notifications/', AppNotificationView.as_view(), name='api-notifications'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='api-notification-read'),

    # Password Recovery
    path('forgot-password/', ForgotPasswordRequestView.as_view(), name='api-forgot-password'),
    path('forgot-password/verify/', ForgotPasswordVerifyView.as_view(), name='api-forgot-password-verify'),
    path('forgot-password/new-password/', ForgotPasswordNewPasswordView.as_view(), name='api-forgot-password-new'),
]
