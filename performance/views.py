from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import require_module
from django.contrib import messages
from .models import Kpi, PerformanceReview, Reviewer, ReviewerRating, PerformanceTracker, PerformanceTrackerLog, ReviewerGroup
from django import forms


class KpiForm(forms.ModelForm):
    class Meta:
        model = Kpi
        fields = ['title', 'job_title', 'min_rating', 'max_rating', 'is_default']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'min_rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_rating': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['employee', 'job_title', 'department', 'review_period_start', 'review_period_end', 'due_date']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'review_period_start': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'review_period_end': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class TrackerForm(forms.ModelForm):
    class Meta:
        model = PerformanceTracker
        fields = ['tracker_name', 'employee']
        widgets = {
            'tracker_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
        }


class TrackerLogForm(forms.ModelForm):
    class Meta:
        model = PerformanceTrackerLog
        fields = ['log', 'achievement']
        widgets = {
            'log': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'achievement': forms.Select(attrs={'class': 'form-select'},
                                        choices=[(i, str(i)) for i in range(6)]),
        }




@login_required
@require_module('performance')
def review_list(request):
    if request.user.is_admin():
        reviews = PerformanceReview.objects.all()
    else:
        emp = getattr(request.user, 'employee', None)
        reviews = PerformanceReview.objects.filter(employee=emp) if emp else PerformanceReview.objects.none()
    reviews = reviews.select_related('employee', 'job_title', 'department').order_by('-due_date')
    return render(request, 'performance/review_list.html', {'reviews': reviews})


