from django.urls import path
from . import views

urlpatterns = [
    path('', views.organization_view, name='organization'),
    
    path('legal-entities/', views.legal_entity_list, name='legal_entity_list'),
    path('legal-entities/add/', views.legal_entity_create, name='legal_entity_create'),
    path('legal-entities/<int:pk>/edit/', views.legal_entity_edit, name='legal_entity_edit'),
    
    path('locations/', views.location_list, name='location_list'),
    path('locations/add/', views.location_create, name='location_create'),
    path('locations/<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:pk>/delete/', views.delete_generic, {'model_name': 'location'}, name='location_delete'),
    
    path('cities/', views.city_list, name='city_list'),
    path('cities/add/', views.city_create, name='city_create'),
    path('cities/<int:pk>/edit/', views.city_edit, name='city_edit'),
    path('cities/<int:pk>/delete/', views.delete_generic, {'model_name': 'city'}, name='city_delete'),
    
    path('subunits/', views.subunit_list, name='subunit_list'),
    path('subunits/add/', views.subunit_create, name='subunit_create'),
    path('subunits/<int:pk>/edit/', views.subunit_edit, name='subunit_edit'),
    path('subunits/<int:pk>/delete/', views.delete_generic, {'model_name': 'subunit'}, name='subunit_delete'),
    
    path('job-titles/', views.job_title_list, name='job_title_list'),
    path('job-titles/add/', views.job_title_create, name='job_title_create'),
    path('job-titles/<int:pk>/edit/', views.job_title_edit, name='job_title_edit'),
    path('job-titles/<int:pk>/delete/', views.delete_generic, {'model_name': 'job_title'}, name='job_title_delete'),
    
    path('job-categories/', views.job_category_list, name='job_category_list'),
    path('job-categories/<int:pk>/edit/', views.job_category_edit, name='job_category_edit'),
    path('job-categories/<int:pk>/delete/', views.delete_generic, {'model_name': 'job_category'}, name='job_category_delete'),
    
    path('work-shifts/', views.work_shift_list, name='work_shift_list'),
    path('work-shifts/add/', views.work_shift_create, name='work_shift_create'),
    path('work-shifts/<int:pk>/edit/', views.work_shift_edit, name='work_shift_edit'),
    path('work-shifts/<int:pk>/delete/', views.delete_generic, {'model_name': 'work_shift'}, name='work_shift_delete'),
    
    path('nationalities/', views.nationality_list, name='nationality_list'),
    path('nationalities/<int:pk>/edit/', views.nationality_edit, name='nationality_edit'),
    path('nationalities/<int:pk>/delete/', views.delete_generic, {'model_name': 'nationality'}, name='nationality_delete'),
    path('skills/', views.skill_list, name='skill_list'),
    path('skills/<int:pk>/edit/', views.skill_edit, name='skill_edit'),
    path('skills/<int:pk>/delete/', views.delete_generic, {'model_name': 'skill'}, name='skill_delete'),
    path('languages/', views.language_list, name='language_list'),
    path('languages/<int:pk>/edit/', views.language_edit, name='language_edit'),
    path('languages/<int:pk>/delete/', views.delete_generic, {'model_name': 'language'}, name='language_delete'),
    path('licenses/', views.license_list, name='license_list'),
    path('licenses/<int:pk>/edit/', views.license_edit, name='license_edit'),
    path('licenses/<int:pk>/delete/', views.delete_generic, {'model_name': 'license'}, name='license_delete'),
    path('memberships/', views.membership_list, name='membership_list'),
    path('memberships/<int:pk>/edit/', views.membership_edit, name='membership_edit'),
    path('memberships/<int:pk>/delete/', views.delete_generic, {'model_name': 'membership'}, name='membership_delete'),
    path('education/', views.education_list, name='education_list'),
    path('education/<int:pk>/edit/', views.education_edit, name='education_edit'),
    path('education/<int:pk>/delete/', views.delete_generic, {'model_name': 'education'}, name='education_delete'),
    path('employment-status/', views.employment_status_list, name='employment_status_list'),
    path('employment-status/<int:pk>/edit/', views.employment_status_edit, name='employment_status_edit'),
    path('employment-status/<int:pk>/delete/', views.delete_generic, {'model_name': 'employment_status'}, name='employment_status_delete'),
    path('pay-grades/', views.pay_grade_list, name='pay_grade_list'),
    path('pay-grades/add/', views.pay_grade_create, name='pay_grade_create'),
    path('pay-grades/<int:pk>/edit/', views.pay_grade_edit, name='pay_grade_edit'),
    path('pay-grades/<int:pk>/delete/', views.delete_generic, {'model_name': 'pay_grade'}, name='pay_grade_delete'),
    
    path('termination-reasons/', views.termination_reason_list, name='termination_reason_list'),
    path('termination-reasons/<int:pk>/edit/', views.termination_reason_edit, name='termination_reason_edit'),
    path('termination-reasons/<int:pk>/delete/', views.delete_generic, {'model_name': 'termination_reason'}, name='termination_reason_delete'),
    
    path('delete/<str:model_name>/<int:pk>/', views.delete_generic, name='delete_generic'),
]
