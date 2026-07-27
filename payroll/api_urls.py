from django.urls import path
from .api_views import PayslipListAPIView, PayslipSignAPIView

urlpatterns = [
    path('payslips/', PayslipListAPIView.as_view(), name='api_payslip_list'),
    path('payslips/<int:pk>/sign/', PayslipSignAPIView.as_view(), name='api_payslip_sign'),
]
