from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import calendar
import csv
from django.http import HttpResponse

from pim.models import Employee
from .models import TimesheetPeriod, DailyTimeBalance, AttendanceClosingSettings

@login_required
def payroll_closing_list(request):
    """Lista os fechamentos de ponto realizados."""
    if not request.user.is_admin() and not request.user.is_hr():
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
        
    
    periods_summary_qs = TimesheetPeriod.objects.filter(status=TimesheetPeriod.STATUS_CLOSED).values('start_date', 'end_date', 'status').distinct().order_by('-end_date')
    
    MESES = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    periods_summary = []
    for p in periods_summary_qs:
        m = p['start_date'].month
        y = p['start_date'].year
        periods_summary.append({
            'start_date': p['start_date'],
            'end_date': p['end_date'],
            'status': p['status'],
            'label': f"{MESES[m]} {y}"
        })

    
    today = timezone.now().date()
    
    months_suggestions = []
    for i in range(3):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        _, last_day = calendar.monthrange(y, m)
        start_date = datetime(y, m, 1).date()
        end_date = datetime(y, m, last_day).date()
        
        
        exists = TimesheetPeriod.objects.filter(start_date=start_date, end_date=end_date).exists()
        months_suggestions.append({
            'start_date': start_date,
            'end_date': end_date,
            'label': f"{MESES[m]} {y}",
            'is_closed': exists
        })

    settings = AttendanceClosingSettings.get_settings()

    return render(request, 'attendance/payroll_closing.html', {
        'periods_summary': periods_summary,
        'months_suggestions': months_suggestions,
        'settings': settings
    })

@login_required
def payroll_close_month(request):
    """Gera os TimesheetPeriods para todos os funcionários no mês recebido e fecha."""
    if not request.user.is_admin() and not request.user.is_hr():
        return redirect('dashboard')
        
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except Exception:
            messages.error(request, 'Datas inválidas.')
            return redirect('payroll_closing_list')
            
        emps = Employee.objects.filter(state=Employee.STATE_ACTIVE)
        count = 0
        for emp in emps:
            period, created = TimesheetPeriod.objects.get_or_create(
                employee=emp, 
                start_date=start_date, 
                end_date=end_date
            )
            
            
            balances = DailyTimeBalance.objects.filter(employee=emp, date__gte=start_date, date__lte=end_date)
            period.total_regular_minutes = sum(b.regular_minutes for b in balances)
            period.total_extra_60_minutes = sum(b.extra_60_minutes for b in balances)
            period.total_extra_100_minutes = sum(b.extra_100_minutes for b in balances)
            period.total_night_minutes = sum(b.night_minutes for b in balances)
            period.total_negative_minutes = sum(b.negative_minutes for b in balances)
            
            
            emp_settings = AttendanceClosingSettings.get_settings(emp.legal_entity)
            mult_60 = emp_settings.overtime_multiplier_weekday
            mult_100 = emp_settings.overtime_multiplier_weekend
            
            
            this_month_balance = int((period.total_extra_60_minutes * mult_60) + (period.total_extra_100_minutes * mult_100)) - period.total_negative_minutes
            
            
            last_zeroed = TimesheetPeriod.objects.filter(
                employee=emp, 
                is_hour_bank_zeroed=True
            ).order_by('-end_date').first()
            
            
            if last_zeroed:
                periods_since = TimesheetPeriod.objects.filter(
                    employee=emp, 
                    start_date__gt=last_zeroed.end_date, 
                    status=TimesheetPeriod.STATUS_CLOSED
                ).order_by('start_date')
            else:
                periods_since = TimesheetPeriod.objects.filter(
                    employee=emp, 
                    status=TimesheetPeriod.STATUS_CLOSED
                ).order_by('start_date')
                
            previous_accumulated = 0
            if periods_since.exists():
                previous_accumulated = list(periods_since)[-1].accumulated_balance_minutes
                
            period.accumulated_balance_minutes = previous_accumulated + this_month_balance
            
            
            reset_months_str = emp_settings.hour_bank_reset_months or ""
            reset_months = [int(m.strip()) for m in reset_months_str.split(',') if m.strip().isdigit()]
            
            if end_date.month in reset_months:
                period.is_hour_bank_zeroed = True
            else:
                period.is_hour_bank_zeroed = False
            
            period.status = TimesheetPeriod.STATUS_CLOSED
            period.closed_at = timezone.now()
            period.closed_by = request.user
            period.save()
            count += 1
            
        messages.success(request, f'Folha de Ponto fechada com sucesso para {count} funcionários!')
    return redirect('payroll_closing_list')


