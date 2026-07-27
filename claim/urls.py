from django.urls import path
from . import views

urlpatterns = [
    path('', views.claim_list, name='claim_list'),
    path('add/', views.claim_create, name='claim_create'),
    path('<int:pk>/', views.claim_detail, name='claim_detail'),
    path('<int:pk>/submit/', views.claim_submit, name='claim_submit'),
    path('<int:pk>/approve/', views.claim_approve, name='claim_approve'),
    path('<int:pk>/final-approve/', views.claim_final_approve, name='claim_final_approve'),
    path('<int:pk>/reject/', views.claim_reject, name='claim_reject'),
    path('<int:pk>/delete/', views.claim_delete, name='claim_delete'),
    
    path('<int:claim_pk>/expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    path('events/', views.event_list, name='event_list'),
    path('events/add/', views.event_create, name='event_create'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    
    path('expense-types/', views.expense_type_list, name='expense_type_list'),
    path('expense-types/add/', views.expense_type_create, name='expense_type_create'),
    path('expense-types/<int:pk>/edit/', views.expense_type_edit, name='expense_type_edit'),
    path('expense-types/<int:pk>/delete/', views.expense_type_delete, name='expense_type_delete'),
    
    path('<int:claim_pk>/attachments/upload/', views.attachment_upload, name='attachment_upload'),
    path('attachments/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),
]
