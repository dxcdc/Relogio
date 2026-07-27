from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import BuzzPost, BuzzShare, BuzzPhoto, BuzzLikeOnShare, BuzzComment, BuzzLikeOnComment
from .models import ChangelogPost, BugReport, BugReportComment, BugReportScreenshot, ContentReport
from .forms import ChangelogPostForm, BugReportForm, BugReportCommentForm, BugStatusForm




@login_required
def buzz_feed(request):
    emp = getattr(request.user, 'employee', None)
    if getattr(request.user, 'is_netgram_suspended', False):
        return render(request, 'buzz/feed.html', {'emp': emp, 'my_employee': emp})
    feed_filter = request.GET.get('filter', 'all')
    
    # Retrieve blocked user IDs
    all_blocked_ids = set()
    if request.user.is_authenticated:
        blocked_by_me = list(request.user.blocked_users.values_list('id', flat=True))
        blocked_me = list(request.user.blocked_by_users.values_list('id', flat=True))
        all_blocked_ids = set(blocked_by_me + blocked_me)
        
    from django.db.models import Prefetch
    # Filter comments to exclude those by blocked users
    comments_qs = BuzzComment.objects.select_related('employee__user')
    if all_blocked_ids:
        comments_qs = comments_qs.exclude(employee__user__id__in=all_blocked_ids)
        
    shares = BuzzShare.objects.select_related('post__employee', 'employee').prefetch_related(
        'post__photos', 
        'likes', 
        Prefetch('comments', queryset=comments_qs)
    ).order_by('-created_at')
    
    if all_blocked_ids:
        shares = shares.exclude(employee__user__id__in=all_blocked_ids)
        shares = shares.exclude(post__employee__user__id__in=all_blocked_ids)
    
    if feed_filter == 'rh':
        shares = shares.filter(post__text__icontains="COMUNICADO OFICIAL")
    elif feed_filter == 'birthdays':
        shares = shares.filter(post__text__icontains="aniversário")
        
    user_liked = []
    if emp:
        user_liked = list(BuzzLikeOnShare.objects.filter(employee=emp).values_list('share_id', flat=True))
        
    can_post = True
    if getattr(request.user, 'role', None):
        from core.models import RoleModuleAccess
        acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
        if acc:
            can_post = acc.netgram_post
            
    return render(request, 'buzz/feed.html', {'shares': shares, 'emp': emp, 'my_employee': emp, 'user_liked': user_liked, 'can_post_netgram': can_post})


@login_required
def create_post(request):
    if getattr(request.user, 'is_netgram_suspended', False):
        messages.error(request, 'Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso.')
        return redirect('dashboard')
        
    emp = getattr(request.user, 'employee', None)
    if not emp:
        return redirect('buzz_feed')
        
    if getattr(request.user, 'role', None):
        from core.models import RoleModuleAccess
        acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
        if acc and not acc.netgram_post:
            messages.error(request, 'Você não tem permissão para publicar no Netgram.')
            return redirect('buzz_feed')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            post = BuzzPost.objects.create(text=text, employee=emp)
            share = BuzzShare.objects.create(post=post, employee=emp, type='post', text=text)
            photos = request.FILES.getlist('photos')
            for photo in photos:
                BuzzPhoto.objects.create(post=post, photo=photo)
                
            from core.push_notifications import send_push_to_users
            from core.models import OrangeUser
            import threading
            
            users = OrangeUser.objects.filter(is_active=True).exclude(id=request.user.id)
            if users.exists():
                users_list = list(users)
                threading.Thread(
                    target=send_push_to_users,
                    args=(users_list, "Novo post no Netgram!", f"{emp.first_name} publicou algo novo. Vem conferir!", {'route': '/buzz'}),
                    daemon=True
                ).start()
    return redirect('buzz_feed')


