from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import OrangeUser, AuditLog


@admin.register(OrangeUser)
class OrangeUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Controles Netgram', {'fields': ('is_netgram_suspended', 'blocked_users')}),
    )
    filter_horizontal = UserAdmin.filter_horizontal + ('blocked_users',)



@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'user', 'ip_address', 'description_short')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def description_short(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_short.short_description = 'Descrição'

    def has_add_permission(self, request):
        return False  

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  
