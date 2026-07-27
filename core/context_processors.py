import os
from django.core.cache import cache


def notifications_processor(request):
    """Context processor to inject unread notification info into all templates."""
    if request.user.is_authenticated:
        cache_key = f'notif_ctx_{request.user.pk}'
        cached = cache.get(cache_key)
        if cached is None:
            # select_related evita N+1 se templates renderizarem campos relacionados
            unread_notifications = list(
                request.user.notifications.filter(is_read=False).order_by('-id')[:50]
            )
            unread_count = len(unread_notifications)

            unread_bugs_count = 0
            pending_reports_count = 0
            if request.user.is_admin() or request.user.is_hr():
                try:
                    from buzz.models import BugReport, ContentReport
                    unread_bugs_count = BugReport.objects.filter(
                        status__in=['OPEN', 'ANALYZING']
                    ).count()
                    pending_reports_count = ContentReport.objects.filter(
                        status='PENDING'
                    ).count()
                except Exception:
                    pass

            cached = {
                'unread_notifications': unread_notifications,
                'unread_count': unread_count,
                'unread_bugs_count': unread_bugs_count,
                'pending_reports_count': pending_reports_count,
            }
            # Cache de 30s — curto o suficiente para notificações aparecerem rapidamente,
            # mas evita query em cada navegação entre páginas.
            cache.set(cache_key, cached, 30)

        return cached
    return {}


def module_permissions_processor(request):
    """Injeta as permissões modulares na sessão.
    
    Usa cache em memória para evitar query ao banco em toda requisição.
    O cache é invalidado após 5 minutos — tempo suficiente para qualquer mudança
    de permissão ser refletida rapidamente sem overhead constante.
    """
    context = {}
    if not request.user.is_authenticated:
        return context

    # Cache key único por usuário + role (invalida automaticamente se o role mudar)
    cache_key = f'module_perms_{request.user.pk}_{request.user.role}'
    cached_modules = cache.get(cache_key)

    if cached_modules is None:
        from core.models import RoleModuleAccess
        from django.forms.models import model_to_dict
        try:
            acc = RoleModuleAccess.objects.get(role=request.user.role)
            cached_modules = model_to_dict(acc)
        except Exception:
            cached_modules = {
                'netgram': True, 'org_chart': True, 'attendance': True, 'leave': True,
                'swap': True, 'claim': True, 'performance': True, 'agenda': True,
                'endpoints': True, 'team_employees': True, 'team_approvals': True,
                'team_attendance': True, 'admin_core': True, 'admin_attendance': True,
                'audit': True, 'integrations': True, 'reports': True,
                'announcements': True, 'support_tickets': True
            }
        # Salva no cache por 5 minutos
        cache.set(cache_key, cached_modules, 300)

    context['user_modules'] = cached_modules

    # Feature flags lidos uma vez e cacheados (são constantes de env — nunca mudam em runtime)
    context['EXIBIR_AGENDA_WEB'] = os.environ.get('EXIBIR_AGENDA_WEB', 'False') == 'True'
    context['EXIBIR_INTEGRACOES_WEB'] = os.environ.get('EXIBIR_INTEGRACOES_WEB', 'False') == 'True'

    return context
