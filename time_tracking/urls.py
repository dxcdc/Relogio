from django.urls import path
from . import views

urlpatterns = [
    path('timesheets/', views.timesheet_list, name='timesheet_list'),
    path('timesheets/add/', views.timesheet_create, name='timesheet_create'),
    path('timesheets/<int:pk>/', views.timesheet_detail, name='timesheet_detail'),
    path('timesheets/<int:pk>/delete/', views.timesheet_delete, name='timesheet_delete'),
    path('timesheets/<int:pk>/submit/', views.timesheet_submit, name='timesheet_submit'),
    path('timesheets/<int:pk>/approve/', views.timesheet_approve, name='timesheet_approve'),
    path('timesheets/<int:pk>/reject/', views.timesheet_reject, name='timesheet_reject'),
    path('timesheets/<int:ts_pk>/add-item/', views.timesheet_item_add, name='timesheet_item_add'),
    path('items/<int:pk>/delete/', views.timesheet_item_delete, name='timesheet_item_delete'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/add/', views.project_create, name='project_create'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
]
