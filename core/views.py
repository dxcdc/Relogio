from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages
from functools import wraps
from .forms import LoginForm


class OrangeLoginView(LoginView):
    template_name = 'core/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_initial(self):
        initial = super().get_initial()
        
        remembered_user = self.request.COOKIES.get('remember_username')
        if remembered_user:
            initial['username'] = remembered_user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if 'remember_username' in self.request.COOKIES:
            context['remember_checked'] = True
        return context

    def form_valid(self, form):
        
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        
        
        remember_me = self.request.POST.get('remember_me')
        if remember_me:
            
            self.request.session.set_expiry(1209600)
            
            
            response.set_cookie('remember_username', username, max_age=2592000, httponly=True, samesite='Lax')
        else:
            
            self.request.session.set_expiry(0)
            
            response.delete_cookie('remember_username')
            
        return response


@login_required
def dashboard(request):
    from pim.models import Employee
    from leave.models import LeaveRequest
    from attendance.models import AttendanceRecord, AttendanceAdjustment

    today = timezone.now().date()
    is_mgmt = request.user.is_supervisor() or request.user.is_admin()

    if is_mgmt:
        # Cache de 60s — KPIs do painel não precisam de precisão em tempo real
        from django.core.cache import cache as _dash_cache
        _dash_stats_key = 'dashboard_mgmt_stats'
        _dash_stats = _dash_cache.get(_dash_stats_key)
        if _dash_stats is None:
            _dash_stats = {
                'active_employees': Employee.objects.filter(state='ACTIVE').count(),
                'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
                'supervisor_approved_leaves': LeaveRequest.objects.filter(status='SUPERVISOR_APPROVED').count(),
                'today_attendance': AttendanceRecord.objects.filter(date=today, punches__isnull=False).distinct().count(),
                'pending_adjustments': AttendanceAdjustment.objects.filter(status='PENDING').count(),
            }
            _dash_cache.set(_dash_stats_key, _dash_stats, 60)
        active_employees           = _dash_stats['active_employees']
        pending_leaves             = _dash_stats['pending_leaves']
        supervisor_approved_leaves = _dash_stats['supervisor_approved_leaves']
        today_attendance           = _dash_stats['today_attendance']
        pending_adjustments        = _dash_stats['pending_adjustments']

        from attendance.models import get_work_info_for_date_bulk
        today_records = list(AttendanceRecord.objects.filter(
            date=today
        ).select_related('employee__work_schedule').prefetch_related('punches'))

        employees_in_records = [r.employee for r in today_records]
        bulk_work_info = get_work_info_for_date_bulk(employees_in_records, today)

        late_today = 0
        for r in today_records:
            r._prefetched_work_info = bulk_work_info.get(r.employee_id, {})
            if r.is_late:
                late_today += 1
        recent_leaves = LeaveRequest.objects.select_related('employee', 'leave_type').order_by('-date_applied')[:5]
        recent_adjustments = AttendanceAdjustment.objects.select_related('employee').order_by('-created_at')[:5]
    else:
        active_employees = 0
        today_attendance = 0
        supervisor_approved_leaves = 0
        pending_adjustments = 0
        late_today = 0
        emp = getattr(request.user, 'employee', None)
        if emp:
            from django.db.models import Q
            from datetime import timedelta
            
            two_days_ago = timezone.now().date() - timedelta(days=2)
            pending_leaves = LeaveRequest.objects.filter(employee=emp, status__in=['PENDING', 'SUPERVISOR_APPROVED']).count()
            
            
            recent_leaves = LeaveRequest.objects.filter(
                Q(status__in=['PENDING', 'SUPERVISOR_APPROVED']) | Q(date_applied__gte=two_days_ago),
                employee=emp
            ).select_related('employee', 'leave_type').order_by('-date_applied')[:4]
            recent_adjustments = AttendanceAdjustment.objects.filter(employee=emp).select_related('employee').order_by('-created_at')[:5]
        else:
            pending_leaves = 0
            recent_leaves = []
            recent_adjustments = []

    birthdays = list(Employee.objects.filter(
        birthday__month=today.month,
        birthday__day__gte=today.day,
        state='ACTIVE'
    ).order_by('birthday__day')[:5])
    
    from .models import Announcement
    from django.db.models import Q
    announcements_qs = Announcement.objects.filter(
        Q(expires_at__gte=today) | Q(expires_at__isnull=True),
        is_active=True
    ).order_by('-created_at')
    
    emp = getattr(request.user, 'employee', None)
    if is_mgmt and not emp:
        announcements = announcements_qs[:2]
    else:
        if emp and emp.sub_division:
            announcements = announcements_qs.filter(
                Q(visibility='ALL') | Q(department=emp.sub_division)
            )[:2]
        else:
            announcements = announcements_qs.filter(visibility='ALL')[:2]

    
    from .models import AnnouncementLike
    user_liked_ids = AnnouncementLike.objects.filter(
        user=request.user, announcement__in=announcements
    ).values_list('announcement_id', flat=True)

    my_team = []
    my_team_count = 0
    my_supervisors = []
    my_leaves_count = 0
    my_upcoming_leaves_count = 0
    
    if emp:
        if emp.sub_division:
            # Avalia 1x a lista — evita 2 queries separadas (count + slice)
            my_team = list(Employee.objects.filter(
                sub_division=emp.sub_division, state='ACTIVE'
            ).exclude(id=emp.id)[:7])
            my_team_count = len(my_team)
            my_team = my_team[:6]  # mostra máx. 6 na UI
        
        my_supervisors = emp.supervisors.filter(state='ACTIVE')[:4]
        
        
        from leave.models import Leave
        
        def calc_days(qs):
            d = sum(0.5 if l.duration_type == 4 else 1.0 for l in qs)
            return int(d) if d == int(d) else d

        pending_qs = Leave.objects.filter(
            employee=emp, 
            leave_request__status__in=['PENDING', 'SUPERVISOR_APPROVED']
        ).exclude(leave_request__leave_type__name__icontains='féria').exclude(leave_request__leave_type__name__icontains='feria')
        my_leaves_count = calc_days(pending_qs)
        
        upcoming_qs = Leave.objects.filter(
            employee=emp, 
            leave_request__status='APPROVED', 
            date__gte=today
        ).exclude(leave_request__leave_type__name__icontains='féria').exclude(leave_request__leave_type__name__icontains='feria')
        my_upcoming_leaves_count = calc_days(upcoming_qs)
        
    
    if is_mgmt and not emp:
        team_qs = Employee.objects.filter(state='ACTIVE')
        my_team_count = team_qs.count()
        my_team = team_qs[:6]

    next_action = 'PUNCH_IN'
    button_color = 'primary'
    button_text = 'Clock in'
    button_icon = 'bi-box-arrow-in-right'

    if not is_mgmt:
        emp = getattr(request.user, 'employee', None)
        if emp:
            # Reutiliza o mesmo record_today que será buscado abaixo (bloco de shift)
            # evitando uma query redundante nesta seção
            _rec = AttendanceRecord.objects.filter(
                employee=emp, date=timezone.localtime(timezone.now()).date()
            ).first()
            if _rec:
                if _rec.current_state == 'IN':
                    next_action = 'OUT'
                    button_color = 'danger'
                    button_text = 'Pausar/Encerrar'
                    button_icon = 'bi-pause-circle'
                else:
                    next_action = 'IN'
                    button_color = 'success'
                    button_text = 'Iniciar/Retornar'
                    button_icon = 'bi-play-circle'

    
    
    
    today_worked_str = "0h 00m"
    today_progress_percent = 0
    today_expected_str = "0h 00m"
    today_is_workday = False
    today_shift_name = "Folga"
    
    emp_for_shift = getattr(request.user, 'employee', None)
    if emp_for_shift:
        from attendance.models import get_work_info_for_date
        local_today = timezone.localtime(timezone.now()).date()
        work_info = get_work_info_for_date(emp_for_shift, local_today)
        today_is_workday = work_info.get('is_work_day', False)
        
        if today_is_workday:
            theo_mins = work_info.get('theo_minutes', 0)
            if theo_mins > 0:
                h = int(theo_mins // 60)
                m = int(theo_mins % 60)
                today_expected_str = f"{h}h {m:02d}m"
            
            entry = work_info.get('entry_time')
            exit_time = work_info.get('exit_time')
            if entry and exit_time:
                today_shift_name = f"{entry.strftime('%H:%M')} - {exit_time.strftime('%H:%M')}"
            else:
                today_shift_name = "Horário Livre"

            # Reutiliza o record_today já buscado pelo punch_context (lógica da linha 187)
            # para evitar uma segunda query idêntica ao banco
            record_today = AttendanceRecord.objects.filter(
                employee=emp_for_shift, date=local_today
            ).prefetch_related('punches').first()
            if record_today:
                record_today._prefetched_work_info = work_info

            worked_mins = 0
            if record_today:
                today_worked_str = record_today.net_hours_worked
                try:
                    parts = today_worked_str.replace('h', '').replace('m', '').split()
                    if len(parts) >= 2:
                        worked_mins = int(parts[0]) * 60 + int(parts[1])
                except:
                    pass
            
            if theo_mins > 0:
                today_progress_percent = min(100, int((worked_mins / theo_mins) * 100))
                
            today_is_working = record_today and record_today.current_state == 'IN'

    current_hour = timezone.localtime().hour
    if current_hour < 12:
        greeting = "Bom dia"
    elif current_hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"

    is_hr_admin = request.user.is_admin() or request.user.is_hr()
    rec_stats = None
    absenteeism_labels = []
    absenteeism_data = []

    if is_hr_admin:
        from recruitment.models import Candidate, JobOpening, PublicApplication
        rec_stats = {
            'candidates_hired': Candidate.objects.filter(status='HIRED').count(),
            'candidates_rejected': Candidate.objects.filter(status='REJECTED').count(),
            'candidates_in_progress': Candidate.objects.filter(status='IN_PROGRESS').count(),
            'open_vacancies': JobOpening.objects.filter(status='OPEN').count(),
            'total_vacancies': JobOpening.objects.count(),
            'public_pending': PublicApplication.objects.filter(status='PENDING').count(),
            'public_accepted': PublicApplication.objects.filter(status='ACCEPTED').count(),
            'public_rejected': PublicApplication.objects.filter(status='REJECTED').count(),
        }

        from leave.models import Leave
        today_date = timezone.localdate()
        pt_months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        
        for i in range(5, -1, -1):
            target_month = today_date.month - i
            target_year = today_date.year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
                
            leaves_count = Leave.objects.filter(
                status=Leave.STATUS_APPROVED,
                date__year=target_year,
                date__month=target_month
            ).count()
            
            label = f"{pt_months[target_month-1]}/{str(target_year)[-2:]}"
            absenteeism_labels.append(label)
            absenteeism_data.append(leaves_count)

    context = {
        'today_worked_mins': worked_mins if 'worked_mins' in locals() else 0,
        'today_theo_mins': theo_mins if 'theo_mins' in locals() else 0,
        'today_is_working': today_is_working if 'today_is_working' in locals() else False,
        'today_worked_str': today_worked_str,
        'today_progress_percent': today_progress_percent,
        'today_expected_str': today_expected_str,
        'today_is_workday': today_is_workday,
        'today_shift_name': today_shift_name,
        'active_employees': active_employees,
        'pending_leaves': pending_leaves,
        'supervisor_approved_leaves': supervisor_approved_leaves,
        'today_attendance': today_attendance,
        'pending_adjustments': pending_adjustments,
        'late_today': late_today,
        'birthdays': birthdays,
        'birthday_count': len(birthdays),
        'recent_leaves': recent_leaves,
        'recent_adjustments': recent_adjustments,
        'today': today,
        'next_action': next_action,
        'button_color': button_color,
        'button_text': button_text,
        'button_icon': button_icon,
        'announcements': announcements,
        'user_liked_ids': user_liked_ids,
        'my_team': my_team,
        'my_team_count': my_team_count,
        'my_supervisors': my_supervisors,
        'my_leaves_count': my_leaves_count,
        'my_upcoming_leaves_count': my_upcoming_leaves_count,
        'rec_stats': rec_stats,
        'absenteeism_labels': absenteeism_labels,
        'absenteeism_data': absenteeism_data,
        'greeting': greeting,
    }
    
    from leave.views import LeaveRequestForm
    from leave.models import LeaveType
    import json

    context['leave_form'] = LeaveRequestForm()

    leave_rules = {lt.id: lt.default_days for lt in LeaveType.objects.filter(is_deleted=False, default_days__isnull=False)}
    context['leave_rules_json'] = json.dumps(leave_rules)

    
    from buzz.models import ChangelogPost
    from datetime import timedelta
    dois_dias_atras = timezone.now() - timedelta(days=2)
    context['latest_changelogs'] = ChangelogPost.objects.filter(
        published_at__isnull=False,
        published_at__gte=dois_dias_atras
    ).order_by('-pinned', '-published_at')[:3]

    
    from performance.models import Survey, SurveyResponse
    pending_surveys = []
    if emp:
        from django.db.models import Q as DQ
        now_ts = timezone.now()
        answered_ids = SurveyResponse.objects.filter(employee=emp).values_list('survey_id', flat=True)
        all_surveys = Survey.objects.filter(status='PUBLISHED').exclude(id__in=answered_ids).filter(
            DQ(end_date__isnull=True) | DQ(end_date__gte=now_ts)
        ).order_by('-created_at')
        
        # Filtra em Python — o queryset já está avaliado, sem query extra por survey
        filtered_surveys = []
        for s in all_surveys:
            if s.is_leadership_survey:
                dept = emp.sub_division
                leader = emp.supervisors.first() or (dept.supervisor if dept else None)
                if leader == emp:
                    continue
            
            if s.target_type == 'ALL':
                filtered_surveys.append(s)
            elif s.target_type == 'LEGAL_ENTITY' and emp.legal_entity_id == s.target_legal_entity_id:
                filtered_surveys.append(s)
            elif s.target_type == 'SUBUNIT' and emp.department_id == s.target_subunit_id:
                filtered_surveys.append(s)
            elif s.target_type == 'CITY' and emp.city_id == s.target_city_id:
                filtered_surveys.append(s)
        pending_surveys = filtered_surveys

    context['pending_surveys'] = pending_surveys

    return render(request, 'core/dashboard.html', context)


@login_required
def profile(request):
    user = request.user
    emp = getattr(user, 'employee', None)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'personal_data' and emp:
            emp.first_name = request.POST.get('first_name', emp.first_name)
            emp.last_name = request.POST.get('last_name', emp.last_name)
            emp.ssn_number = request.POST.get('ssn_number', emp.ssn_number)
            
            birthday = request.POST.get('birthday')
            if birthday:
                emp.birthday = birthday
                
            emp.mobile = request.POST.get('mobile', emp.mobile)
            emp.save()
            
            from core.audit import log_action
            log_action(request, 'UPDATE', 'Funcionário atualizou seus próprios dados pessoais no Meu Perfil.')
            
            messages.success(request, 'Dados pessoais atualizados com sucesso.')
            return redirect('profile')

        elif action == 'account_data':
            email = request.POST.get('email')
            if email:
                user.email = email
                user.save()
                from core.audit import log_action
                log_action(request, 'UPDATE', 'Usuário atualizou seu email no Meu Perfil.')
                messages.success(request, 'Dados de acesso atualizados com sucesso.')
            return redirect('profile')

        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password and new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                from core.audit import log_action
                log_action(request, 'UPDATE', 'Usuário alterou sua própria senha.')
                messages.success(request, 'Senha atualizada com sucesso.')
            else:
                messages.error(request, 'As senhas não coincidem ou são inválidas.')
            return redirect('profile')

    return render(request, 'core/profile.html', {'user': user})




def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_admin() or request.user.is_hr()):
            messages.error(request, 'Acesso restrito a administradores ou RH.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper




@admin_required
def user_list(request):
    from .models import OrangeUser
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')

    users = OrangeUser.objects.filter(is_deleted=False).select_related('employee')

    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role:
        users = users.filter(role=role)

    users = users.order_by('username')
    return render(request, 'core/user_list.html', {
        'users': users,
        'q': q,
        'selected_role': role,
    })


@admin_required
def user_create(request):
    from .forms import UserCreateForm
    from .audit import log_action
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            log_action(request, 'USER_CREATE',
                f'Usuário "{user.username}" (perfil: {user.role}) criado por {request.user.username}.')
            messages.success(request, f'Usuário "{user.username}" criado com sucesso!')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'core/user_form.html', {
        'form': form,
        'title': 'Novo Usuário',
        'is_create': True,
    })