@login_required
def like_share(request, pk):
    if getattr(request.user, 'is_netgram_suspended', False):
        return JsonResponse({'error': 'Seu acesso ao Netgram foi suspenso.'}, status=403)
        
    emp = getattr(request.user, 'employee', None)
    if not emp:
        return JsonResponse({'error': 'no employee'}, status=400)
    share = get_object_or_404(BuzzShare, pk=pk)
    like, created = BuzzLikeOnShare.objects.get_or_create(share=share, employee=emp)
    if not created:
        like.delete()
        share.num_of_likes = max(0, share.num_of_likes - 1)
    else:
        share.num_of_likes += 1
        
        owner_user = getattr(share.employee, 'user', None)
        if owner_user and owner_user.id != request.user.id:
            from core.push_notifications import send_push
            import threading
            threading.Thread(
                target=send_push,
                args=(owner_user, "Alguém curtiu seu post", f"{emp.first_name} curtiu sua postagem no Netgram.", {'route': '/buzz'}),
                daemon=True
            ).start()
            
    share.save()
    return JsonResponse({'likes': share.num_of_likes})


@login_required
def add_comment(request, share_pk):
    if getattr(request.user, 'is_netgram_suspended', False):
        messages.error(request, 'Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso.')
        return redirect('dashboard')
        
    emp = getattr(request.user, 'employee', None)
    if not emp or request.method != 'POST':
        return redirect('buzz_feed')
    share = get_object_or_404(BuzzShare, pk=share_pk)
    text = request.POST.get('text', '').strip()
    if text:
        BuzzComment.objects.create(share=share, employee=emp, text=text)
        share.num_of_comments += 1
        share.save()
        
        owner_user = getattr(share.employee, 'user', None)
        if owner_user and owner_user.id != request.user.id:
            from core.push_notifications import send_push
            import threading
            threading.Thread(
                target=send_push,
                args=(owner_user, "Novo comentário!", f"{emp.first_name} comentou: {text[:30]}", {'route': '/buzz'}),
                daemon=True
            ).start()
            
    return redirect('buzz_feed')


@login_required
def delete_post(request, share_pk):
    emp = getattr(request.user, 'employee', None)
    share = get_object_or_404(BuzzShare, pk=share_pk)
    if emp and (share.employee == emp or request.user.is_admin()):
        share.post.delete()
    return redirect('buzz_feed')




@login_required
def changelog_list(request):
    """Lista de notas de atualização — visível para todos os funcionários."""
    posts = ChangelogPost.objects.all()
    
    my_open_bugs = BugReport.objects.filter(
        reported_by=request.user,
        status__in=[BugReport.STATUS_OPEN, BugReport.STATUS_ANALYZING]
    ).count()
    
    all_open_bugs = 0
    if request.user.is_admin() or request.user.is_hr():
        all_open_bugs = BugReport.objects.filter(
            status__in=[BugReport.STATUS_OPEN, BugReport.STATUS_ANALYZING]
        ).count()
    return render(request, 'buzz/changelog_list.html', {
        'posts': posts,
        'my_open_bugs': my_open_bugs,
        'all_open_bugs': all_open_bugs,
    })


