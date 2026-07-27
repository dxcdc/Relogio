from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import require_module
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import JobOpening, Candidate, Interview, InterviewFeedback, Skill, PublicApplication
from .forms import JobOpeningForm, CandidateForm, InterviewForm, InterviewFeedbackForm, PublicApplicationForm
from .match import calculate_match, skill_breakdown
from agenda.models import Event
from pim.models import Employee
from admin_app.models import Location, City


def is_admin_or_hr(user):
    return user.is_admin() or user.is_hr()


# ===========================================================================
# JOB OPENINGS
# ===========================================================================

@login_required
@require_module('performance')
def job_list(request):
    if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
    jobs = JobOpening.objects.prefetch_related('required_skills', 'desired_skills').all()
    is_modal = request.GET.get('is_modal') == '1'
    if is_modal:
        jobs = jobs.filter(status='OPEN')

    # Count pending applications per job
    pending_counts = {}
    for job in jobs:
        pending_counts[job.id] = job.applications.filter(status='PENDING').count()
    return render(request, 'recruitment/job_list.html', {
        'jobs': jobs,
        'pending_counts': pending_counts,
        'is_modal': is_modal,
    })


@login_required
def job_create(request):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito ao RH/Administradores.')
        return redirect('job_list')
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vaga criada com sucesso!')
            if request.GET.get('popup'):
                from django.http import HttpResponse
                return HttpResponse("""
                    <script>
                        window.top.postMessage({type:'iframeFormSaved'}, '*');
                    </script>
                """)
            return redirect('job_list')
    else:
        form = JobOpeningForm()
    skills_by_category = _skills_grouped()
    return render(request, 'recruitment/job_form.html', {
        'form': form,
        'title': 'Nova Vaga',
        'skills_by_category': skills_by_category,
    })