@admin_required
def user_edit(request, pk):
    from .models import OrangeUser
    from .forms import UserEditForm
    from .audit import log_action
    user_obj = get_object_or_404(OrangeUser, pk=pk)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            log_action(request, 'USER_EDIT',
                f'Usuário "{user_obj.username}" editado por {request.user.username}.')
            messages.success(request, f'Usuário "{user_obj.username}" atualizado!')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user_obj)

    return render(request, 'core/user_form.html', {
        'form': form,
        'title': f'Editar — {user_obj.username}',
        'user_obj': user_obj,
        'is_create': False,
    })


@admin_required
def user_reset_password(request, pk):
    from .forms import UserResetPasswordForm
    from .models import OrangeUser
    user_obj = get_object_or_404(OrangeUser, pk=pk)

    if request.method == 'POST':
        form = UserResetPasswordForm(request.POST)
        if form.is_valid():
            user_obj.set_password(form.cleaned_data['password1'])
            user_obj.save()
            messages.success(request, f'Senha de "{user_obj.username}" redefinida!')
            return redirect('user_list')
    else:
        form = UserResetPasswordForm()

    return render(request, 'core/user_form.html', {
        'form': form,
        'title': f'Redefinir Senha — {user_obj.username}',
        'user_obj': user_obj,
        'is_reset': True,
    })


