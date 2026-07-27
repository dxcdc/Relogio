from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='agenda_calendar'),
    path('api/events/', views.list_events, name='agenda_list_events'),
    path('api/events/create/', views.create_event, name='agenda_create_event'),
    path('api/events/<int:event_id>/update/', views.update_event, name='agenda_update_event'),
    path('api/events/<int:event_id>/delete/', views.delete_event, name='agenda_delete_event'),
    path('api/events/<int:event_id>/cancel/', views.cancel_event, name='agenda_cancel_event'),
    path('api/events/<int:event_id>/export-ics/', views.export_event_ics, name='agenda_export_event_ics'),
    path('api/notes/create/', views.create_quick_note, name='agenda_create_quick_note'),
    path('api/notes/<int:note_id>/delete/', views.delete_quick_note, name='agenda_delete_quick_note'),
    path('api/notes/<int:note_id>/update/', views.update_quick_note, name='agenda_update_quick_note'),
    path('api/locations/create/', views.create_location, name='agenda_create_location'),
    path('api/event-types/create/', views.create_event_type, name='agenda_create_event_type'),
    path('salas/', views.manage_locations, name='agenda_manage_locations'),
    path('tipos/', views.manage_event_types, name='agenda_manage_event_types'),
    path('lembretes/', views.manage_quick_notes, name='agenda_manage_quick_notes'),
]
