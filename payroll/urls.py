from django.urls import path
from . import views

urlpatterns = [
    path('', views.payroll_dashboard, name='payroll_dashboard'),
    path('payslip/<int:pk>/', views.payslip_detail, name='payslip_detail'),
    path('payslip/<int:pk>/sign/', views.payslip_sign, name='payslip_sign'),
    path('payslip/<int:pk>/delete/', views.payslip_delete, name='payslip_delete'),
    path('payslips/delete-all/<int:year>/<int:month>/', views.payslip_delete_all, name='payslip_delete_all'),
]
