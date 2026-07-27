from django.contrib import admin
from .models import LeaveRequest, LeaveActionLog, LeaveType, LeaveEntitlement


@admin.register(LeaveActionLog)
class LeaveActionLogAdmin(admin.ModelAdmin):
    list_display = ('performed_at', 'leave_request', 'action', 'performed_by', 'note_short')
    list_filter = ('action', 'performed_at')
    search_fields = ('leave_request__employee__first_name', 'leave_request__employee__last_name', 'performed_by__username', 'note')
    readonly_fields = ('leave_request', 'action', 'performed_by', 'note', 'performed_at')
    ordering = ('-performed_at',)
    date_hierarchy = 'performed_at'

    def note_short(self, obj):
        if obj.note:
            return obj.note[:60] + '...' if len(obj.note) > 60 else obj.note
        return '—'
    note_short.short_description = 'Nota'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'from_date', 'to_date', 'status', 'date_applied')
    list_filter = ('status', 'leave_type', 'date_applied')
    search_fields = ('employee__first_name', 'employee__last_name', 'leave_type__name')
    ordering = ('-date_applied',)
    date_hierarchy = 'date_applied'
