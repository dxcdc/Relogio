from django.contrib import admin
from django.utils import timezone
from .models import ContentReport


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    """
    Painel de moderação de denúncias do Netgram.
    Exigido pela Apple App Store Guideline 1.2 — User-Generated Content.
    ⚠️  Denúncias pendentes devem ser analisadas em até 24h.
    """
    list_display = (
        'id',
        'content_type',
        'content_id',
        'reason_short',
        'reported_by',
        'status',
        'created_at',
    )
    list_filter = ('status', 'content_type')
    search_fields = ('reason', 'reported_by__first_name', 'reported_by__last_name')
    readonly_fields = ('content_type', 'content_id', 'reason', 'reported_by', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_resolved', 'mark_dismissed', 'mark_reviewing']

    fieldsets = (
        ('📋 Denúncia', {
            'fields': ('content_type', 'content_id', 'reason', 'reported_by', 'created_at')
        }),
        ('⚖️ Moderação', {
            'fields': ('status', 'moderator_note', 'resolved_at')
        }),
    )

    def reason_short(self, obj):
        return obj.reason[:60] + ('...' if len(obj.reason) > 60 else '')
    reason_short.short_description = 'Motivo'

    @admin.action(description='✅ Marcar como Resolvido (conteúdo removido)')
    def mark_resolved(self, request, queryset):
        queryset.update(status=ContentReport.STATUS_RESOLVED, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} denúncia(s) marcada(s) como resolvida(s).')

    @admin.action(description='🗄️ Arquivar (sem violação)')
    def mark_dismissed(self, request, queryset):
        queryset.update(status=ContentReport.STATUS_DISMISSED, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} denúncia(s) arquivada(s).')

    @admin.action(description='🔍 Marcar como Em Análise')
    def mark_reviewing(self, request, queryset):
        queryset.update(status=ContentReport.STATUS_REVIEWING)
        self.message_user(request, f'{queryset.count()} denúncia(s) marcada(s) como em análise.')
