from django.utils import timezone
from django.core.cache import cache
from .models import AttendanceRecord, PendingPunchRequest


def _build_punch_context(emp, request):
    """Monta o contexto de ponto a partir do banco — chamado só quando o cache expira."""
    today = timezone.localtime(timezone.now()).date()

    from .models import get_work_info_for_date
    work_info = get_work_info_for_date(emp, today)
    theo_minutes = work_info.get('theo_minutes', 0)

    # prefetch_related evita query extra ao acessar .punches
    record = (
        AttendanceRecord.objects
        .filter(employee=emp, date=today)
        .prefetch_related('punches')
        .first()
    )
    if record:
        record._prefetched_work_info = work_info

    pending = PendingPunchRequest.objects.filter(
        employee=emp,
        status=PendingPunchRequest.STATUS_PENDING,
        requested_at__date=today,
    ).order_by('-requested_at').first()

    worked_min = 0
    is_ticking = False
    punch_is_pending = False
    next_action = 'IN'
    worked_sec = 0

    if record:
        worked_min = record.net_minutes_worked
        worked_sec = int(worked_min * 60)
        current_state = record.current_state
        if current_state == 'IN':
            is_ticking = True
            next_action = 'OUT'

    elif pending:
        if pending.action_type == 'IN':
            worked_sec = (timezone.now() - pending.requested_at).total_seconds()
            is_ticking = True
        punch_is_pending = True
        next_action = 'DONE'

    block_reason = "Bloqueado"
    work_info_source = work_info.get('source', '')
    if work_info_source == 'leave':
        next_action = 'DONE'
        block_reason = work_info.get('title', 'Licença')
    elif work_info_source == 'holiday':
        next_action = 'DONE'
        block_reason = work_info.get('title', 'Feriado')
    elif not work_info.get('is_work_day') and not record:
        next_action = 'DONE'
        block_reason = "Folga"

    worked_sec = max(0, worked_sec)
    h = int(worked_sec // 3600)
    m = int((worked_sec % 3600) // 60)
    s = int(worked_sec % 60)
    worked_str = f"{h:02d}:{m:02d}:{s:02d}"

    theo_h = int(theo_minutes // 60)
    theo_m = int(theo_minutes % 60)
    theo_str = f"{theo_h:02d}:{theo_m:02d}:00" if theo_minutes > 0 else "00:00:00"

    punch_count = 0
    if record:
        punches_list = list(record.punches.all())
        punch_count = len(punches_list)

    require_photo_all = False
    if request.user and getattr(request.user, 'role', None):
        cache_key = f'module_perms_{request.user.pk}_{request.user.role}'
        acc_data = cache.get(cache_key)
        if acc_data is not None:
            require_photo_all = acc_data.get('attendance_photo_all_punches', False)
        else:
            from core.models import RoleModuleAccess
            acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
            if acc:
                require_photo_all = getattr(acc, 'attendance_photo_all_punches', False)

    return {
        'punch_active'             : True,
        'punch_employee'           : emp,
        # Objetos Django não são serializáveis no cache — guardamos apenas os dados primitivos
        '_punch_record_id'         : record.pk if record else None,
        '_punch_pending_id'        : pending.pk if pending else None,
        'punch_count'              : punch_count,
        'punch_is_pending'         : punch_is_pending,
        'punch_worked_str'         : worked_str,
        'punch_theo_str'           : theo_str,
        'punch_next_action'        : next_action,
        'punch_is_ticking'         : is_ticking,
        'punch_worked_sec'         : int(worked_sec),
        'require_photo_all_punches': require_photo_all,
        'punch_block_reason'       : block_reason,
        # Guardados para reattach nos objetos Django
        'punch_record'             : None,
        'punch_pending'            : None,
    }


def punch_context(request):
    """
    Fornece o estado atual do registro de ponto e o saldo do dia
    para renderizar a cápsula no navbar (em base.html).

    PERFORMANCE: Cache de 20 segundos por funcionário.
    - O timer no frontend é atualizado via JavaScript (não depende de re-render).
    - O cache é invalidado imediatamente quando o funcionário bate o ponto (via punch_action).
    - 20s é suficiente para a UX: o botão responde no ato via redirect, o navbar atualiza no próximo load.
    """
    context = {'punch_active': False, 'punch_record': None, 'punch_pending': None}
    if not request.user.is_authenticated:
        return context

    emp = getattr(request.user, 'employee', None)
    if not emp:
        return context

    cache_key = f'punch_ctx_{emp.pk}_{timezone.localdate()}'
    cached = cache.get(cache_key)

    if cached is None:
        cached = _build_punch_context(emp, request)
        # Cache de 20 segundos — curto o suficiente para ser dinâmico,
        # longo o suficiente para evitar queries em navegação rápida entre páginas.
        cache.set(cache_key, cached, 20)

    context.update(cached)
    return context