@login_required
def job_edit(request, pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('job_list')
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == 'POST':
        form = JobOpeningForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vaga atualizada!')
            if request.GET.get('popup'):
                from django.http import HttpResponse
                return HttpResponse("""
                    <script>
                        window.top.postMessage({type:'iframeFormSaved'}, '*');
                    </script>
                """)
            return redirect('job_list')
    else:
        form = JobOpeningForm(instance=job)
    skills_by_category = _skills_grouped()
    return render(request, 'recruitment/job_form.html', {
        'form': form,
        'title': 'Editar Vaga',
        'job': job,
        'skills_by_category': skills_by_category,
    })


@login_required
def job_delete(request, pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('job_list')
    job = get_object_or_404(JobOpening, pk=pk)
    job.delete()
    messages.success(request, 'Vaga excluída com sucesso!')
    return redirect('job_list')


def _skills_grouped():
    """Helper: returns skills queryset grouped by category."""
    from itertools import groupby
    skills = Skill.objects.order_by('category', 'name')
    grouped = {}
    for skill in skills:
        grouped.setdefault(skill.get_category_display(), []).append(skill)
    return grouped


# ===========================================================================
# SKILL MANAGEMENT
# ===========================================================================

@login_required
def skill_list(request):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'tech')
        if name:
            if Skill.objects.filter(name__iexact=name).exists():
                messages.warning(request, f'A skill "{name}" já existe.')
            else:
                Skill.objects.create(name=name, category=category)
                messages.success(request, f'Skill "{name}" criada com sucesso!')
        return redirect('skill_list')

    skills = Skill.objects.order_by('category', 'name')
    categories = Skill.CATEGORY_CHOICES
    return render(request, 'recruitment/skill_list.html', {
        'skills': skills,
        'categories': categories,
    })


@login_required
def skill_delete(request, pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('skill_list')
    skill = get_object_or_404(Skill, pk=pk)
    skill.delete()
    messages.success(request, f'Skill "{skill.name}" removida.')
    return redirect('skill_list')


# ===========================================================================
# PUBLIC PORTAL (no login required)
# ===========================================================================

def public_job_list(request):
    """Public listing of open vacancies."""
    jobs = JobOpening.objects.filter(status='OPEN').prefetch_related('required_skills', 'desired_skills')
    return render(request, 'recruitment/public_job_list.html', {'jobs': jobs})


def public_apply(request, pk):
    """Public application form for a specific vacancy."""
    job = get_object_or_404(JobOpening, pk=pk, status='OPEN')
    skills_by_category = _skills_grouped()

    if request.method == 'POST':
        form = PublicApplicationForm(request.POST, request.FILES, job_opening=job)
        if form.is_valid():
            app = form.save(commit=False)
            app.job_opening = job
            app.save()
            form.save_m2m()

            # Calculate match score immediately
            skill_ids = app.skills.values_list('id', flat=True)
            app.match_score = calculate_match(list(skill_ids), job)
            app.save(update_fields=['match_score'])

            return redirect('apply_thanks')
    else:
        form = PublicApplicationForm(job_opening=job)

    return render(request, 'recruitment/public_apply.html', {
        'form': form,
        'job': job,
        'skills_by_category': skills_by_category,
    })


def apply_thanks(request):
    """Thank you confirmation page after successful application."""
    return render(request, 'recruitment/apply_thanks.html')


# ===========================================================================
# APPLICATIONS REVIEW (HR/Admin internal panel)
# ===========================================================================

@login_required
@require_module('performance')
def applications_review(request, job_pk):
    """Internal panel: list pending public applications for a job opening."""
    if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    job = get_object_or_404(JobOpening, pk=job_pk)
    status_filter = request.GET.get('status', 'PENDING')
    applications = job.applications.prefetch_related('skills').filter(status=status_filter).order_by('-match_score', '-created_at')

    return render(request, 'recruitment/applications_review.html', {
        'job': job,
        'applications': applications,
        'status_filter': status_filter,
        'pending_count':  job.applications.filter(status='PENDING').count(),
        'accepted_count': job.applications.filter(status='ACCEPTED').count(),
        'rejected_count': job.applications.filter(status='REJECTED').count(),
        'total_count':    job.applications.count(),
    })


@login_required
def application_accept(request, app_pk):
    """Accept a public application → create Candidate in pipeline (screening)."""
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    app = get_object_or_404(PublicApplication, pk=app_pk)

    # Avoid duplicate candidates for same email + job
    if Candidate.objects.filter(email=app.email, job_opening=app.job_opening).exists():
        messages.warning(request, f'{app.name} já existe como candidato nesta vaga.')
        return redirect('applications_review', job_pk=app.job_opening.pk)

    # Create Candidate from application
    candidate = Candidate.objects.create(
        name=app.name,
        email=app.email,
        phone=app.phone,
        linkedin_url=app.linkedin_url,
        resume=app.resume,
        job_opening=app.job_opening,
        match_score=app.match_score,
        current_stage='screening',
        status='IN_PROGRESS',
    )
    candidate.skills.set(app.skills.all())
    candidate.save()

    # Mark application as accepted
    app.status = 'ACCEPTED'
    app.save(update_fields=['status'])

    messages.success(request, f'✅ {app.name} aceito(a) e adicionado(a) à pipeline na etapa de Triagem!')
    return redirect('applications_review', job_pk=app.job_opening.pk)


@login_required
def application_reject(request, app_pk):
    """Reject a public application."""
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    app = get_object_or_404(PublicApplication, pk=app_pk)
    notes = request.POST.get('rh_notes', '')
    feedback = request.POST.get('candidate_feedback', '').strip()
    
    app.status = 'REJECTED'
    app.rh_notes = notes
    app.save(update_fields=['status', 'rh_notes'])

    if feedback:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags

        subject = f"Atualização sobre a vaga: {app.job_opening.title}"
        context = {
            'candidate_name': app.name,
            'job_title': app.job_opening.title,
            'rejection_reason': feedback,
        }
        html_content = render_to_string('email/rejection_feedback.html', context)
        text_content = strip_tags(html_content)
        
        try:
            from emails.utils import send_custom_email
            
            sent = send_custom_email('candidate_rejection', context, app.email)
            if not sent:
                email = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [app.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=True)
            messages.success(request, f'Email de feedback enviado para {app.name}.')
        except Exception:
            messages.warning(request, f'O candidato foi reprovado, mas houve um erro ao enviar o email para {app.name}.')

    messages.info(request, f'{app.name} foi marcado(a) como reprovado(a).')
    return redirect('applications_review', job_pk=app.job_opening.pk)


@login_required
@require_module('performance')
def application_detail(request, app_pk):
    """Full profile view of a public application for HR analysis."""
    if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    app = get_object_or_404(
        PublicApplication.objects.select_related('job_opening').prefetch_related('skills'),
        pk=app_pk
    )

    # Skill breakdown vs job requirements
    breakdown = skill_breakdown(
        app.skills.values_list('id', flat=True),
        app.job_opening
    )

    return render(request, 'recruitment/application_detail.html', {
        'app': app,
        'breakdown': breakdown,
    })


# ===========================================================================
# PIPELINE KANBAN DASHBOARD
# ===========================================================================

@login_required
@require_module('performance')
def candidate_pipeline(request):
    if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    candidates = Candidate.objects.select_related('job_opening').prefetch_related('interviews', 'skills').exclude(status='REJECTED').exclude(onboarded=True)

    job_id = request.GET.get('job_opening')
    current_job_id = None
    if job_id and job_id.isdigit():
        current_job_id = int(job_id)
        candidates = candidates.filter(job_opening_id=current_job_id)

    # Auto-advance logic for probations
    now = timezone.now()
    # Check candidates in probation_45
    for c in candidates.filter(current_stage='probation_45'):
        if c.stage_updated_at and now >= c.stage_updated_at + timedelta(days=45):
            c.current_stage = 'probation_90'
            c.save()
            
    # Check candidates in probation_90 (45 days after entering probation_90)
    for c in candidates.filter(current_stage='probation_90'):
        if c.stage_updated_at and now >= c.stage_updated_at + timedelta(days=45):
            c.current_stage = 'hired'
            c.save()

    stages = [
        ('screening',          'Triagem'),
        ('interview',          'Entrevista'),
        ('psych_test',         'Teste Psicológico'),
        ('practical_test',     'Teste Prático'),
        ('probation_45',       'Estágio 45 d'),
        ('probation_90',       'Estágio 90 d'),
        ('hired',              'Efetivação'),
    ]

    pipeline = {stage_key: [] for stage_key, _ in stages}
    for c in candidates:
        if c.current_stage in pipeline:
            pipeline[c.current_stage].append(c)

    jobs = JobOpening.objects.filter(status='OPEN')
    locations = Location.objects.all().order_by('name')
    cities = City.objects.all().order_by('name')

    return render(request, 'recruitment/pipeline.html', {
        'pipeline': pipeline,
        'stages': stages,
        'jobs': jobs,
        'current_job_id': current_job_id,
        'total_candidates': candidates.count(),
        'locations': locations,
        'cities': cities,
    })


@login_required
@csrf_exempt
def update_candidate_stage_ajax(request):
    if request.method == 'POST':
        if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
            return JsonResponse({'success': False, 'message': 'Acesso negado'}, status=403)
        candidate_id = request.POST.get('candidate_id')
        new_stage = request.POST.get('stage')
        new_status = request.POST.get('status')
        rejection_reason = request.POST.get('rejection_reason')

        candidate = get_object_or_404(Candidate, id=candidate_id)
        if new_stage in dict(Candidate.STAGE_CHOICES):
            candidate.current_stage = new_stage
        if new_status in dict(Candidate.STATUS_CHOICES):
            candidate.status = new_status
            
        if new_status == 'REJECTED' and rejection_reason:
            candidate.rejection_reason = rejection_reason
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags

            subject = f"Atualização sobre o processo seletivo: {candidate.job_opening.title}"
            
            context = {
                'candidate_name': candidate.name,
                'job_title': candidate.job_opening.title,
                'rejection_reason': rejection_reason,
            }
            html_content = render_to_string('email/rejection_feedback.html', context)
            text_content = strip_tags(html_content)
            
            try:
                from emails.utils import send_custom_email
                
                sent = send_custom_email('candidate_rejection', context, candidate.email)
                if not sent:
                    email = EmailMultiAlternatives(
                        subject,
                        text_content,
                        settings.DEFAULT_FROM_EMAIL,
                        [candidate.email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send(fail_silently=True)
            except Exception as e:
                pass

        candidate.save()

        return JsonResponse({
            'success': True,
            'stage': candidate.current_stage,
            'status': candidate.status,
            'job_closed': False,
        })
    return JsonResponse({'success': False, 'message': 'Método inválido'}, status=400)


@login_required
def onboard_as_employee(request, candidate_id):
    """
    Cria automaticamente um Employee + OrangeUser a partir dos dados do candidato contratado.
    Retorna JSON com os dados do novo usuário criado (username e senha provisória).
    """
    if not (is_admin_or_hr(request.user)):
        return JsonResponse({'success': False, 'message': 'Acesso negado.'}, status=403)

    candidate = get_object_or_404(Candidate, id=candidate_id)

    if candidate.status != 'HIRED':
        return JsonResponse({'success': False, 'message': 'Candidato não está com status de Contratado.'}, status=400)

    from pim.models import Employee
    from core.models import OrangeUser
    import random, string
    from django.utils import timezone

    # Split candidate name
    parts = candidate.name.strip().split()
    first_name = parts[0]
    last_name = ' '.join(parts[1:]) if len(parts) > 1 else 'Sem Sobrenome'

    # Generate unique username from name
    base_username = (first_name + '.' + last_name.split()[0]).lower() if len(parts) > 1 else first_name.lower()
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '.')
    username = base_username
    counter = 1
    while OrangeUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    # Random provisional password
    provisional_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Get job title and department directly from the job opening
    job_title_obj  = candidate.job_opening.job_title   # FK set when creating the vacancy
    department_obj = candidate.job_opening.department  # FK set when creating the vacancy

    # Create Employee record
    employee = Employee.objects.create(
        first_name=first_name,
        last_name=last_name,
        work_email=candidate.email,
        mobile=candidate.phone or '',
        job_title=job_title_obj,
        sub_division=department_obj,
        joined_date=timezone.localdate(),
        state=Employee.STATE_ACTIVE,
    )

    # Create OrangeUser linked to employee
    user = OrangeUser.objects.create_user(
        username=username,
        email=candidate.email,
        password=provisional_password,
        first_name=first_name,
        last_name=last_name,
        role=OrangeUser.ROLE_ESS,
    )
    user.employee = employee
    user.save()

    # Mark candidate as fully onboarded so they leave the pipeline
    candidate.onboarded = True
    candidate.save(update_fields=['onboarded'])

    # -----------------------------------------------------------------------
    # Encerramento automático da vaga quando a meta de vagas é atingida
    # -----------------------------------------------------------------------
    job = candidate.job_opening
    job_closed = False
    if job.status == 'OPEN':
        hired_count = Candidate.objects.filter(job_opening=job, status='HIRED', onboarded=True).count()
        if hired_count >= job.quantity:
            job.status = 'CLOSED'
            job.save(update_fields=['status'])
            job_closed = True
            
            # Reprovar automaticamente os demais candidatos em andamento
            outros = Candidate.objects.filter(
                job_opening=job,
                status='IN_PROGRESS'
            )
            outros.update(
                status='REJECTED',
                rejection_reason='Vaga encerrada — a quantidade necessária de candidatos foi contratada.'
            )

    return JsonResponse({
        'success': True,
        'employee_id': employee.id,
        'username': username,
        'password': provisional_password,
        'name': candidate.name,
        'email': candidate.email,
        'job_closed': job_closed,
    })


@login_required
def send_onboard_email(request, candidate_id):
    """Send welcome email with credentials to the newly hired employee. Called on 'Concluir'."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)

    candidate = get_object_or_404(Candidate, id=candidate_id)
    username = request.POST.get('username')
    password = request.POST.get('password')

    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags

        parts = candidate.name.strip().split()
        first_name = parts[0]

        try:
            from emails.utils import send_custom_email
            
            context = {
                'first_name': first_name,
                'username': username,
                'temp_password': password,
            }
            
            sent = send_custom_email('onboard_welcome', context, candidate.email)
            if not sent:
                email_msg = EmailMultiAlternatives(
                    subject='Boas-vindas! Suas credenciais de acesso ao CDC',
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[candidate.email],
                )
                email_msg.attach_alternative(html_content, 'text/html')
                email_msg.send(fail_silently=False)
        except Exception:
            pass
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})



# ===========================================================================
# CANDIDATE CRUD
# ===========================================================================

@login_required
@require_module('performance')
def candidate_list(request):
    if not (is_admin_or_hr(request.user) or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    candidates = Candidate.objects.select_related('job_opening').prefetch_related('skills').all()

    # Search filter (name / email)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        candidates = candidates.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Job opening filter
    job_id = request.GET.get('job_opening', '').strip()
    if job_id and job_id.isdigit():
        candidates = candidates.filter(job_opening_id=int(job_id))

    # Stage filter
    stage = request.GET.get('stage', '').strip()
    if stage:
        candidates = candidates.filter(current_stage=stage)

    # Status filter
    status = request.GET.get('status', '').strip()
    if status:
        candidates = candidates.filter(status=status)

    # Ordering
    order_by = request.GET.get('order_by', '-created_at').strip()
    if order_by in ['name', '-name', 'match_score', '-match_score', 'created_at', '-created_at']:
        candidates = candidates.order_by(order_by)
    else:
        candidates = candidates.order_by('-created_at')

    # Get choices for filters
    jobs = JobOpening.objects.all()
    stages = Candidate.STAGE_CHOICES
    statuses = Candidate.STATUS_CHOICES

    # Summary statistics
    total_count = candidates.count()
    hired_count = candidates.filter(status='HIRED').count()
    in_progress_count = candidates.filter(status='IN_PROGRESS').count()
    rejected_count = candidates.filter(status='REJECTED').count()

    return render(request, 'recruitment/candidate_list.html', {
        'candidates': candidates,
        'jobs': jobs,
        'stages': stages,
        'statuses': statuses,
        'total_count': total_count,
        'hired_count': hired_count,
        'in_progress_count': in_progress_count,
        'rejected_count': rejected_count,
        'search_query': search_query,
        'selected_job': int(job_id) if job_id and job_id.isdigit() else None,
        'selected_stage': stage,
        'selected_status': status,
        'selected_order_by': order_by,
    })


@login_required
def candidate_create(request):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('candidate_pipeline')
    is_popup = request.GET.get('popup') == '1' or request.POST.get('popup') == '1'
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.save()
            form.save_m2m()
            # Recalculate match score
            skill_ids = candidate.skills.values_list('id', flat=True)
            candidate.match_score = calculate_match(list(skill_ids), candidate.job_opening)
            candidate.save(update_fields=['match_score'])
            messages.success(request, 'Candidato cadastrado com sucesso!')
            if is_popup:
                from django.http import HttpResponse
                return HttpResponse('''
                    <!DOCTYPE html><html><body>
                    <script>
                        window.parent.postMessage({ type: "iframeFormSaved" }, "*");
                    </script>
                    </body></html>
                ''')
            return redirect('candidate_profile', pk=candidate.pk)
    else:
        form = CandidateForm()
    skills_by_category = _skills_grouped()
    return render(request, 'recruitment/candidate_form.html', {
        'form': form,
        'title': 'Cadastrar Candidato',
        'skills_by_category': skills_by_category,
        'is_popup': is_popup,
    })


@login_required
def candidate_edit(request, pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('candidate_pipeline')
    candidate = get_object_or_404(Candidate, pk=pk)
    is_popup = request.GET.get('popup') == '1' or request.POST.get('popup') == '1'
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.save()
            form.save_m2m()
            skill_ids = candidate.skills.values_list('id', flat=True)
            candidate.match_score = calculate_match(list(skill_ids), candidate.job_opening)
            candidate.save(update_fields=['match_score'])
            messages.success(request, 'Cadastro do candidato atualizado!')
            if is_popup:
                # Em modo popup: redireciona para URL de sucesso sem popup=1
                # O JS do pai detecta a saída do popup e fecha o modal + recarrega
                from django.http import HttpResponse
                return HttpResponse('''
                    <!DOCTYPE html><html><body>
                    <script>
                        window.parent.postMessage({ type: "iframeFormSaved" }, "*");
                    </script>
                    </body></html>
                ''')
            return redirect('candidate_profile', pk=pk)
    else:
        form = CandidateForm(instance=candidate)
    skills_by_category = _skills_grouped()
    return render(request, 'recruitment/candidate_form.html', {
        'form': form,
        'title': 'Editar Candidato',
        'candidate': candidate,
        'skills_by_category': skills_by_category,
        'is_popup': is_popup,
    })


@login_required
def candidate_delete(request, pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('candidate_pipeline')
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.delete()
    messages.success(request, 'Candidato excluído com sucesso.')
    return redirect('candidate_pipeline')


@login_required
@require_module('performance')
def candidate_profile(request, pk):
    candidate = get_object_or_404(
        Candidate.objects.select_related('job_opening').prefetch_related('skills'),
        pk=pk
    )
    user_emp = getattr(request.user, 'employee', None)
    is_authorized = is_admin_or_hr(request.user)

    interviews = candidate.interviews.prefetch_related('interviewers', 'feedbacks__interviewer').all()

    if not is_authorized and user_emp:
        for iv in interviews:
            if user_emp in iv.interviewers.all():
                is_authorized = True
                break

    if not is_authorized:
        messages.error(request, 'Você não possui permissão para visualizar este perfil.')
        return redirect('dashboard')

    # Skill breakdown vs job the candidate applied to
    breakdown = skill_breakdown(
        candidate.skills.values_list('id', flat=True),
        candidate.job_opening
    )

    # Compatibility chart: match against ALL open job openings
    candidate_skill_ids = set(candidate.skills.values_list('id', flat=True))
    open_jobs = JobOpening.objects.filter(status='OPEN').prefetch_related('required_skills', 'desired_skills')
    job_compatibility = []
    for job in open_jobs:
        score = calculate_match(candidate_skill_ids, job)
        job_compatibility.append({
            'title': job.title,
            'score': score,
            'is_current': job.id == candidate.job_opening_id,
            'job_id': job.id,
        })
    # Sort by score descending, current job first if tie
    job_compatibility.sort(key=lambda x: (x['score'], x['is_current']), reverse=True)

    return render(request, 'recruitment/candidate_profile.html', {
        'candidate': candidate,
        'interviews': interviews,
        'user_emp': user_emp,
        'breakdown': breakdown,
        'job_compatibility': job_compatibility,
    })


# ===========================================================================
# INTERVIEW SCHEDULING & FEEDBACK
# ===========================================================================

@login_required
def interview_schedule(request, candidate_pk):
    if not is_admin_or_hr(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect('candidate_profile', pk=candidate_pk)

    candidate = get_object_or_404(Candidate, pk=candidate_pk)

    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.candidate = candidate
            interview.save()
            form.save_m2m()

            title = f"Entrevista: {candidate.name} ({interview.get_stage_display()})"
            organizer = interview.interviewers.first() or getattr(request.user, 'employee', None)

            event = Event.objects.create(
                title=title,
                event_type='entrevista',
                organizer=organizer,
                start_date=interview.date,
                end_date=interview.date + timedelta(hours=1),
                notes=f"Entrevista para a vaga: {candidate.job_opening.title}\n\nObservações: {interview.notes or ''}",
                status='agendado'
            )
            event.employees.set(interview.interviewers.all())
            event.save()

            interview.linked_event = event
            interview.save()

            messages.success(request, 'Entrevista agendada e sincronizada no calendário!')
            return redirect('candidate_profile', pk=candidate_pk)
    else:
        initial_data = {
            'candidate': candidate,
            'stage': candidate.current_stage if candidate.current_stage in ['interview', 'psych_test', 'practical_test'] else 'interview'
        }
        form = InterviewForm(initial=initial_data)

    return render(request, 'recruitment/interview_form.html', {
        'form': form,
        'candidate': candidate,
        'title': f"Agendar Entrevista — {candidate.name}"
    })


@login_required
def interview_feedback_create(request, interview_pk):
    interview = get_object_or_404(Interview.objects.select_related('candidate'), pk=interview_pk)
    user_emp = getattr(request.user, 'employee', None)

    if not user_emp:
        messages.error(request, 'Perfil de funcionário não encontrado.')
        return redirect('dashboard')

    if not (is_admin_or_hr(request.user) or user_emp in interview.interviewers.all()):
        messages.error(request, 'Acesso negado. Apenas entrevistadores designados podem registrar feedback.')
        return redirect('candidate_profile', pk=interview.candidate.pk)

    if InterviewFeedback.objects.filter(interview=interview, interviewer=user_emp).exists():
        messages.info(request, 'Você já registrou o seu feedback para esta entrevista.')
        return redirect('candidate_profile', pk=interview.candidate.pk)

    if request.method == 'POST':
        form = InterviewFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.interview = interview
            feedback.interviewer = user_emp
            feedback.save()

            interview.status = 'COMPLETED'
            interview.save()

            messages.success(request, 'Feedback registrado com sucesso!')
            return redirect('candidate_profile', pk=interview.candidate.pk)
    else:
        form = InterviewFeedbackForm()

    return render(request, 'recruitment/feedback_form.html', {
        'form': form,
        'interview': interview,
        'title': f"Parecer da Entrevista — {interview.candidate.name}"
    })

@login_required
def recruitment_metrics(request):
    from collections import Counter
    from django.db.models import Count
    jobs = JobOpening.objects.all()
    candidates = Candidate.objects.all()

    total_candidates = candidates.count()
    active_candidates = candidates.filter(status='IN_PROGRESS').count()
    hired_candidates = candidates.filter(status='HIRED').count()
    rejected_candidates = candidates.filter(status='REJECTED').count()

    success_rate = (hired_candidates / total_candidates * 100) if total_candidates > 0 else 0

    jobs_data = []
    for j in jobs:
        cnt = candidates.filter(job_opening=j).count()
        jobs_data.append({'title': j.title, 'count': cnt})
    jobs_data.sort(key=lambda x: x['count'], reverse=True)

    rejection_funnel = {}
    for stage_key, stage_name in Candidate.STAGE_CHOICES:
        cnt = candidates.filter(status='REJECTED', current_stage=stage_key).count()
        if cnt > 0:
            rejection_funnel[stage_name] = cnt

    reasons = candidates.filter(status='REJECTED').exclude(rejection_reason__isnull=True).exclude(rejection_reason='').values_list('rejection_reason', flat=True)
    reason_counts = Counter(reasons).most_common(5)

    context = {
        'total_candidates': total_candidates,
        'active_candidates': active_candidates,
        'hired_candidates': hired_candidates,
        'rejected_candidates': rejected_candidates,
        'success_rate': round(success_rate, 1),
        'jobs_data': jobs_data[:10],
        'rejection_funnel': rejection_funnel,
        'reason_counts': reason_counts
    }
    return render(request, 'recruitment/metrics.html', context)
