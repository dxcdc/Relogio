from django.urls import path
from . import views



urlpatterns = [
    path('email', views.teste_email_resend, name='emails'),
    path('templates/', views.email_template_list, name='email_template_list'),
    path('templates/<int:pk>/editar/', views.email_template_edit, name='email_template_edit'),
]