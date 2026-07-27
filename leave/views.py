from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import require_module
from django.contrib import messages
from django.db.models import Q
from .models import LeaveRequest, LeaveType, LeaveEntitlement, LeaveRequestComment, Leave, Holiday, WorkWeek, LeaveActionLog
from django import forms
from pim.utils import get_visible_employees


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'from_date', 'to_date', 'comment', 'attachment']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'from_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'accept': 'image/*,.pdf',
                'onchange': "document.getElementById('file-name-display').innerText = this.files.length > 0 ? this.files[0].name : 'Nenhum arquivo de atestado selecionado'"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_deleted=False)
        self.fields['leave_type'].empty_label = "Selecione a licença..."
        self.fields['attachment'].required = True
        self.fields['attachment'].help_text = "Formatos aceitos: Imagens (JPG, PNG, etc) ou Arquivos PDF."

class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'default_days']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Deixe em branco p/ dias livres'
            })
        }


class LeaveEntitlementForm(forms.ModelForm):
    class Meta:
        model = LeaveEntitlement
        fields = ['employee', 'leave_type', 'from_date', 'to_date', 'no_of_days']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'from_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'no_of_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        }


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'recurring', 'length', 'is_global', 'cities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'length': forms.Select(attrs={'class': 'form-select'}),
            'is_global': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cities': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }




@login_required
@require_module('leave')
def leave_list(request):
    user = request.user
    emp = getattr(user, 'employee', None)
    mine = request.GET.get('mine')
    visible_employees = get_visible_employees(user)

    from attendance.models import ShiftSwapRequest, AttendanceAdjustment, PendingPunchRequest
    from claim.models import ClaimRequest

    if user.is_supervisor() and not mine:
        requests_qs = LeaveRequest.objects.filter(employee__in=visible_employees)

        
        from django.db.models import Q
        swaps_qs = ShiftSwapRequest.objects.filter(
            Q(target_employee__in=visible_employees) | Q(requester__in=visible_employees)
        )
        if user.is_hr() or user.is_admin():
            swaps_qs = swaps_qs.exclude(status='PENDING_TARGET')
        else:
            swaps_qs = swaps_qs.filter(status='PENDING_SUPERVISOR')

        adj_qs = AttendanceAdjustment.objects.filter(employee__in=visible_employees)

        
        pending_punches_qs = PendingPunchRequest.objects.filter(
            employee__in=visible_employees,
        ).select_related('employee').order_by('-requested_at')

        
        pending_punches_count = pending_punches_qs.filter(status=PendingPunchRequest.STATUS_PENDING).count()

        
        claims_qs = ClaimRequest.objects.filter(employee__in=visible_employees)

        
        if user.is_hr() or user.is_admin():
            claims_pending = claims_qs.filter(
                status__in=[ClaimRequest.STATUS_SUBMITTED, ClaimRequest.STATUS_SUPERVISOR_APPROVED]
            )
        else:
            claims_pending = claims_qs.filter(status=ClaimRequest.STATUS_SUBMITTED)

        view_mode = 'inbox'
    else:
        from django.db.models import Q
        requests_qs = LeaveRequest.objects.filter(employee=emp) if emp else LeaveRequest.objects.none()
        swaps_qs = ShiftSwapRequest.objects.filter(Q(requester=emp) | Q(target_employee=emp)) if emp else ShiftSwapRequest.objects.none()
        adj_qs = AttendanceAdjustment.objects.filter(employee=emp) if emp else AttendanceAdjustment.objects.none()
        pending_punches_qs = PendingPunchRequest.objects.none()
        pending_punches_count = 0
        claims_qs = ClaimRequest.objects.filter(employee=emp) if emp else ClaimRequest.objects.none()
        claims_pending = claims_qs.filter(
            status__in=[ClaimRequest.STATUS_SUBMITTED, ClaimRequest.STATUS_SUPERVISOR_APPROVED]
        )
        view_mode = 'personal'

    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
        swaps_qs = swaps_qs.filter(status=status_filter)
        adj_qs = adj_qs.filter(status=status_filter)

    from django.db.models import Case, When, Value, IntegerField
    def prioritize_pending(qs, date_field):
        return qs.annotate(
            urgency=Case(
                When(status__in=['PENDING', 'SUBMITTED', 'PENDING_TARGET', 'PENDING_SUPERVISOR', 'PENDING_HR'], then=Value(1)),
                When(status='SUPERVISOR_APPROVED', then=Value(2)),
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('urgency', f'-{date_field}')

    requests_qs = prioritize_pending(requests_qs.select_related('employee', 'leave_type'), 'date_applied')
    swaps_qs = prioritize_pending(swaps_qs.select_related('requester', 'target_employee'), 'created_at')
    adj_qs = prioritize_pending(adj_qs.select_related('employee'), 'date')
    pending_punches_qs = prioritize_pending(pending_punches_qs, 'requested_at')
    claims_qs = prioritize_pending(claims_qs.select_related('employee', 'claim_event').prefetch_related('expenses', 'attachments'), 'created_at')

    form = LeaveRequestForm()

    return render(request, 'leave/leave_list.html', {
        'requests': requests_qs,
        'swaps': swaps_qs,
        'adjustments': adj_qs,
        'pending_punches': pending_punches_qs,
        'pending_punches_count': pending_punches_count,
        'claims': claims_qs,
        'claims_pending': claims_pending,
        'status_filter': status_filter,
        'view_mode': view_mode,
        'form': form,
    })


@login_required
@require_module('leave')
def leave_create(request):
    user = request.user
    emp = getattr(user, 'employee', None)
    if not emp:
        messages.error(request, 'Seu usuario nao esta vinculado a um funcionario.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            lr = form.save(commit=False)
            lr.employee = emp
            
            if lr.leave_type:
                leave_name = lr.leave_type.name.lower()
                is_folga = 'folga' in leave_name
                
                if not is_folga and not request.FILES.get('attachment'):
                    form.add_error('attachment', f'O tipo de licença "{lr.leave_type.name}" exige um atestado/documento anexado.')
                    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Nova Solicitacao'})
                    
            lr.save()
            LeaveActionLog.objects.create(
                leave_request=lr,
                action=LeaveActionLog.ACTION_SUBMIT,
                performed_by=user,
                note=f'Solicitado em {lr.date_applied.strftime("%d/%m/%Y")}'
            )
            messages.success(request, 'Solicitacao de licenca enviada!')
            return redirect('leave_list')
    else:
        initial = {}
        if 'date' in request.GET:
            from datetime import datetime
            try:
                date_val = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
                initial['from_date'] = date_val
                initial['to_date'] = date_val
            except ValueError:
                pass
        form = LeaveRequestForm(initial=initial)
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Nova Solicitacao'})


@login_required
def leave_detail(request, pk):
    visible_employees = get_visible_employees(request.user)
    lr = get_object_or_404(
        LeaveRequest.objects.select_related('employee', 'leave_type', 'reviewed_by_supervisor', 'reviewed_by_hr')
        .prefetch_related('comments__created_by', 'action_logs__performed_by')
        .filter(employee__in=visible_employees), pk=pk
    )
    return render(request, 'leave/leave_detail.html', {'lr': lr})


@login_required
def leave_approve(request, pk):
    visible_employees = get_visible_employees(request.user)
    lr = get_object_or_404(LeaveRequest.objects.filter(employee__in=visible_employees), pk=pk)
    user = request.user

    
    if user.is_hr() or user.is_admin():
        if lr.status in [LeaveRequest.STATUS_PENDING, LeaveRequest.STATUS_SUPERVISOR_APPROVED]:
            lr.status = LeaveRequest.STATUS_APPROVED
            lr.reviewed_by_hr = user
            from django.utils import timezone
            lr.hr_reviewed_at = timezone.now()
            lr.save()
            LeaveActionLog.objects.create(
                leave_request=lr, action=LeaveActionLog.ACTION_HR_APPROVE, performed_by=user
            )
            from core.audit import log_action
            log_action(request, 'LEAVE_APPROVE',
                f'{user.username} aprovou licença de {lr.employee.full_name} '
                f'({lr.leave_type.name}, {lr.from_date.strftime("%d/%m/%Y")} a {lr.to_date.strftime("%d/%m/%Y")}).')
            messages.success(request, 'Licença aprovada pelo RH! Decisão final registrada.')
        else:
            messages.warning(request, 'Esta licença não pode ser aprovada no estado atual.')

    
    elif user.role == user.ROLE_SUPERVISOR:
        if lr.status == LeaveRequest.STATUS_PENDING:
            lr.status = LeaveRequest.STATUS_SUPERVISOR_APPROVED
            lr.reviewed_by_supervisor = user
            from django.utils import timezone
            lr.supervisor_reviewed_at = timezone.now()
            lr.save()
            LeaveActionLog.objects.create(
                leave_request=lr, action=LeaveActionLog.ACTION_SUPERVISOR_APPROVE, performed_by=user
            )
            messages.success(request, 'Licença pré-aprovada! O RH será notificado para validação final.')
        else:
            messages.warning(request, 'Esta licença já passou da etapa de aprovação do supervisor.')
    else:
        messages.error(request, 'Você não tem permissão para aprovar licenças.')

    return redirect('leave_detail', pk=pk)


@login_required
def leave_reject(request, pk):
    if request.method != 'POST':
        return redirect('leave_detail', pk=pk)
    visible_employees = get_visible_employees(request.user)
    lr = get_object_or_404(LeaveRequest.objects.filter(employee__in=visible_employees), pk=pk)
    user = request.user
    reason = request.POST.get('rejection_reason', '').strip()

    if not reason:
        messages.error(request, 'O motivo da rejeição é obrigatório.')
        return redirect('leave_detail', pk=pk)

    
    if user.is_hr() or user.is_admin():
        if lr.status in [LeaveRequest.STATUS_PENDING, LeaveRequest.STATUS_SUPERVISOR_APPROVED]:
            lr.status = LeaveRequest.STATUS_REJECTED
            lr.rejection_reason = reason
            lr.reviewed_by_hr = user
            from django.utils import timezone
            lr.hr_reviewed_at = timezone.now()
            lr.save()
            LeaveActionLog.objects.create(
                leave_request=lr, action=LeaveActionLog.ACTION_REJECT, performed_by=user, note=reason
            )
            from core.audit import log_action
            log_action(request, 'LEAVE_REJECT',
                f'{user.username} rejeitou licença de {lr.employee.full_name} '
                f'({lr.leave_type.name}, {lr.from_date.strftime("%d/%m/%Y")}). Motivo: {reason}')
            messages.warning(request, 'Licença rejeitada pelo RH.')
        else:
            messages.warning(request, 'Esta licença não pode ser rejeitada no estado atual.')

    
    elif user.role == user.ROLE_SUPERVISOR:
        if lr.status == LeaveRequest.STATUS_PENDING:
            lr.status = LeaveRequest.STATUS_REJECTED
            lr.rejection_reason = reason
            lr.reviewed_by_supervisor = user
            from django.utils import timezone
            lr.supervisor_reviewed_at = timezone.now()
            lr.save()
            LeaveActionLog.objects.create(
                leave_request=lr, action=LeaveActionLog.ACTION_REJECT, performed_by=user, note=reason
            )
            messages.warning(request, 'Licença rejeitada.')
        else:
            messages.error(request, 'Apenas o RH pode rejeitar uma licença já pré-aprovada.')
    else:
        messages.error(request, 'Você não tem permissão para rejeitar licenças.')

    return redirect('leave_detail', pk=pk)


@login_required
def leave_cancel(request, pk):
    visible_employees = get_visible_employees(request.user)
    lr = get_object_or_404(LeaveRequest.objects.filter(employee__in=visible_employees), pk=pk)

    
    if lr.status == LeaveRequest.STATUS_APPROVED:
        messages.error(request, 'Esta licença já foi aprovada pelo RH e não pode ser cancelada. Entre em contato com o RH.')
        return redirect('leave_list')

    if not request.user.is_supervisor():
        my_emp = getattr(request.user, 'employee', None)
        if not my_emp or lr.employee != my_emp:
            messages.error(request, 'Você não pode cancelar esta licença.')
            return redirect('leave_list')

    lr.status = LeaveRequest.STATUS_CANCELLED
    lr.save()
    messages.info(request, 'Licença cancelada.')
    return redirect('leave_list')


@login_required
@require_module('leave')
def my_absences_calendar(request):
    import calendar
    from datetime import date
    from django.utils import timezone
    from django.db import models
    
    emp = getattr(request.user, 'employee', None)
    
    
    try:
        year = int(request.GET.get('year', timezone.now().year))
    except ValueError:
        year = timezone.now().year
        
    holidays = Holiday.objects.filter(
        models.Q(date__year=year) | models.Q(recurring=True)
    )
    holiday_map = {}
    for h in holidays:
        h_date = date(year, h.date.month, h.date.day) if h.recurring else h.date
        holiday_map[h_date] = h.name
        
    leave_map = {}
    if emp:
        leaves = Leave.objects.filter(employee=emp, date__year=year).select_related('leave_type', 'leave_request')
        for l in leaves:
            leave_map[l.date] = {
                'status': l.status,
                'type_name': l.leave_type.name.lower()
            }
            
    cal = calendar.Calendar(firstweekday=6) 
    
    months_data = []
    month_names = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    for month in range(1, 13):
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            week_days = []
            for current_date in week:
                is_current_month = (current_date.month == month)
                
                day_data = {
                    'date': current_date,
                    'day': current_date.day,
                    'is_current_month': is_current_month,
                    'is_sunday':  current_date.weekday() == 6,
                    'is_weekend': current_date.weekday() >= 5,
                    'is_today':   current_date == date.today(),
                }
                
                category = 'normal'
                color_class = ''
                status = ''
                hover_text = ''
                
                if is_current_month:
                    if current_date in leave_map:
                        l_data = leave_map[current_date]
                        status = l_data['status']
                        l_type = l_data['type_name']
                        
                        hover_text = f"{l_type.title()} ({status})"
                        
                        if status == 'PENDING' or status == 'SUPERVISOR_APPROVED':
                            color_class = 'bg-pendente'
                            category = 'pendente'
                        elif status == 'APPROVED':
                            if 'férias' in l_type or 'ferias' in l_type:
                                color_class = 'bg-ferias'
                                category = 'ferias'
                            elif 'médica' in l_type or 'medica' in l_type:
                                color_class = 'bg-medica'
                                category = 'medica'
                            elif 'banco' in l_type:
                                color_class = 'bg-banco'
                                category = 'banco'
                            elif 'folga' in l_type:
                                color_class = 'bg-folga'
                                category = 'folga'
                            else:
                                color_class = 'bg-ferias'
                                category = 'ferias'
                    elif current_date in holiday_map:
                        color_class = 'bg-feriado'
                        category = 'feriado'
                        hover_text = holiday_map[current_date]
                
                day_data['category'] = category
                day_data['color_class'] = color_class
                day_data['status'] = status
                day_data['hover_text'] = hover_text
                
                week_days.append(day_data)
            weeks.append(week_days)
            
        months_data.append({
            'name': f"{month_names[month]} {year}",
            'weeks': weeks,
        })
        
    context = {
        'months': months_data,
        'year': year,
        'prev_year': year - 1,
        'next_year': year + 1,
    }
    
    return render(request, 'leave/my_absences.html', context)


@login_required
def leave_comment_add(request, pk):
    visible_employees = get_visible_employees(request.user)
    lr = get_object_or_404(LeaveRequest.objects.filter(employee__in=visible_employees), pk=pk)
    if request.method == 'POST':
        text = request.POST.get('comment', '').strip()
        if text:
            LeaveRequestComment.objects.create(
                leave_request=lr, created_by=request.user, comment=text
            )
            messages.success(request, 'Comentario adicionado.')
    return redirect('leave_detail', pk=pk)




@login_required
def leave_type_list(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    types = LeaveType.objects.filter(is_deleted=False)
    return render(request, 'leave/leave_type_list.html', {'types': types})


@login_required
def leave_type_create(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de licenca criado!')
            return redirect('leave_type_list')
    else:
        form = LeaveTypeForm()
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Novo Tipo de Licenca'})


@login_required
def leave_type_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    lt = get_object_or_404(LeaveType, pk=pk)
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST, instance=lt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de licenca atualizado!')
            return redirect('leave_type_list')
    else:
        form = LeaveTypeForm(instance=lt)
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Editar Tipo de Licenca'})


@login_required
def leave_type_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    lt = get_object_or_404(LeaveType, pk=pk)
    lt.is_deleted = True
    lt.save()
    messages.success(request, 'Tipo de licenca excluido.')
    return redirect('leave_type_list')




@login_required
def leave_entitlement_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    visible_employees = get_visible_employees(request.user)
    entitlements = LeaveEntitlement.objects.select_related('employee', 'leave_type').filter(employee__in=visible_employees)
    return render(request, 'leave/entitlement_list.html', {'entitlements': entitlements})


@login_required
def leave_entitlement_create(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = LeaveEntitlementForm(request.POST)
        if form.is_valid():
            ent = form.save(commit=False)
            ent.created_by = request.user
            ent.save()
            messages.success(request, 'Saldo de licenca adicionado!')
            return redirect('leave_entitlement_list')
    else:
        form = LeaveEntitlementForm()
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Novo Saldo de Licenca'})


@login_required
def leave_entitlement_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    ent = get_object_or_404(LeaveEntitlement, pk=pk)
    if request.method == 'POST':
        form = LeaveEntitlementForm(request.POST, instance=ent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saldo atualizado!')
            return redirect('leave_entitlement_list')
    else:
        form = LeaveEntitlementForm(instance=ent)
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Editar Saldo de Licenca'})


@login_required
def leave_entitlement_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    ent = get_object_or_404(LeaveEntitlement, pk=pk)
    ent.delete()
    messages.success(request, 'Saldo removido.')
    return redirect('leave_entitlement_list')




@login_required
def holiday_list(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    
    from admin_app.models import City
    holidays = Holiday.objects.prefetch_related('cities').all().order_by('date')
    cities = City.objects.all().order_by('name')
    return render(request, 'leave/holiday_list.html', {'holidays': holidays, 'cities': cities})


@login_required
def holiday_create(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Feriado adicionado!')
            return redirect('holiday_list')
    else:
        form = HolidayForm()
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Adicionar Feriado'})


@login_required
def holiday_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            messages.success(request, 'Feriado atualizado!')
            return redirect('holiday_list')
    else:
        form = HolidayForm(instance=holiday)
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Editar Feriado'})


@login_required
def holiday_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return redirect('dashboard')
    holiday = get_object_or_404(Holiday, pk=pk)
    holiday.delete()
    messages.success(request, 'Feriado removido!')
    return redirect('holiday_list')
