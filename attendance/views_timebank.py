from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from attendance.models import AttendanceRecord, get_work_info_for_date_range
from datetime import date
import calendar
from django.core.cache import cache
from django.template.loader import render_to_string
from django.http import HttpResponse

@login_required
def time_bank_modal(request):
    """Retorna o fragmento HTML do Extrato do Banco de Horas com cálculo dinâmico e em tempo real para o Mês"""
    employee = getattr(request.user, 'employee', None)
    if not employee:
        return render(request, 'attendance/_time_bank_empty.html', {'msg': 'Perfil de funcionário não encontrado.'})

    import datetime
    today = datetime.date.today()

    def fmt_hours(minutes):
        sign = "+" if minutes >= 0 else "-"
        m = int(abs(minutes))
        h = m // 60
        r = m % 60
        return f"{sign} {h:02d}h {r:02d}m"

    try:
        req_year  = int(request.GET.get('year',  today.year))
        req_month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        req_year  = today.year
        req_month = today.month

    # Cache — meses passados ficam 7 dias, mês atual fica 5 minutos (dados mudam ao longo do dia)
    is_current_month = (req_year == today.year and req_month == today.month)
    cache_ttl = 60 * 5 if is_current_month else 60 * 60 * 24 * 7
    cache_key = f'timebank_{employee.id}_{req_year}_{req_month}'
    cached_html = cache.get(cache_key)
    if cached_html:
        return HttpResponse(cached_html)

    # ── Determina o range de datas do mês ──────────────────────────────────────
    _, last_day = calendar.monthrange(req_year, req_month)
    end_day = today.day if is_current_month else last_day

    start_date = date(req_year, req_month, 1)
    end_date   = date(req_year, req_month, end_day)

    # ── BULK FETCH — 5 queries para o mês todo (antes eram 5 × end_day queries) ──
    month_work_info = get_work_info_for_date_range(employee, start_date, end_date)

    # ── Registros de ponto do mês (1 query com prefetch de batidas) ─────────────
    records_qs = AttendanceRecord.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    ).prefetch_related('punches')
    record_map = {}
    for r in records_qs:
        r._prefetched_work_info = month_work_info.get(r.date, {})
        record_map[r.date] = r

    # ── Cálculo do saldo — 100% em memória, zero queries adicionais ─────────────
    month_theo     = 0
    month_acted    = 0
    month_extra    = 0
    month_negative = 0
    transactions   = []

    for d in range(1, end_day + 1):
        target_date = date(req_year, req_month, d)

        work_info = month_work_info.get(target_date, {})
        theo_min  = work_info.get('theo_minutes', 0)
        tol_min   = work_info.get('tolerance_minutes', 0)

        record    = record_map.get(target_date)
        acted_min = record.net_minutes_worked if record else 0

        month_theo  += theo_min
        month_acted += acted_min

        daily_diff = acted_min - theo_min

        if daily_diff > tol_min:
            month_extra += daily_diff
            transactions.append({
                'date': target_date,
                'extra_total': int(daily_diff),
                'extra_total_str': fmt_hours(int(daily_diff)).replace('+ ', ''),
                'negative_total': 0
            })
        elif daily_diff < -tol_min and theo_min > 0:
            cost = abs(daily_diff)
            month_negative += cost
            transactions.append({
                'date': target_date,
                'extra_total': 0,
                'negative_total': int(cost),
                'negative_total_str': fmt_hours(int(cost)).replace('+ ', ''),
            })

    global_balance_minutes = month_extra - month_negative

    transactions.reverse()
    transactions = transactions[:30]

    regular_done     = min(month_acted, month_theo) if month_theo > 0 else month_acted
    progress_percent = (regular_done / month_theo * 100) if month_theo > 0 else 0
    if progress_percent > 100:
        progress_percent = 100

    global_balance_str = fmt_hours(global_balance_minutes)

    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    context = {
        'global_balance_minutes': global_balance_minutes,
        'global_balance_str':     global_balance_str,
        'month_theo_str':         fmt_hours(month_theo).replace('+ ', ''),
        'month_extra_str':        fmt_hours(month_extra).replace('+ ', ''),
        'month_negative_str':     fmt_hours(-month_negative).replace('- ', ''),
        'progress_percent':       int(progress_percent),
        'transactions':           transactions,
        'month_name':             f"{month_names[req_month - 1]} {req_year}",
    }

    html = render_to_string('attendance/_time_bank_modal.html', context, request)
    cache.set(cache_key, html, cache_ttl)

    return HttpResponse(html)
