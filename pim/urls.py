from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('export/', views.employee_export, name='employee_export'),
    path('add/', views.employee_create, name='employee_create'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/personal/', views.employee_personal_edit, name='employee_personal_edit'),
    path('<int:pk>/job/', views.employee_job_edit, name='employee_job_edit'),
    path('<int:pk>/contact/', views.employee_contact_edit, name='employee_contact_edit'),
    path('<int:pk>/photo/', views.employee_photo_upload, name='employee_photo_upload'),
    path('<int:pk>/terminate/', views.terminate_employee, name='terminate_employee'),

    
    path('<int:emp_pk>/dependents/add/', views.dependent_create, name='dependent_create'),
    path('dependents/<int:pk>/edit/', views.dependent_edit, name='dependent_edit'),
    path('dependents/<int:pk>/delete/', views.dependent_delete, name='dependent_delete'),

    
    path('<int:emp_pk>/emergency/add/', views.emergency_contact_create, name='emergency_contact_create'),
    path('emergency/<int:pk>/edit/', views.emergency_contact_edit, name='emergency_contact_edit'),
    path('emergency/<int:pk>/delete/', views.emergency_contact_delete, name='emergency_contact_delete'),

    
    path('<int:emp_pk>/experience/add/', views.work_experience_create, name='work_experience_create'),
    path('experience/<int:pk>/edit/', views.work_experience_edit, name='work_experience_edit'),
    path('experience/<int:pk>/delete/', views.work_experience_delete, name='work_experience_delete'),

    
    path('<int:emp_pk>/education/add/', views.education_create, name='education_create'),
    path('education/<int:pk>/edit/', views.education_edit, name='education_edit'),
    path('education/<int:pk>/delete/', views.education_delete, name='education_delete'),

    
    path('<int:emp_pk>/skills/add/', views.skill_create, name='skill_create'),
    path('skills/<int:pk>/edit/', views.skill_edit, name='skill_edit'),
    path('skills/<int:pk>/delete/', views.skill_delete, name='skill_delete'),

    
    path('<int:emp_pk>/languages/add/', views.language_create, name='language_create'),
    path('languages/<int:pk>/edit/', views.language_edit, name='language_edit'),
    path('languages/<int:pk>/delete/', views.language_delete, name='language_delete'),

    
    path('<int:emp_pk>/licenses/add/', views.license_create, name='license_create'),
    path('licenses/<int:pk>/edit/', views.license_edit, name='license_edit'),
    path('licenses/<int:pk>/delete/', views.license_delete, name='license_delete'),

    
    path('<int:emp_pk>/memberships/add/', views.membership_create, name='membership_create'),
    path('memberships/<int:pk>/edit/', views.membership_edit, name='membership_edit'),
    path('memberships/<int:pk>/delete/', views.membership_delete, name='membership_delete'),

    
    path('<int:emp_pk>/immigration/add/', views.immigration_create, name='immigration_create'),
    path('immigration/<int:pk>/edit/', views.immigration_edit, name='immigration_edit'),
    path('immigration/<int:pk>/delete/', views.immigration_delete, name='immigration_delete'),

    
    path('<int:emp_pk>/salary/add/', views.salary_create, name='salary_create'),
    path('salary/<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('salary/<int:pk>/delete/', views.salary_delete, name='salary_delete'),

    
    path('<int:emp_pk>/contract/add/', views.contract_create, name='contract_create'),
    path('contract/<int:pk>/delete/', views.contract_delete, name='contract_delete'),

    
    path('org-chart/', views.organization_chart, name='org_chart_view'),
    path('onboarding/', views.employee_onboarding_dashboard, name='employee_onboarding_dashboard'),
]
