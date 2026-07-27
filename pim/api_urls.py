from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import EmployeeViewSet, DashboardAPIView, MyProfileAPIView, CitiesAPIView, OnboardingAPIView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view(), name='api-dashboard'),
    path('profile/', MyProfileAPIView.as_view(), name='api-profile'),
    path('cities/', CitiesAPIView.as_view(), name='api-cities'),
    path('employees/onboarding/', OnboardingAPIView.as_view(), name='api-onboarding'),
    path('', include(router.urls)),
]
