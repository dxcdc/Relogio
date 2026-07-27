from django.contrib import admin
from .models import Event, QuickNote, EventType

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'organizer', 'start_date', 'end_date', 'status')
    list_filter = ('event_type', 'status', 'start_date', 'location', 'city')
    search_fields = ('title', 'notes', 'organizer__first_name', 'organizer__last_name')
    filter_horizontal = ('employees',)

@admin.register(QuickNote)
class QuickNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'content')
