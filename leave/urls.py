from django.urls import path
from . import views

urlpatterns = [
    path('', views.leave_list, name='leave_list'),
    path('calendar/', views.my_absences_calendar, name='my_absences_calendar'),
    path('add/', views.leave_create, name='leave_create'),
    path('<int:pk>/', views.leave_detail, name='leave_detail'),
    path('<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('<int:pk>/cancel/', views.leave_cancel, name='leave_cancel'),
    path('<int:pk>/comment/', views.leave_comment_add, name='leave_comment_add'),
    
    path('types/', views.leave_type_list, name='leave_type_list'),
    path('types/add/', views.leave_type_create, name='leave_type_create'),
    path('types/<int:pk>/edit/', views.leave_type_edit, name='leave_type_edit'),
    path('types/<int:pk>/delete/', views.leave_type_delete, name='leave_type_delete'),
    
    path('entitlements/', views.leave_entitlement_list, name='leave_entitlement_list'),
    path('entitlements/add/', views.leave_entitlement_create, name='leave_entitlement_create'),
    path('entitlements/<int:pk>/edit/', views.leave_entitlement_edit, name='leave_entitlement_edit'),
    path('entitlements/<int:pk>/delete/', views.leave_entitlement_delete, name='leave_entitlement_delete'),
    
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/add/', views.holiday_create, name='holiday_create'),
    path('holidays/<int:pk>/edit/', views.holiday_edit, name='holiday_edit'),
    path('holidays/<int:pk>/delete/', views.holiday_delete, name='holiday_delete'),
]