@admin_required
def user_toggle_active(request, pk):
    from .models import OrangeUser
    user_obj = get_object_or_404(OrangeUser, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'Você não pode desativar sua própria conta.')
        return redirect('user_list')
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    status = 'ativado' if user_obj.is_active else 'desativado'
    messages.success(request, f'Usuário "{user_obj.username}" {status}.')
    return redirect('user_list')


@admin_required
def user_delete(request, pk):
    from .models import OrangeUser
    user_obj = get_object_or_404(OrangeUser, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'Você não pode excluir sua própria conta.')
        return redirect('user_list')
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Usuário "{username}" excluído.')
        return redirect('user_list')
    return render(request, 'core/user_confirm_delete.html', {'user_obj': user_obj})


from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

@login_required
@require_POST
def mark_notifications_read(request):
    """Marca todas as notificações não lidas como lidas e retorna a mesma página"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def landing_page(request):
    """Página pública de apresentação do navyBlue"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')





from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    from .audit import log_action
    log_action(request, 'LOGIN', f'Usuário "{user.username}" entrou no sistema.')


@login_required
def audit_log(request):
    """Página de Log de Auditoria — somente Admin"""
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')

    from .models import AuditLog
    from leave.models import LeaveActionLog

    
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    
    system_logs = AuditLog.objects.select_related('user').order_by('-created_at')
    if action_filter:
        system_logs = system_logs.filter(action=action_filter)
    if user_filter:
        system_logs = system_logs.filter(user__username__icontains=user_filter)
    if date_from:
        system_logs = system_logs.filter(created_at__date__gte=date_from)
    if date_to:
        system_logs = system_logs.filter(created_at__date__lte=date_to)

    
    leave_logs = LeaveActionLog.objects.select_related(
        'leave_request__employee', 'leave_request__leave_type', 'performed_by'
    ).order_by('-performed_at')
    if user_filter:
        leave_logs = leave_logs.filter(performed_by__username__icontains=user_filter)
    if date_from:
        leave_logs = leave_logs.filter(performed_at__date__gte=date_from)
    if date_to:
        leave_logs = leave_logs.filter(performed_at__date__lte=date_to)

    system_logs = system_logs[:200]
    leave_logs = leave_logs[:200]

    from .models import OrangeUser
    all_users = OrangeUser.objects.filter(is_deleted=False).order_by('username')

    context = {
        'system_logs': system_logs,
        'leave_logs': leave_logs,
        'action_choices': AuditLog.ACTION_CHOICES,
        'all_users': all_users,
        'filter_action': action_filter,
        'filter_user': user_filter,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    return render(request, 'core/audit_log.html', context)





import secrets
from datetime import timedelta
from django.core.mail import send_mail


def password_reset_request(request):
    """Passo 1 — Usuário informa o e-mail e recebe o código de 6 dígitos."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        from .models import OrangeUser, PasswordResetToken

        user = OrangeUser.objects.filter(email=email, is_active=True, is_deleted=False).first()
        if user:
            
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

            
            code = f"{secrets.randbelow(1000000):06d}"
            PasswordResetToken.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=15),
            )

            
            
            
            from emails.utils import send_custom_email
            
            from django.templatetags.static import static
            context_data = {
                'user_name': user.first_name or user.username,
                'code': code,
                'logo_url': request.build_absolute_uri(static('img/netline_logo_white.png'))
            }
            
            try:
                # Tenta enviar pelo gerenciador de templates customizados
                sent = send_custom_email('password_reset', context_data, user.email)
                if not sent:
                    # Fallback de segurança se o template tiver sido apagado
                    send_mail(
                        subject='Código de Redefinição de Senha — Netline RH',
                        message=f'Seu código de acesso é: {code}', 
                        from_email=dj_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
            except Exception as e:
                messages.error(request, f'Erro ao enviar o e-mail: {e}')
                return render(request, 'core/forgot_password.html')

        
        messages.success(request, 'Se este e-mail estiver cadastrado, você receberá o código em breve.')
        request.session['reset_email'] = email
        return redirect('password_reset_verify')

    return render(request, 'core/forgot_password.html')


def password_reset_verify(request):
    """Passo 2 — Usuário digita o código de 6 dígitos recebido por e-mail."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    email = request.session.get('reset_email')
    if not email:
        return redirect('password_reset_request')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        from .models import OrangeUser, PasswordResetToken

        user = OrangeUser.objects.filter(email=email).first()
        if user:
            token = PasswordResetToken.objects.filter(
                user=user, code=code, used=False
            ).order_by('-created_at').first()

            if token and token.is_valid():
                token.used = True
                token.save()
                request.session['reset_user_id'] = user.pk
                request.session.pop('reset_email', None)
                return redirect('password_reset_new')
            else:
                messages.error(request, 'Código inválido ou expirado. Tente novamente.')

    return render(request, 'core/forgot_password_verify.html', {'email': email})


def password_reset_new(request):
    """Passo 3 — Usuário define a nova senha."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('password_reset_request')

    if request.method == 'POST':
        from .models import OrangeUser
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        elif password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        else:
            user = OrangeUser.objects.filter(pk=user_id).first()
            if user:
                user.set_password(password1)
                user.save()
                request.session.pop('reset_user_id', None)
                messages.success(request, 'Senha redefinida com sucesso! Faça login.')
                return redirect('login')

    return render(request, 'core/forgot_password_new.html')






@login_required
def announcement_list(request):
    if not (request.user.is_admin() or request.user.is_supervisor() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a gerentes/RH.')
        return redirect('dashboard')
    
    from .models import Announcement
    announcements = Announcement.objects.all().select_related('author', 'department')
    
    from .forms import AnnouncementForm
    form = AnnouncementForm()
    
    return render(request, 'core/announcement_list.html', {'announcements': announcements, 'form': form})


@login_required
def announcement_detail(request, pk):
    from .models import Announcement
    anc = get_object_or_404(Announcement, pk=pk)
    
    
    from .models import AnnouncementLike
    user_liked = AnnouncementLike.objects.filter(announcement=anc, user=request.user).exists()

    
    return render(request, 'core/announcement_detail.html', {'anc': anc, 'user_liked': user_liked})


@login_required
def announcement_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a gerentes/RH.')
        return redirect('dashboard')
    
    from .forms import AnnouncementForm
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            messages.success(request, 'Aviso criado e publicado com sucesso!')
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
        
    return render(request, 'core/announcement_form.html', {'form': form, 'title': 'Novo Aviso no Mural'})


@login_required
def announcement_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor() or request.user.is_hr()):
        return redirect('dashboard')
        
    from .models import Announcement
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Aviso removido do mural.')
    return redirect('announcement_list')


from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def announcement_like_toggle(request, pk):
    """Rota AJAX para curtir/descurtir um aviso no Dashboard"""
    from .models import Announcement, AnnouncementLike
    announcement = get_object_or_404(Announcement, pk=pk)
    
    like, created = AnnouncementLike.objects.get_or_create(
        announcement=announcement, 
        user=request.user
    )
    
    if not created:
        
        like.delete()
        liked = False
    else:
        liked = True
        
    
    if hasattr(request.user, 'employee') and request.user.employee and announcement.buzz_post_id:
        try:
            from buzz.models import BuzzShare, BuzzLikeOnShare
            share = BuzzShare.objects.filter(post_id=announcement.buzz_post_id).first()
            if share:
                if not liked:
                    BuzzLikeOnShare.objects.filter(share=share, employee=request.user.employee).delete()
                else:
                    BuzzLikeOnShare.objects.get_or_create(share=share, employee=request.user.employee)
                share.num_of_likes = share.likes.count()
                share.save()
        except Exception:
            pass
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'liked': liked,
            'likes_count': announcement.likes.count()
        })
    else:
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def announcement_comment_add(request, pk):
    """Rota para enviar um comentário em um aviso"""
    from .models import Announcement, AnnouncementComment
    announcement = get_object_or_404(Announcement, pk=pk)
    
    text = request.POST.get('comment_text', '').strip()
    if text:
        AnnouncementComment.objects.create(
            announcement=announcement,
            user=request.user,
            text=text
        )
        messages.success(request, 'Comentário adicionado!')
        
    return redirect('dashboard')


from django.contrib.auth.decorators import user_passes_test
@login_required
@user_passes_test(lambda u: u.is_admin())
def module_permissions_list(request):
    from core.models import RoleModuleAccess
    roles = RoleModuleAccess.objects.all().order_by('role')
    
    if request.method == 'POST':
        
        role_type = request.POST.get('role_type')
        module = request.POST.get('module')
        is_active = request.POST.get('is_active') == 'true'
        
        target_role = RoleModuleAccess.objects.filter(role=role_type).first()
        if target_role:
            if hasattr(target_role, module):
                setattr(target_role, module, is_active)
                target_role.save()
                return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error'}, status=400)
        
    return render(request, 'core/module_permissions.html', {'roles': roles})

@login_required
def integrations_dashboard(request):
    from core.models import Config
    cloudinary_configured = (
        Config.objects.filter(name='CLOUDINARY_CLOUD_NAME').exists() and 
        Config.objects.filter(name='CLOUDINARY_API_KEY').exists()
    )
    
    cloud_name = Config.objects.filter(name='CLOUDINARY_CLOUD_NAME').first()
    api_key = Config.objects.filter(name='CLOUDINARY_API_KEY').first()
    
    active_cloud = Config.objects.filter(name='ACTIVE_CLOUD_STORAGE').first()
    active_cloud_val = active_cloud.value if active_cloud else 'CLOUDINARY'
    
    aws_bucket_name = Config.objects.filter(name='AWS_STORAGE_BUCKET_NAME').first()
    aws_access_key = Config.objects.filter(name='AWS_ACCESS_KEY_ID').first()
    aws_region = Config.objects.filter(name='AWS_S3_REGION_NAME').first()
    
    s3_configured = aws_bucket_name and aws_access_key
    
    context = {
        'title': 'Integrações & API',
        'active_cloud': active_cloud_val,
        'cloudinary_configured': cloudinary_configured,
        'cloudinary_cloud_name': cloud_name.value if cloud_name else '',
        'cloudinary_api_key': api_key.value if api_key else '',
        's3_configured': bool(s3_configured),
        'aws_bucket_name': aws_bucket_name.value if aws_bucket_name else '',
        'aws_access_key': aws_access_key.value if aws_access_key else '',
        'aws_region': aws_region.value if aws_region else 'us-east-1',
    }
    return render(request, 'core/integrations.html', context)

@login_required
@require_POST
def save_cloudinary_integration(request):
    if not request.user.is_admin():
        return JsonResponse({'status': 'error', 'message': 'Acesso negado'}, status=403)
        
    from core.models import Config
    
    cloud_name = request.POST.get('cloud_name', '').strip()
    api_key = request.POST.get('api_key', '').strip()
    api_secret = request.POST.get('api_secret', '').strip()
    
    if cloud_name and api_key and api_secret:
        Config.objects.update_or_create(name='CLOUDINARY_CLOUD_NAME', defaults={'value': cloud_name})
        Config.objects.update_or_create(name='CLOUDINARY_API_KEY', defaults={'value': api_key})
        Config.objects.update_or_create(name='CLOUDINARY_API_SECRET', defaults={'value': api_secret})
        
        # Opcional: Reconfigurar na mesma hora para uso imediato (se for usado no mesmo processo WSGI)
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        messages.success(request, 'Integração com Cloudinary salva com sucesso!')
    else:
        messages.error(request, 'Todos os campos do Cloudinary são obrigatórios.')
        
    return redirect('integrations')

@login_required
@require_POST
def save_s3_integration(request):
    if not request.user.is_admin():
        return JsonResponse({'status': 'error', 'message': 'Acesso negado'}, status=403)
        
    from core.models import Config
    
    bucket_name = request.POST.get('aws_bucket_name', '').strip()
    access_key = request.POST.get('aws_access_key', '').strip()
    secret_key = request.POST.get('aws_secret_key', '').strip()
    region = request.POST.get('aws_region', '').strip()
    set_active = request.POST.get('set_active') == 'true'
    
    if bucket_name and access_key and secret_key:
        Config.objects.update_or_create(name='AWS_STORAGE_BUCKET_NAME', defaults={'value': bucket_name})
        Config.objects.update_or_create(name='AWS_ACCESS_KEY_ID', defaults={'value': access_key})
        Config.objects.update_or_create(name='AWS_SECRET_ACCESS_KEY', defaults={'value': secret_key})
        
        if region:
            Config.objects.update_or_create(name='AWS_S3_REGION_NAME', defaults={'value': region})
            
        if set_active:
            Config.objects.update_or_create(name='ACTIVE_CLOUD_STORAGE', defaults={'value': 'S3'})
        else:
            active_cloud = Config.objects.filter(name='ACTIVE_CLOUD_STORAGE').first()
            if active_cloud and active_cloud.value == 'S3':
                Config.objects.update_or_create(name='ACTIVE_CLOUD_STORAGE', defaults={'value': 'CLOUDINARY'})
                
        messages.success(request, 'Configurações do AWS S3 salvas com sucesso!')
    else:
        messages.error(request, 'Todos os campos obrigatórios do AWS S3 devem ser preenchidos.')
        
    return redirect('integrations')