@login_required
def changelog_create(request):
    """Publicar nova nota de atualização — apenas Admin/HR."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Apenas administradores podem publicar atualizacoes.')
        return redirect('changelog_list')
    if request.method == 'POST':
        form = ChangelogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Nota de atualizacao publicada com sucesso!')
            return redirect('changelog_list')
    else:
        form = ChangelogPostForm()
    return render(request, 'buzz/changelog_form.html', {'form': form, 'title': 'Nova Atualizacao'})


@login_required
def changelog_delete(request, pk):
    """Deletar nota de atualização — apenas Admin."""
    if not request.user.is_admin():
        messages.error(request, 'Apenas administradores podem deletar notas.')
        return redirect('changelog_list')
    post = get_object_or_404(ChangelogPost, pk=pk)
    post.delete()
    messages.success(request, 'Nota removida.')
    return redirect('changelog_list')


@login_required
def bug_list(request):
    """Lista de bugs — Admin vê todos, funcionário vê só os seus."""
    is_admin_or_hr = request.user.is_admin() or request.user.is_hr()
    status_filter = request.GET.get('status', '')

    if is_admin_or_hr:
        bugs = BugReport.objects.select_related('reported_by').all()
    else:
        bugs = BugReport.objects.filter(reported_by=request.user)

    if status_filter:
        bugs = bugs.filter(status=status_filter)

    status_counts = {}
    base_qs = BugReport.objects.all() if is_admin_or_hr else BugReport.objects.filter(reported_by=request.user)
    for s, _ in BugReport.STATUS_CHOICES:
        status_counts[s] = base_qs.filter(status=s).count()

    return render(request, 'buzz/bug_list.html', {
        'bugs': bugs,
        'is_admin_or_hr': is_admin_or_hr,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'STATUS_CHOICES': BugReport.STATUS_CHOICES,
    })


@login_required
def bug_create(request):
    """Qualquer funcionário pode abrir um bug report."""
    if request.method == 'POST':
        form = BugReportForm(request.POST, request.FILES)
        if form.is_valid():
            bug = form.save(commit=False)
            bug.reported_by = request.user
            bug.save()
            
            for img in request.FILES.getlist('screenshots'):
                BugReportScreenshot.objects.create(bug_report=bug, image=img)
            messages.success(request, 'Seu relato foi enviado! Nossa equipe vai analisar em breve.')
            return redirect('bug_detail', pk=bug.pk)
        
        messages.error(request, 'Preencha todos os campos obrigatórios.')
        return redirect('bug_list')
    return redirect('bug_list')


@login_required
def bug_detail(request, pk):
    """Detalhe do bug + thread de comentários."""
    is_admin_or_hr = request.user.is_admin() or request.user.is_hr()
    if is_admin_or_hr:
        bug = get_object_or_404(BugReport, pk=pk)
    else:
        bug = get_object_or_404(BugReport, pk=pk, reported_by=request.user)

    
    comments = bug.comments.all()
    if not is_admin_or_hr:
        comments = comments.filter(is_internal=False)

    screenshots = bug.screenshots.all()
    comment_form = BugReportCommentForm()
    status_form = BugStatusForm(instance=bug) if is_admin_or_hr else None

    return render(request, 'buzz/bug_detail.html', {
        'bug': bug,
        'comments': comments,
        'screenshots': screenshots,
        'comment_form': comment_form,
        'status_form': status_form,
        'is_admin_or_hr': is_admin_or_hr,
    })


@login_required
def bug_comment_add(request, pk):
    """Adicionar comentário a um bug — Admin responde, usuário também pode comentar."""
    is_admin_or_hr = request.user.is_admin() or request.user.is_hr()
    if is_admin_or_hr:
        bug = get_object_or_404(BugReport, pk=pk)
    else:
        bug = get_object_or_404(BugReport, pk=pk, reported_by=request.user)

    if request.method == 'POST':
        form = BugReportCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.bug_report = bug
            comment.author = request.user
            
            if not is_admin_or_hr:
                comment.is_internal = False
            comment.save()
            
            if is_admin_or_hr and not comment.is_internal and bug.reported_by != request.user:
                from core.push_notifications import send_push
                import threading
                threading.Thread(
                    target=send_push,
                    args=(bug.reported_by, "Suporte Respondeu!", f"Um analista respondeu seu chamado: {bug.title}", {'route': '/my-reports'}),
                    daemon=True
                ).start()
                
            messages.success(request, 'Comentario adicionado.')
    return redirect('bug_detail', pk=pk)


@login_required
def bug_status_update(request, pk):
    """Atualizar status e prioridade de um bug — apenas Admin/HR."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Sem permissao.')
        return redirect('bug_list')
    bug = get_object_or_404(BugReport, pk=pk)
    if request.method == 'POST':
        form = BugStatusForm(request.POST, instance=bug)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status == BugReport.STATUS_RESOLVED and not bug.resolved_at:
                updated.resolved_at = timezone.now()
            updated.save()
            messages.success(request, f'Status atualizado para: {bug.get_status_display()}')
    return redirect('bug_detail', pk=pk)


