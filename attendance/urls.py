from django.urls import path
from . import views
from . import views_swap
from . import views_roster
from . import views_timebank
from . import payroll_views

urlpatterns = [
    path('adjustment/<int:pk>/approve/', views.adjustment_approve_action, name='adjustment_approve_action'),
    path('adjustment/<int:pk>/reject/', views.adjustment_reject_action, name='adjustment_reject_action'),

    
    path('punch/pending/', views.pending_punch_list, name='pending_punch_list'),
    path('punch/pending/<int:pk>/approve/', views.pending_punch_approve, name='pending_punch_approve'),
    path('punch/pending/<int:pk>/reject/', views.pending_punch_reject, name='pending_punch_reject'),

    
    path('', views.attendance_list, name='attendance_list'),
    path('reports/', views.admin_reports, name='attendance_reports'),
    path('my/', views.attendance_my, name='attendance_my'),
    path('my/calendar/', views.attendance_my_calendar, name='attendance_my_calendar'),
    path('my/stats/', views.attendance_stats, name='attendance_stats'),
    path('my/time-bank/', views_timebank.time_bank_modal, name='time_bank_modal'),
    path('record/<int:pk>/delete/', views.attendance_record_delete, name='attendance_record_delete'),
    path('punch/', views.punch_action, name='punch_action'),
    path('punch/status.json', views.punch_status_json, name='punch_status_json'),


    
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/new/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    
    path('employee/<int:emp_pk>/assign-schedule/', views.assign_schedule, name='assign_schedule'),

    
    path('adjustments/', views.adjustment_list, name='adjustment_list'),
    path('adjustments/new/', views.adjustment_create, name='adjustment_create'),
    path('adjustments/<int:pk>/approve/', views.adjustment_approve, name='adjustment_approve'),
    path('adjustments/<int:pk>/reject/', views.adjustment_reject, name='adjustment_reject'),

    
    path('shift-patterns/', views.shift_pattern_list, name='shift_pattern_list'),
    path('shift-patterns/new/', views.shift_pattern_create, name='shift_pattern_create'),
    path('shift-patterns/<int:pk>/edit/', views.shift_pattern_edit, name='shift_pattern_edit'),
    path('shift-patterns/<int:pk>/delete/', views.shift_pattern_delete, name='shift_pattern_delete'),

    
    path('shift-assignments/', views.shift_assignment_list, name='shift_assignment_list'),
    path('shift-assignments/new/', views.shift_assignment_create, name='shift_assignment_create'),
    path('shift-assignments/<int:pk>/delete/', views.shift_assignment_delete, name='shift_assignment_delete'),

    
    path('shift-overrides/', views.shift_override_list, name='shift_override_list'),
    path('shift-overrides/new/', views.shift_override_create, name='shift_override_create'),
    path('shift-overrides/<int:pk>/delete/', views.shift_override_delete, name='shift_override_delete'),

    
    path('swap/request/', views_swap.swap_request_create, name='swap_request_create'),
    path('swap/inbox/', views_swap.swap_inbox_data, name='swap_inbox_data'),
    path('swap/resolve/', views_swap.swap_request_resolve, name='swap_request_resolve'),
    path('swap/minhas-trocas/', views_swap.swap_inbox_page, name='swap_inbox_page'),
    path('swap/schedules/<int:request_id>/', views_swap.api_swap_schedules, name='api_swap_schedules'),

    
    path('roster/', views_roster.roster_builder, name='roster_builder'),
    path('roster/api/fetch/', views_roster.api_roster_fetch, name='api_roster_fetch'),
    path('roster/api/update/', views_roster.api_roster_update, name='api_roster_update'),
    path('roster/api/export-excel/', views_roster.api_export_roster_excel, name='api_export_roster_excel'),
    path('roster/api/import-excel/', views_roster.api_import_roster_excel, name='api_import_roster_excel'),
    path('roster/calendar/feed/<str:signed_token>/feed.ics', views_roster.roster_calendar_feed, name='roster_calendar_feed'),

    
    path('payroll/closing/', payroll_views.payroll_closing_list, name='payroll_closing_list'),
    path('payroll/closing/close/', payroll_views.payroll_close_month, name='payroll_close_month'),
    path('payroll/closing/export/', payroll_views.payroll_export_excel, name='payroll_export_excel'),
    path('payroll/settings/', payroll_views.payroll_settings, name='payroll_settings'),
]
