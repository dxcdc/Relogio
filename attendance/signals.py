from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def invalidate_timebank_cache(employee_id, date_obj):
    if not employee_id or not date_obj:
        return

    year = date_obj.year
    month = date_obj.month

    key_modal = f'timebank_{employee_id}_{year}_{month}'
    key_stats = f'attendance_stats_{employee_id}_{year}_{month}'

    cache.delete(key_modal)
    cache.delete(key_stats)
    logger.debug(f"[CACHE] Invalidacao feita para Emp_{employee_id} Mes {month}/{year}")


def _invalidate_monthly_summary(employee_id, year, month):
    """Remove o resumo mensal pre-computado para forcao re-calculo na proxima leitura."""
    try:
        from attendance.models import MonthlyAttendanceSummary
        MonthlyAttendanceSummary.objects.filter(employee_id=employee_id, year=year, month=month).delete()
    except Exception:
        pass
    # Também invalida o cache HTML do timebank para o mesmo mes
    cache.delete(f'timebank_{employee_id}_{year}_{month}')



@receiver(post_save, sender='attendance.AttendancePunch')
@receiver(post_delete, sender='attendance.AttendancePunch')
def clear_cache_on_punch(sender, instance, **kwargs):
    if instance.attendance_record:
        invalidate_timebank_cache(
            instance.attendance_record.employee_id,
            instance.attendance_record.date
        )
        # Invalida o resumo mensal pre-computado
        d = instance.attendance_record.date
        _invalidate_monthly_summary(instance.attendance_record.employee_id, d.year, d.month)


@receiver(post_save, sender='attendance.AttendanceRecord')
@receiver(post_delete, sender='attendance.AttendanceRecord')
def clear_cache_on_record(sender, instance, **kwargs):
    invalidate_timebank_cache(instance.employee_id, instance.date)
    # Invalida o resumo mensal pre-computado
    _invalidate_monthly_summary(instance.employee_id, instance.date.year, instance.date.month)

@receiver(post_save, sender='attendance.DailyTimeBalance')
@receiver(post_delete, sender='attendance.DailyTimeBalance')
def clear_cache_on_daily_balance(sender, instance, **kwargs):
    invalidate_timebank_cache(instance.employee_id, instance.date)

@receiver(post_save, sender='leave.LeaveRequest')
@receiver(post_delete, sender='leave.LeaveRequest')
def clear_cache_on_leave(sender, instance, **kwargs):
    
    if instance.from_date:
        invalidate_timebank_cache(instance.employee_id, instance.from_date)
    
    if instance.to_date and (instance.to_date.month != instance.from_date.month):
        invalidate_timebank_cache(instance.employee_id, instance.to_date)


# -----------------------------------------------------------------------------
# Google Calendar Sync (Push) Automações
# -----------------------------------------------------------------------------

@receiver(post_save, sender='attendance.ShiftOverride')
def sync_google_on_override_save(sender, instance, **kwargs):
    """Sincroniza a escala dinâmica no Google Agenda após salvar/criar."""
    from attendance.google_sync import sync_shift_override_to_google
    try:
        sync_shift_override_to_google(instance)
    except Exception as e:
        logger.error("Erro ao sincronizar ShiftOverride %s no Google: %s", instance.id, e)


@receiver(post_delete, sender='attendance.ShiftOverride')
def sync_google_on_override_delete(sender, instance, **kwargs):
    """Remove a escala do Google Agenda caso ela seja apagada."""
    from attendance.google_sync import delete_shift_override_from_google
    try:
        delete_shift_override_from_google(instance)
    except Exception as e:
        logger.error("Erro ao remover ShiftOverride %s no Google: %s", instance.id, e)


@receiver(post_save, sender='leave.Leave')
def sync_google_on_leave_save(sender, instance, **kwargs):
    """Sincroniza licenças e folgas no Google Agenda."""
    from attendance.google_sync import sync_leave_to_google
    try:
        sync_leave_to_google(instance)
    except Exception as e:
        logger.error("Erro ao sincronizar Leave %s no Google: %s", instance.id, e)


@receiver(post_delete, sender='leave.Leave')
def sync_google_on_leave_delete(sender, instance, **kwargs):
    """Remove a licença do Google Agenda se for apagada."""
    from attendance.google_sync import delete_leave_from_google
    try:
        delete_leave_from_google(instance)
    except Exception as e:
        logger.error("Erro ao remover Leave %s no Google: %s", instance.id, e)


# =============================================================================
# Invalidação da DailyWorkSummary (Materialized View Cache)
# =============================================================================

def _invalidate_daily_summary(employee_id, start_date, end_date=None):
    """Remove linhas da DailyWorkSummary para forçar recomputação na próxima leitura."""
    from datetime import timedelta
    try:
        from attendance.models import DailyWorkSummary
        qs = DailyWorkSummary.objects.filter(employee_id=employee_id)
        if end_date:
            qs = qs.filter(date__range=[start_date, end_date])
        else:
            qs = qs.filter(date__gte=start_date)
        qs.delete()
    except Exception:
        pass
    # Também invalida o cache de memória (5 min)
    if end_date:
        cur = start_date
        while cur <= end_date:
            cache.delete(f'work_info_{employee_id}_{cur}')
            cur += timedelta(days=1)
    else:
        cache.delete(f'work_info_{employee_id}_{start_date}')


@receiver(post_save, sender='leave.Leave')
@receiver(post_delete, sender='leave.Leave')
def invalidate_summary_on_leave(sender, instance, **kwargs):
    """Leave afeta apenas a data específica do funcionário."""
    _invalidate_daily_summary(instance.employee_id, instance.date, instance.date)


@receiver(post_save, sender='attendance.WorkScheduleAssignment')
@receiver(post_delete, sender='attendance.WorkScheduleAssignment')
def invalidate_summary_on_schedule_assignment(sender, instance, **kwargs):
    """Mudança de escala afeta todos os dias a partir do start_date."""
    _invalidate_daily_summary(instance.employee_id, instance.start_date)


@receiver(post_save, sender='attendance.EmployeeShiftAssignment')
@receiver(post_delete, sender='attendance.EmployeeShiftAssignment')
def invalidate_summary_on_shift_assignment(sender, instance, **kwargs):
    """Mudança de turno afeta todos os dias a partir do start_date."""
    _invalidate_daily_summary(instance.employee_id, instance.start_date)


@receiver(post_save, sender='leave.Holiday')
@receiver(post_delete, sender='leave.Holiday')
def invalidate_summary_on_holiday(sender, instance, **kwargs):
    """Feriado afeta todos os funcionários naquela data."""
    try:
        from attendance.models import DailyWorkSummary
        DailyWorkSummary.objects.filter(date=instance.date).delete()
    except Exception:
        pass