@login_required
def bug_claim(request, pk):
    """Permite Admin/HR assumir ou liberar a responsabilidade de um bug report."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Sem permissao.')
        return redirect('bug_list')
    bug = get_object_or_404(BugReport, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'claim':
            bug.assigned_to = request.user
            
            if bug.status == BugReport.STATUS_OPEN:
                bug.status = BugReport.STATUS_ANALYZING
            bug.save()
            messages.success(request, f'Você assumiu este reporte. Status atualizado para Em análise.')
        elif action == 'release':
            bug.assigned_to = None
            bug.save()
            messages.info(request, 'Responsabilidade liberada.')
    return redirect('bug_detail', pk=pk)


@login_required
def content_reports(request):
    """Painel de moderação de denúncias do Netgram — apenas Admin/HR."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('buzz_feed')

    status_filter = request.GET.get('status', '')
    type_filter   = request.GET.get('type', '')

    qs = ContentReport.objects.select_related('reported_by').all()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(content_type=type_filter)

    all_reports = ContentReport.objects.select_related('reported_by').all()

    # Busca o conteúdo real de cada denúncia para exibir no modal
    from .models import BuzzShare, BuzzComment
    reports_with_content = []
    for r in all_reports:
        content_text = None
        content_author = None
        content_date = None
        content_deleted = False
        try:
            if r.content_type == 'post':
                obj = BuzzShare.objects.select_related('employee').get(pk=r.content_id)
                content_text = obj.text or '[Sem texto — apenas mídia]'
                content_author = str(obj.employee)
                content_date = obj.created_at.strftime('%d/%m/%Y %H:%M')
            else:
                obj = BuzzComment.objects.select_related('employee').get(pk=r.content_id)
                content_text = obj.text
                content_author = str(obj.employee)
                content_date = obj.created_at.strftime('%d/%m/%Y %H:%M')
        except Exception:
            content_deleted = True
            content_text = '[Conteúdo já removido]'

        reports_with_content.append({
            'id': r.id,
            'content_type': r.content_type,
            'content_id': r.content_id,
            'reason': r.reason,
            'reporter': f'{r.reported_by.first_name} {r.reported_by.last_name}',
            'reporter_email': getattr(r.reported_by, 'work_email', '-') or '-',
            'status': r.status,
            'note': r.moderator_note or '',
            'created_at': r.created_at.strftime('%d/%m/%Y %H:%M'),
            'resolved_at': r.resolved_at.strftime('%d/%m/%Y %H:%M') if r.resolved_at else '-',
            'content_text': content_text,
            'content_author': content_author,
            'content_date': content_date,
            'content_deleted': content_deleted,
        })

    return render(request, 'buzz/content_reports.html', {
        'reports':              qs,
        'all_reports':          all_reports,
        'reports_with_content': reports_with_content,
        'status_filter':        status_filter,
        'type_filter':          type_filter,
        'count_pending':    ContentReport.objects.filter(status='PENDING').count(),
        'count_reviewing':  ContentReport.objects.filter(status='REVIEWING').count(),
        'count_resolved':   ContentReport.objects.filter(status='RESOLVED').count(),
        'count_dismissed':  ContentReport.objects.filter(status='DISMISSED').count(),
    })