@login_required
@require_module('performance')
def review_create(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save()
            messages.success(request, 'Avaliacao criada!')
            return redirect('review_detail', pk=review.pk)
    else:
        form = ReviewForm()
    return render(request, 'performance/review_form.html', {'form': form, 'title': 'Nova Avaliacao'})


@login_required
def review_edit(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    review = get_object_or_404(PerformanceReview, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avaliacao atualizada!')
            return redirect('review_detail', pk=pk)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'performance/review_form.html', {'form': form, 'title': 'Editar Avaliacao'})


@login_required
def review_delete(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    review = get_object_or_404(PerformanceReview, pk=pk)
    review.delete()
    messages.success(request, 'Avaliacao excluida.')
    return redirect('review_list')


@login_required
def review_detail(request, pk):
    review = get_object_or_404(
        PerformanceReview.objects.prefetch_related('reviewers__ratings__kpi', 'reviewers__employee'), pk=pk
    )
    return render(request, 'performance/review_detail.html', {'review': review})




@login_required
def kpi_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    kpis = Kpi.objects.select_related('job_title').all()
    return render(request, 'performance/kpi_list.html', {'kpis': kpis})


@login_required
def kpi_create(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'KPI criado!')
            return redirect('kpi_list')
    else:
        form = KpiForm()
    return render(request, 'performance/review_form.html', {'form': form, 'title': 'Novo KPI'})


@login_required
def kpi_edit(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    kpi = get_object_or_404(Kpi, pk=pk)
    if request.method == 'POST':
        form = KpiForm(request.POST, instance=kpi)
        if form.is_valid():
            form.save()
            messages.success(request, 'KPI atualizado!')
            return redirect('kpi_list')
    else:
        form = KpiForm(instance=kpi)
    return render(request, 'performance/review_form.html', {'form': form, 'title': 'Editar KPI'})


@login_required
def kpi_delete(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    kpi = get_object_or_404(Kpi, pk=pk)
    kpi.delete()
    messages.success(request, 'KPI excluido.')
    return redirect('kpi_list')




@login_required
def tracker_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    trackers = PerformanceTracker.objects.select_related('employee').order_by('-added_date')
    return render(request, 'performance/tracker_list.html', {'trackers': trackers})


@login_required
def tracker_create(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = TrackerForm(request.POST)
        if form.is_valid():
            tracker = form.save()
            messages.success(request, 'Tracker criado!')
            return redirect('tracker_detail', pk=tracker.pk)
    else:
        form = TrackerForm()
    return render(request, 'performance/review_form.html', {'form': form, 'title': 'Novo Tracker'})


@login_required
def tracker_delete(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    tracker = get_object_or_404(PerformanceTracker, pk=pk)
    tracker.delete()
    messages.success(request, 'Tracker excluido.')
    return redirect('tracker_list')


@login_required
def tracker_detail(request, pk):
    tracker = get_object_or_404(PerformanceTracker.objects.prefetch_related('logs', 'reviewers'), pk=pk)
    form = TrackerLogForm()
    if request.method == 'POST':
        form = TrackerLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.tracker = tracker
            log.reviewer = getattr(request.user, 'employee', None)
            log.save()
            messages.success(request, 'Log adicionado!')
            return redirect('tracker_detail', pk=pk)
    return render(request, 'performance/tracker_detail.html', {'tracker': tracker, 'form': form})


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer
from .models import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer
from buzz.models import BuzzPost
from admin_app.models import LegalEntity, Subunit, City

@login_required
@require_module('performance')
def survey_list(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
    surveys = Survey.objects.all()
    return render(request, 'performance/survey_list.html', {'surveys': surveys})

@login_required
@require_module('performance')
@csrf_exempt
def survey_create(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Acesso negado'}, status=403)
        return redirect('dashboard')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            survey = Survey.objects.create(
                title=data.get('title'),
                description=data.get('description'),
                is_anonymous=data.get('is_anonymous', False),
                is_leadership_survey=data.get('is_leadership_survey', False),
                target_type=data.get('target_type', 'ALL'),
                created_by=request.user,
                end_date=data.get('end_date') or None
            )
            
            
            if survey.target_type == 'LEGAL_ENTITY':
                survey.target_legal_entity_id = data.get('legal_entity_id')
            elif survey.target_type == 'SUBUNIT':
                survey.target_subunit_id = data.get('subunit_id')
            elif survey.target_type == 'CITY':
                survey.target_city_id = data.get('city_id')
            survey.save()

            
            questions = data.get('questions', [])
            for i, q in enumerate(questions):
                SurveyQuestion.objects.create(
                    survey=survey,
                    question_text=q.get('question_text'),
                    question_type=q.get('question_type'),
                    choices=q.get('choices', ''),
                    is_required=q.get('is_required', True),
                    order=i
                )
            
            
            status = data.get('status', 'DRAFT')
            if status == 'PUBLISHED':
                survey.status = 'PUBLISHED'
                survey.save()
                if hasattr(request.user, 'employee') and request.user.employee:
                    BuzzPost.objects.create(
                        employee=request.user.employee,
                        text=f"📢 O RH acabou de lançar uma nova pesquisa: **{survey.title}**.\nAcesse o seu painel para responder!"
                    )
                
            return JsonResponse({'success': True, 'survey_id': survey.pk})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
            
    
    legal_entities = LegalEntity.objects.all()
    subunits = Subunit.objects.all()
    cities = City.objects.all()
    return render(request, 'performance/survey_builder.html', {'legal_entities': legal_entities, 'subunits': subunits, 'cities': cities})

@login_required
@require_module('performance')
@csrf_exempt
def survey_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        return redirect('dashboard')
    survey = get_object_or_404(Survey, pk=pk)
    
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                survey.title = data.get('title')
                survey.description = data.get('description')
                survey.is_anonymous = data.get('is_anonymous', False)
                survey.is_leadership_survey = data.get('is_leadership_survey', False)
                survey.target_type = data.get('target_type', 'ALL')
                survey.end_date = data.get('end_date') or None
                
                survey.target_legal_entity_id = None
                survey.target_subunit_id = None
                survey.target_city_id = None
                
                if survey.target_type == 'LEGAL_ENTITY':
                    survey.target_legal_entity_id = data.get('legal_entity_id')
                elif survey.target_type == 'SUBUNIT':
                    survey.target_subunit_id = data.get('subunit_id')
                elif survey.target_type == 'CITY':
                    survey.target_city_id = data.get('city_id')
                
                status = data.get('status', 'DRAFT')
                if status == 'PUBLISHED':
                    survey.status = 'PUBLISHED'
                    if hasattr(request.user, 'employee') and request.user.employee:
                        BuzzPost.objects.create(
                            employee=request.user.employee,
                            text=f"📢 O RH acabou de lançar uma nova pesquisa: **{survey.title}**.\nAcesse o seu painel para responder!"
                        )
                survey.save()
                
                
                survey.questions.all().delete()
                questions = data.get('questions', [])
                for i, q in enumerate(questions):
                    SurveyQuestion.objects.create(
                        survey=survey,
                        question_text=q.get('question_text'),
                        question_type=q.get('question_type'),
                        choices=q.get('choices', ''),
                        is_required=q.get('is_required', True),
                        order=i
                    )
                return JsonResponse({'success': True, 'survey_id': survey.pk})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
                
        action = request.POST.get('action')
        if action == 'publish' and survey.status != 'PUBLISHED':
            survey.status = 'PUBLISHED'
            survey.save()
            if hasattr(request.user, 'employee') and request.user.employee:
                BuzzPost.objects.create(
                    employee=request.user.employee,
                    text=f"📢 O RH lançou uma pesquisa: **{survey.title}**.\nAcesse seu painel!"
                )
            messages.success(request, 'Pesquisa Publicada com sucesso!')
        elif action == 'close':
            survey.status = 'CLOSED'
            survey.save()
            messages.success(request, 'Pesquisa Encerrada.')
            
        return redirect('survey_list')

    
    survey_data = {
        'id': survey.id,
        'title': survey.title,
        'description': survey.description or '',
        'is_anonymous': survey.is_anonymous,
        'is_leadership_survey': survey.is_leadership_survey,
        'target_type': survey.target_type,
        'legal_entity_id': survey.target_legal_entity_id,
        'subunit_id': survey.target_subunit_id,
        'city_id': survey.target_city_id,
        'end_date': survey.end_date.strftime('%Y-%m-%dT%H:%M') if survey.end_date else '',
        'questions': [
            {
                'text': q.question_text,
                'type': q.question_type,
                'choices': q.choices or ''
            } for q in survey.questions.all()
        ]
    }
    
    legal_entities = LegalEntity.objects.all()
    subunits = Subunit.objects.all()
    cities = City.objects.all()
    return render(request, 'performance/survey_builder.html', {
        'legal_entities': legal_entities, 
        'subunits': subunits, 
        'cities': cities,
        'survey_data': json.dumps(survey_data)
    })

@login_required
@require_module('performance')
def survey_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        return redirect('dashboard')
    survey = get_object_or_404(Survey, pk=pk)
    survey.delete()
    messages.success(request, 'Pesquisa Excluída.')
    return redirect('survey_list')

@login_required
@require_module('performance')
def survey_results(request, pk):
    if not (request.user.is_admin() or request.user.is_hr() or request.user.is_supervisor()):
        return redirect('dashboard')
    survey = get_object_or_404(Survey.objects.prefetch_related('questions', 'responses__answers'), pk=pk)
    
    sector_id = request.GET.get('sector')
    current_sector_id = None
    if sector_id and sector_id.isdigit():
        current_sector_id = int(sector_id)
        
    is_supervisor_viewer = request.user.is_supervisor() and not (request.user.is_admin() or request.user.is_hr())
        
    from pim.models import Employee
    qs = Employee.objects.filter(state=Employee.STATE_ACTIVE)
    if survey.target_type == 'LEGAL_ENTITY' and survey.target_legal_entity_id:
        qs = qs.filter(legal_entity_id=survey.target_legal_entity_id)
    elif survey.target_type == 'SUBUNIT' and survey.target_subunit_id:
        qs = qs.filter(sub_division_id=survey.target_subunit_id)
        
    if current_sector_id:
        qs = qs.filter(sub_division_id=current_sector_id)
        
    if is_supervisor_viewer:
        qs = qs.exclude(sub_division__name='DESENVOLVEDOR(A)')
        
    total_target = qs.count()
    
    responses_qs = survey.responses.all()
    if current_sector_id:
        responses_qs = responses_qs.filter(department_id=current_sector_id)
        
    if is_supervisor_viewer:
        responses_qs = responses_qs.exclude(evaluated_leader__first_name='NIULANIO', evaluated_leader__last_name='NIULANIO')
        responses_qs = responses_qs.exclude(department__name='DESENVOLVEDOR(A)')
        
    responses_count = responses_qs.count()
    
    leader_stats = {}
    if survey.is_leadership_survey:
        responses = responses_qs.select_related('employee', 'evaluated_leader', 'department').prefetch_related('answers__question')
        for r in responses:
            leader = r.evaluated_leader
            dept = r.department
            leader_key = str(leader.id) if leader else 'no_leader'
            leader_name = leader.full_name if leader else 'Sem Líder'
            dept_name = dept.name if dept else 'Sem Setor'
            
            if leader_key not in leader_stats:
                leader_stats[leader_key] = {
                    'leader_name': leader_name,
                    'dept_name': dept_name,
                    'subunit_id': str(dept.id) if dept else 'none',
                    'response_count': 0,
                    'questions': {}
                }
            
            leader_stats[leader_key]['response_count'] += 1
            
            for ans in r.answers.all():
                q = ans.question
                q_id = str(q.id)
                if q_id not in leader_stats[leader_key]['questions']:
                    leader_stats[leader_key]['questions'][q_id] = {
                        'question_text': q.question_text,
                        'question_type': q.question_type,
                        'total_score': 0,
                        'rating_count': 0,
                        'choice_counts': {},
                        'text_answers': []
                    }
                
                q_stat = leader_stats[leader_key]['questions'][q_id]
                if q.question_type == 'RATING_10' and ans.rating_answer is not None:
                    q_stat['total_score'] += ans.rating_answer
                    q_stat['rating_count'] += 1
                elif q.question_type in ['GOOD_BAD', 'MULTIPLE_CHOICE'] and ans.choice_answer:
                    choice = ans.choice_answer
                    q_stat['choice_counts'][choice] = q_stat['choice_counts'].get(choice, 0) + 1
                elif q.question_type == 'TEXT' and ans.text_answer:
                    q_stat['text_answers'].append({
                        'text': ans.text_answer,
                        'employee_name': r.employee.full_name if not survey.is_anonymous and r.employee else None,
                        'dept_name': dept_name if not survey.is_anonymous else None,
                    })
                    
        # First pass: calculate global survey average score C
        total_survey_score = 0
        total_survey_count = 0
        leader_raw_scores = {}
        
        for l_key, stats in leader_stats.items():
            leader_total_score = 0
            leader_score_count = 0
            
            for q_id, q_stat in stats['questions'].items():
                if q_stat['rating_count'] > 0:
                    leader_total_score += q_stat['total_score']
                    leader_score_count += q_stat['rating_count']
                
                if q_stat['question_type'] == 'GOOD_BAD':
                    gb_total = 0
                    gb_count = 0
                    for choice, count in q_stat['choice_counts'].items():
                        if choice == 'Bom':
                            gb_total += 10.0 * count
                        elif choice == 'Regular':
                            gb_total += 5.0 * count
                        elif choice == 'Ruim':
                            gb_total += 0.0 * count
                        gb_count += count
                    if gb_count > 0:
                        leader_total_score += gb_total
                        leader_score_count += gb_count
            
            leader_raw_scores[l_key] = (leader_total_score, leader_score_count)
            total_survey_score += leader_total_score
            total_survey_count += leader_score_count
            
        C = total_survey_score / total_survey_count if total_survey_count > 0 else 8.0
        
        # Second pass: calculate team size, adhesion rate, and apply Bayesian adjusted overall score
        for l_key, stats in leader_stats.items():
            leader_total_score, leader_score_count = leader_raw_scores.get(l_key, (0, 0))
            
            # Team size of active subordinates (excluding the leader)
            from pim.models import Employee
            if l_key != 'no_leader':
                leader_id = int(l_key)
                leader_emp = Employee.objects.filter(id=leader_id).first()
                if leader_emp and leader_emp.sub_division:
                    team_size = Employee.objects.filter(sub_division=leader_emp.sub_division, state=Employee.STATE_ACTIVE).exclude(id=leader_id).count()
                else:
                    team_size = 0
            else:
                team_size = 0
                
            stats['team_size'] = max(team_size, stats['response_count'])
            stats['adhesion_pct'] = int((stats['response_count'] / stats['team_size']) * 100) if stats['team_size'] > 0 else 0
            
            # Set averages for questions
            for q_id, q_stat in stats['questions'].items():
                if q_stat['rating_count'] > 0:
                    q_stat['average'] = round(q_stat['total_score'] / q_stat['rating_count'], 2)
                else:
                    q_stat['average'] = None
            
            if leader_score_count > 0:
                v = leader_score_count
                R = leader_total_score / v
                weighted_score = (v * R + 2.0 * C) / (v + 2.0)
                stats['overall_score'] = round(weighted_score, 1)
            else:
                stats['overall_score'] = None
                
            stats['history'] = []
            if l_key != 'no_leader':
                leader_id = int(l_key)
                history_surveys = Survey.objects.filter(is_leadership_survey=True).exclude(status='DRAFT').prefetch_related('responses__answers__question').order_by('created_at')
                for hs in history_surveys:
                    hs_all_resps = hs.responses.all().prefetch_related('answers__question')
                    if is_supervisor_viewer:
                        hs_all_resps = hs_all_resps.exclude(evaluated_leader__first_name='NIULANIO', evaluated_leader__last_name='NIULANIO')
                        hs_all_resps = hs_all_resps.exclude(department__name='DESENVOLVEDOR(A)')
                    
                    comp_total = 0
                    comp_count = 0
                    leader_total = 0
                    leader_count = 0
                    
                    for r in hs_all_resps:
                        r_total = 0
                        r_count = 0
                        for ans in r.answers.all():
                            q = ans.question
                            if q.question_type == 'RATING_10' and ans.rating_answer is not None:
                                r_total += ans.rating_answer
                                r_count += 1
                            elif q.question_type == 'GOOD_BAD' and ans.choice_answer:
                                if ans.choice_answer == 'Bom':
                                    r_total += 10.0
                                elif ans.choice_answer == 'Regular':
                                    r_total += 5.0
                                elif ans.choice_answer == 'Ruim':
                                    r_total += 0.0
                                r_count += 1
                        
                        comp_total += r_total
                        comp_count += r_count
                        
                        if r.evaluated_leader_id == leader_id:
                            leader_total += r_total
                            leader_count += r_count
                            
                    C_hs = comp_total / comp_count if comp_count > 0 else 8.0
                    
                    if leader_count > 0:
                        v = leader_count
                        R = leader_total / v
                        weighted_score = (v * R + 2.0 * C_hs) / (v + 2.0)
                        hs_val = round(weighted_score, 1)
                        stats['history'].append({
                            'survey_title': hs.title,
                            'date': hs.created_at.strftime('%m/%Y'),
                            'score': hs_val
                        })

    # Calculate statistics per question
    question_stats = {}
    for q in survey.questions.all():
        question_stats[str(q.id)] = {
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'total_responses': 0,
            'average_rating': 0,
            'rating_count': 0,
            'rating_distribution': {i: 0 for i in range(1, 11)},
            'choices_distribution': {},
            'text_answers': [],
            'dept_averages': {}
        }
        
    for resp in responses_qs.select_related('employee', 'evaluated_leader', 'department').prefetch_related('answers'):
        dept_id = str(resp.department.id) if resp.department else None
        dept_name = resp.department.name if resp.department else 'Sem Setor'
        
        for ans in resp.answers.all():
            q_id = str(ans.question_id)
            if q_id not in question_stats:
                continue
                
            q_stat = question_stats[q_id]
            q_stat['total_responses'] += 1
            
            if q_stat['question_type'] == 'RATING_10' and ans.rating_answer is not None:
                q_stat['rating_distribution'][ans.rating_answer] += 1
                q_stat['rating_count'] += 1
                
                if dept_id:
                    if dept_id not in q_stat['dept_averages']:
                        q_stat['dept_averages'][dept_id] = {'name': dept_name, 'total': 0, 'count': 0}
                    q_stat['dept_averages'][dept_id]['total'] += ans.rating_answer
                    q_stat['dept_averages'][dept_id]['count'] += 1
                    
            elif q_stat['question_type'] in ['GOOD_BAD', 'MULTIPLE_CHOICE'] and ans.choice_answer:
                choice = ans.choice_answer
                q_stat['choices_distribution'][choice] = q_stat['choices_distribution'].get(choice, 0) + 1
            elif q_stat['question_type'] == 'TEXT' and ans.text_answer:
                q_stat['text_answers'].append({
                    'text': ans.text_answer,
                    'employee_name': resp.employee.full_name if not survey.is_anonymous and resp.employee else None,
                    'dept_name': dept_name if not survey.is_anonymous else None,
                    'leader_name': resp.evaluated_leader.full_name if resp.evaluated_leader else None,
                })
                
    for q_id, q_stat in question_stats.items():
        if q_stat['rating_count'] > 0:
            total_sum = sum(rating * count for rating, count in q_stat['rating_distribution'].items())
            q_stat['average_rating'] = round(total_sum / q_stat['rating_count'], 2)
        else:
            q_stat['average_rating'] = None
            
        for dept_id, da in q_stat['dept_averages'].items():
            da['average'] = round(da['total'] / da['count'], 2)

    subunits_in_responses = []
    seen_subunits = set()
    for resp in survey.responses.all().select_related('department'):
        if resp.department and resp.department.id not in seen_subunits:
            seen_subunits.add(resp.department.id)
            subunits_in_responses.append({
                'id': resp.department.id,
                'name': resp.department.name
            })
            
    ranked_leaders = []
    if survey.is_leadership_survey:
        ranked_leaders = list(leader_stats.values())
        ranked_leaders.sort(
            key=lambda x: x['overall_score'] if x['overall_score'] is not None else -1,
            reverse=True
        )

    all_surveys = Survey.objects.exclude(status='DRAFT').order_by('-created_at')

    return render(request, 'performance/survey_results.html', {
        'survey': survey, 
        'all_surveys': all_surveys,
        'responses': responses_qs,
        'responses_count': responses_count,
        'total_target': total_target,
        'pending_count': max(0, total_target - responses_count),
        'leader_stats': leader_stats,
        'ranked_leaders': ranked_leaders,
        'question_stats': question_stats,
        'subunits_in_responses': subunits_in_responses,
        'current_sector_id': current_sector_id
    })

@login_required
def survey_take(request, pk):
    survey = get_object_or_404(Survey, pk=pk, status='PUBLISHED')
    emp = getattr(request.user, 'employee', None)
    if not emp:
        messages.error(request, 'Perfil de funcionário não encontrado.')
        return redirect('dashboard')
        
    from django.utils import timezone
    if survey.end_date and survey.end_date < timezone.now():
        messages.error(request, 'O prazo para responder esta pesquisa já encerrou.')
        return redirect('dashboard')
        
    if SurveyResponse.objects.filter(survey=survey, employee=emp).exists():
        messages.info(request, 'Você já respondeu esta pesquisa. Obrigado!')
        return redirect('dashboard')
        
    dept = emp.sub_division
    leader = emp.supervisors.first()
    if not leader and dept:
        leader = dept.supervisor
        
    if survey.is_leadership_survey and leader == emp:
        messages.warning(request, 'Você é o líder avaliado nesta pesquisa para o seu setor, portanto não precisa respondê-la.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        resp = SurveyResponse.objects.create(
            survey=survey, 
            employee=emp,
            evaluated_leader=leader if survey.is_leadership_survey else None,
            department=dept if survey.is_leadership_survey else None
        )
        
        for q in survey.questions.all():
            key = f"question_{q.id}"
            val = request.POST.get(key, '')
            
            ans = SurveyAnswer(response=resp, question=q)
            if q.question_type == 'TEXT':
                ans.text_answer = val
            elif q.question_type == 'RATING_10':
                ans.rating_answer = int(val) if val.isdigit() else None
            elif q.question_type in ['GOOD_BAD', 'MULTIPLE_CHOICE']:
                ans.choice_answer = val
            ans.save()
            
        messages.success(request, 'Pesquisa enviada com sucesso!')
        return redirect('dashboard')
        
    return render(request, 'performance/survey_take.html', {
        'survey': survey,
        'leader': leader,
        'department': dept
    })


@login_required
@require_module('performance')
def survey_ranking_list(request):
    if not (request.user.is_admin() or request.user.is_hr() or request.user.is_supervisor()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
        
    surveys = Survey.objects.filter(is_leadership_survey=True).exclude(status='DRAFT').order_by('-created_at')

    # Sempre agrega TODAS as pesquisas — média geral
    from .models import SurveyResponse
    responses = SurveyResponse.objects.filter(survey__in=surveys).select_related('evaluated_leader', 'department').prefetch_related('answers__question')

    is_supervisor_viewer = request.user.is_supervisor() and not (request.user.is_admin() or request.user.is_hr())
    if is_supervisor_viewer:
        responses = responses.exclude(evaluated_leader__first_name='NIULANIO', evaluated_leader__last_name='NIULANIO')
        responses = responses.exclude(department__name='DESENVOLVEDOR(A)')

    leader_stats = {}
    for r in responses:
        leader = r.evaluated_leader
        dept = r.department
        if not leader:
            continue
        leader_key = str(leader.id)
        if leader_key not in leader_stats:
            leader_stats[leader_key] = {
                'leader_name': leader.full_name,
                'dept_name': dept.name if dept else 'Sem Setor',
                'response_count': 0,
                'total_score': 0,
                'score_count': 0,
                'survey_id': r.survey_id,
            }
        leader_stats[leader_key]['response_count'] += 1
        for ans in r.answers.all():
            q = ans.question
            if q.question_type == 'RATING_10' and ans.rating_answer is not None:
                leader_stats[leader_key]['total_score'] += ans.rating_answer
                leader_stats[leader_key]['score_count'] += 1
            elif q.question_type == 'GOOD_BAD' and ans.choice_answer:
                if ans.choice_answer == 'Bom':
                    leader_stats[leader_key]['total_score'] += 10.0
                elif ans.choice_answer == 'Regular':
                    leader_stats[leader_key]['total_score'] += 5.0
                leader_stats[leader_key]['score_count'] += 1

    # Média global da empresa (para Bayesian smoothing)
    total_company_score = sum(s['total_score'] for s in leader_stats.values())
    total_company_count = sum(s['score_count'] for s in leader_stats.values())
    C = total_company_score / total_company_count if total_company_count > 0 else 8.0

    ranked_leaders = []
    for l_key, stats in leader_stats.items():
        leader_id = int(l_key)
        from pim.models import Employee
        leader_emp = Employee.objects.filter(id=leader_id).first()
        if leader_emp and leader_emp.sub_division:
            team_size = Employee.objects.filter(sub_division=leader_emp.sub_division, state=Employee.STATE_ACTIVE).exclude(id=leader_id).count()
        else:
            team_size = 0
        stats['team_size'] = max(team_size, stats['response_count'])
        stats['adhesion_pct'] = int((stats['response_count'] / stats['team_size']) * 100) if stats['team_size'] > 0 else 0
        if stats['score_count'] > 0:
            v = stats['score_count']
            R = stats['total_score'] / v
            stats['overall_score'] = round((v * R + 2.0 * C) / (v + 2.0), 1)
        else:
            stats['overall_score'] = None
        ranked_leaders.append(stats)

    ranked_leaders.sort(key=lambda x: x['overall_score'] if x['overall_score'] is not None else -1, reverse=True)

    return render(request, 'performance/survey_ranking_list.html', {
        'ranked_leaders': ranked_leaders,
        'total_surveys': surveys.count(),
    })

