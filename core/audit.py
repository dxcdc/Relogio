"""
Helper centralizado para gravar entradas no AuditLog.
Uso: from core.audit import log_action
     log_action(request, 'USER_CREATE', 'Usuário fulano criado')
"""


def _get_ip(request):
    """Extrai o IP real do request, considerando proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action, description=''):
    """
    Grava uma entrada no AuditLog.

    :param request:     HttpRequest (usado para obter user e IP)
    :param action:      Código da ação (ex: 'USER_CREATE', conforme AuditLog.ACTION_CHOICES)
    :param description: Texto livre descrevendo o que ocorreu
    """
    try:
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user if request and request.user.is_authenticated else None,
            action=action,
            description=description,
            ip_address=_get_ip(request) if request else None,
        )
    except Exception:
        pass  