@login_required
def payroll_export_excel(request):
    """Exporta um mês fechado em formato CSV (Abre nativamente no Excel)."""
    if not request.user.is_admin() and not request.user.is_hr():
        return redirect('dashboard')
        
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="Folha_Ponto_{start_date_str}_a_{end_date_str}.csv"'
    
    writer = csv.writer(response, delimiter=';') 
    writer.writerow(['NOME', 'CPF', 'HORAS NORMAIS', 'HE 60%', 'HE 100%', 'HORAS NOTURNAS', 'ATRASOS (MIN)', 'SALDO BANCO ACUMULADO (MIN)', 'STATUS DO BANCO'])
    
    periods = TimesheetPeriod.objects.filter(start_date=start_date_str, end_date=end_date_str, status=TimesheetPeriod.STATUS_CLOSED).select_related('employee')
    
    def format_hm(mins):
        h = mins // 60
        m = mins % 60
        return f"{h:02d}:{m:02d}"
        
    for p in periods:
        emp = p.employee
        cpf = getattr(emp, 'cpf', '') or getattr(emp, 'nic', '') 
        
        normais = format_hm(p.total_regular_minutes)
        he60 = format_hm(p.total_extra_60_minutes)
        he100 = format_hm(p.total_extra_100_minutes)
        noturnos = format_hm(p.total_night_minutes)
        atrasos = p.total_negative_minutes
        saldo_banco_acumulado = p.accumulated_balance_minutes
        status_banco = 'ZERAR/PAGAR' if p.is_hour_bank_zeroed else 'ACUMULANDO'
        
        writer.writerow([
            emp.full_name,
            cpf,
            normais,
            he60,
            he100,
            noturnos,
            atrasos,
            saldo_banco_acumulado,
            status_banco
        ])
        
    return response

@login_required
def payroll_settings(request):
    """Tela para configuração SAS de regras de ponto (Banco de horas e Adicionais) por Filial."""
    from admin_app.models import LegalEntity
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
        
    
    edit_id = request.GET.get('edit')
    target_setting = None
    if edit_id:
        target_setting = AttendanceClosingSettings.objects.filter(id=edit_id).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            setting_id = request.POST.get('setting_id')
            AttendanceClosingSettings.objects.filter(id=setting_id, legal_entity__isnull=False).delete()
            messages.success(request, 'Configuração da filial excluída. Retornará para a Global.')
            return redirect('payroll_settings')
            
        if action == 'toggle':
            setting_id = request.POST.get('setting_id')
            s = AttendanceClosingSettings.objects.filter(id=setting_id).first()
            if s:
                s.is_active = not s.is_active
                s.save()
                messages.success(request, f"Regra {'ativada' if s.is_active else 'desativada'} com sucesso!")
            return redirect('payroll_settings')
            
        legal_entity_id = request.POST.get('legal_entity_id')
        if legal_entity_id == 'all' or not legal_entity_id:
            setting, _ = AttendanceClosingSettings.objects.get_or_create(legal_entity=None)
        else:
            try:
                le = LegalEntity.objects.get(id=legal_entity_id)
                setting, _ = AttendanceClosingSettings.objects.get_or_create(legal_entity=le)
            except LegalEntity.DoesNotExist:
                messages.error(request, 'Empresa/Filial inválida.')
                return redirect('payroll_settings')
                
        setting.is_active = request.POST.get('is_active') == 'on'
        setting.payroll_closing_day = request.POST.get('payroll_closing_day', setting.payroll_closing_day)
        setting.hour_bank_reset_months = request.POST.get('hour_bank_reset_months', setting.hour_bank_reset_months)
        setting.overtime_multiplier_weekday = float(request.POST.get('overtime_multiplier_weekday', setting.overtime_multiplier_weekday))
        setting.overtime_multiplier_weekend = float(request.POST.get('overtime_multiplier_weekend', setting.overtime_multiplier_weekend))
        setting.night_shift_start = request.POST.get('night_shift_start', setting.night_shift_start)
        setting.night_shift_end = request.POST.get('night_shift_end', setting.night_shift_end)
        setting.save()
        messages.success(request, 'Configurações parametrizadas com sucesso!')
        return redirect('payroll_settings')
        
    
    AttendanceClosingSettings.get_settings() 
    all_configs = AttendanceClosingSettings.objects.all().select_related('legal_entity').order_by('legal_entity__name')
    legal_entities = LegalEntity.objects.all()
        
    return render(request, 'attendance/payroll_settings.html', {
        'all_configs': all_configs,
        'legal_entities': legal_entities,
        'target_setting': target_setting
    })