@login_required
def update_content_report(request, pk):
    """Atualiza status e nota de moderador de uma denúncia — apenas Admin/HR."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('buzz_feed')

    report = get_object_or_404(ContentReport, pk=pk)
    if request.method == 'POST':
        new_status     = request.POST.get('new_status', '').strip()
        moderator_note = request.POST.get('moderator_note', '').strip()

        valid_statuses = [s for s, _ in ContentReport.STATUS_CHOICES]
        if new_status in valid_statuses:
            report.status = new_status
            if new_status in ('RESOLVED', 'DISMISSED') and not report.resolved_at:
                report.resolved_at = timezone.now()
        if moderator_note:
            report.moderator_note = moderator_note
        report.save()
        
        # Envia email de notificação
        try:
            send_content_report_email(report)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Falha ao enviar email de status da denuncia: {e}")
            
        messages.success(request, f'Denúncia #{pk} atualizada para: {report.get_status_display()}')
        
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
    return redirect('content_reports')


@login_required
def central_suporte(request):
    """Central de Suporte — Bugs do Sistema + Denúncias do Netgram. Apenas Admin/HR."""
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('buzz_feed')

    active_tab = request.GET.get('tab', 'bugs')

    # ── TAB 1: Bugs do Sistema ──────────────────────────────────────
    bug_status = request.GET.get('bug_status', '')
    bugs_qs = BugReport.objects.select_related('reported_by', 'assigned_to').prefetch_related('screenshots').all()
    if bug_status:
        bugs_qs = bugs_qs.filter(status=bug_status)
    bug_counts = {
        'open':      BugReport.objects.filter(status='OPEN').count(),
        'analyzing': BugReport.objects.filter(status='ANALYZING').count(),
        'resolved':  BugReport.objects.filter(status='RESOLVED').count(),
        'wontfix':   BugReport.objects.filter(status='WONTFIX').count(),
    }

    # ── TAB 2: Denúncias do Netgram ─────────────────────────────────
    rep_status = request.GET.get('rep_status', '')
    rep_type   = request.GET.get('rep_type', '')
    reports_qs = ContentReport.objects.select_related('reported_by').all()
    if rep_status:
        reports_qs = reports_qs.filter(status=rep_status)
    if rep_type:
        reports_qs = reports_qs.filter(content_type=rep_type)
    rep_counts = {
        'pending':   ContentReport.objects.filter(status='PENDING').count(),
        'reviewing': ContentReport.objects.filter(status='REVIEWING').count(),
        'resolved':  ContentReport.objects.filter(status='RESOLVED').count(),
        'dismissed': ContentReport.objects.filter(status='DISMISSED').count(),
    }

    # Enriquece denúncias com conteúdo real
    from .models import BuzzShare, BuzzComment as BC
    reports_with_content = []
    for r in ContentReport.objects.select_related('reported_by').all():
        content_text = content_author = content_date = None
        content_deleted = False
        try:
            if r.content_type == 'post':
                obj = BuzzShare.objects.select_related('employee').get(pk=r.content_id)
                content_text   = obj.text or '[Sem texto — apenas mídia]'
                content_author = str(obj.employee)
                content_date   = obj.created_at.strftime('%d/%m/%Y %H:%M')
            else:
                obj = BC.objects.select_related('employee').get(pk=r.content_id)
                content_text   = obj.text
                content_author = str(obj.employee)
                content_date   = obj.created_at.strftime('%d/%m/%Y %H:%M')
        except Exception:
            content_deleted = True
            content_text = '[Conteúdo já removido]'

        reports_with_content.append({
            'id':             r.id,
            'content_type':   r.content_type,
            'content_id':     r.content_id,
            'reason':         r.reason,
            'reporter':       f'{r.reported_by.first_name} {r.reported_by.last_name}',
            'reporter_email': getattr(r.reported_by, 'work_email', '-') or '-',
            'status':         r.status,
            'note':           r.moderator_note or '',
            'created_at':     r.created_at.strftime('%d/%m/%Y %H:%M'),
            'resolved_at':    r.resolved_at.strftime('%d/%m/%Y %H:%M') if r.resolved_at else '-',
            'content_text':   content_text,
            'content_author': content_author,
            'content_date':   content_date,
            'content_deleted': content_deleted,
        })

    return render(request, 'buzz/central_suporte.html', {
        'active_tab':           active_tab,
        'bugs':                 bugs_qs,
        'bug_counts':           bug_counts,
        'bug_status':           bug_status,
        'reports':              reports_qs,
        'reports_with_content': reports_with_content,
        'rep_counts':           rep_counts,
        'rep_status':           rep_status,
        'rep_type':             rep_type,
    })


def send_content_report_email(report):
    """
    Envia notificações por e-mail para o denunciante e para a equipe de moderação/RH
    com base no status atual da denúncia (PENDING, REVIEWING, RESOLVED, DISMISSED).
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    from core.models import OrangeUser
    from .models import BuzzShare, BuzzComment
    
    # 1. Busca trecho do conteúdo para exibir no e-mail
    content_preview = ""
    try:
        if report.content_type == 'post':
            obj = BuzzShare.objects.get(pk=report.content_id)
            content_preview = obj.text or '[Publicação com mídia]'
        else:
            obj = BuzzComment.objects.get(pk=report.content_id)
            content_preview = obj.text
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."
    except Exception:
        content_preview = "[Conteúdo já removido do sistema]"

    report_type_display = "Publicação" if report.content_type == 'post' else "Comentário"
    
    # E-mail do denunciante
    reporter_email = getattr(report.reported_by, 'work_email', None) or getattr(report.reported_by, 'other_email', None)
    
    # 2. Se status for PENDING, notifica a equipe de moderação/RH
    if report.status == 'PENDING':
        admin_hr_emails = list(OrangeUser.objects.filter(
            role__in=[OrangeUser.ROLE_ADMIN, OrangeUser.ROLE_HR],
            is_active=True
        ).exclude(email='').values_list('email', flat=True))
        
        if admin_hr_emails:
            try:
                from emails.utils import send_custom_email
                
                context_admin = {
                    'recipient_type': 'admin',
                    'report_id': report.id,
                    'report_type': report_type_display,
                    'reason': report.reason,
                    'content_preview': content_preview,
                    'status': report.status,
                }
                
                sent = send_custom_email('content_report_admin', context_admin, admin_hr_emails)
                
                if not sent:
                    html_admin = render_to_string('email/content_report_status.html', context_admin)
                    msg = EmailMultiAlternatives(
                        subject=f"[CDC] Nova denúncia de conteúdo #{report.id}",
                        body=f"Uma nova denúncia (#{report.id}) de {report_type_display.lower()} foi recebida e requer moderação.",
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@netlineplay.com.br'),
                        to=admin_hr_emails
                    )
                    msg.attach_alternative(html_admin, "text/html")
                    msg.send(fail_silently=True)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erro ao enviar email de denuncia para admins: {e}")

    # 3. Notifica o denunciante sobre o status atual
    if reporter_email:
        try:
            subject_map = {
                'PENDING': f"Denúncia #{report.id} registrada com sucesso",
                'REVIEWING': f"Sua denúncia #{report.id} está em análise",
                'RESOLVED': f"Sua denúncia #{report.id} foi resolvida",
                'DISMISSED': f"Sua denúncia #{report.id} foi concluída",
            }
            
            subject = subject_map.get(report.status, f"Atualização da Denúncia #{report.id}")
            body_text = f"Sua denúncia #{report.id} de {report_type_display.lower()} foi atualizada para: {report.get_status_display()}."
            
            context_reporter = {
                'recipient_type': 'reporter',
                'first_name': report.reported_by.first_name or "Colaborador",
                'report_id': report.id,
                'report_type': report_type_display,
                'reason': report.reason,
                'content_preview': content_preview,
                'status': report.status,
                'moderator_note': report.moderator_note,
                'status_display': report.get_status_display(),
            }
            
            from emails.utils import send_custom_email
            
            sent = send_custom_email('content_report_reporter', context_reporter, reporter_email)
            
            if not sent:
                html_reporter = render_to_string('email/content_report_status.html', context_reporter)
                
                msg = EmailMultiAlternatives(
                    subject=f"[Netgram] {subject}",
                    body=body_text,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@netlineplay.com.br'),
                    to=[reporter_email]
                )
                msg.attach_alternative(html_reporter, "text/html")
                msg.send(fail_silently=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao enviar email de atualizacao de denuncia para denunciante: {e}")


@login_required
def netgram_user_moderation(request):
    if not (request.user.is_admin() or request.user.is_superuser):
        return redirect('dashboard')
        
    query = request.GET.get('q', '').strip()
    from core.models import OrangeUser
    users = OrangeUser.objects.all().select_related('employee')
    if query:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(employee__first_name__icontains=query) |
            Q(employee__last_name__icontains=query)
        )
        
    users = users.order_by('username')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_id = request.POST.get('user_id')
        target_user = get_object_or_404(OrangeUser, id=user_id)
        target_user.is_netgram_suspended = not target_user.is_netgram_suspended
        target_user.save()
        return JsonResponse({
            'success': True,
            'is_netgram_suspended': target_user.is_netgram_suspended,
            'message': f'Status do usuário {target_user.username} atualizado com sucesso.'
        })
        
    return render(request, 'buzz/user_moderation.html', {
        'users': users,
        'q': query
    })
