from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from .models import ChangelogPost, BugReport, BugReportComment, BugReportScreenshot, BuzzShare, BuzzLikeOnShare, BuzzPost, BuzzPhoto, BuzzComment, ContentReport
from core.models import OrangeUser


class ChangelogListAPIView(APIView):
    """
    Retorna as notas de atualização do sistema publicadas pelos admins.
    GET /api/v1/buzz/changelogs/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        changelogs = ChangelogPost.objects.all()[:30]
        data = []
        for c in changelogs:
            data.append({
                'id': c.id,
                'title': c.title,
                'version': c.version,
                'category': c.category,
                'category_display': c.get_category_display(),
                'category_color': c.category_color,
                'content': c.content,
                'pinned': c.pinned,
                'published_at': c.published_at.isoformat(),
            })
        return Response(data)


class MyBugReportsAPIView(APIView):
    """
    Retorna os chamados (BugReports) abertos pelo usuário logado.
    GET /api/v1/buzz/my-reports/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = BugReport.objects.filter(
            reported_by=request.user
        ).order_by('-created_at')[:50]

        data = []
        for r in reports:
            data.append({
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'status': r.status,
                'status_display': r.get_status_display(),
                'status_color': r.status_color,
                'priority': r.priority,
                'priority_display': r.get_priority_display(),
                'priority_color': r.priority_color,
                'created_at': r.created_at.isoformat(),
                'resolved_at': r.resolved_at.isoformat() if r.resolved_at else None,
                'comments_count': r.public_comments_count,
            })
        return Response(data)


class CreateBugReportAPIView(APIView):
    """
    Abre um novo chamado/bug report pelo usuário logado.
    POST /api/v1/buzz/report/
    Body: { "title": "...", "description": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '').strip()
        description = request.data.get('description', '').strip()
        screenshots = request.FILES.getlist('screenshots')

        if not title:
            return Response(
                {"error": "O titulo do chamado e obrigatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not description:
            return Response(
                {"error": "A descricao do chamado e obrigatoria."},
                status=status.HTTP_400_BAD_REQUEST
            )

        report = BugReport.objects.create(
            title=title,
            description=description,
            reported_by=request.user,
            status=BugReport.STATUS_OPEN,
            priority=BugReport.PRIORITY_MEDIUM,
        )
        
        for img in screenshots:
            BugReportScreenshot.objects.create(bug_report=report, image=img)

        return Response(
            {"message": "Chamado aberto com sucesso!", "id": report.id},
            status=status.HTTP_201_CREATED
        )


class BugReportDetailAPIView(APIView):
    """
    Retorna os detalhes de um chamado e a lista de comentários.
    GET /api/v1/buzz/report/<id>/
    POST /api/v1/buzz/report/<id>/ (para adicionar comentário)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        report = get_object_or_404(BugReport, pk=pk, reported_by=request.user)
        
        comments = report.comments.filter(is_internal=False).order_by('created_at')
        comments_data = []
        for c in comments:
            comments_data.append({
                'id': c.id,
                'author': 'Você' if c.author == request.user else c.author.get_full_name() or c.author.username,
                'is_author': c.author == request.user,
                'content': c.content,
                'created_at': c.created_at.isoformat(),
            })

        screenshots = []
        for s in report.screenshots.all():
            if s.image:
                screenshots.append(request.build_absolute_uri(s.image.url))

        return Response({
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'status_display': report.get_status_display(),
            'status_color': report.status_color,
            'created_at': report.created_at.isoformat(),
            'comments': comments_data,
            'screenshots': screenshots,
        })

    def post(self, request, pk):
        report = get_object_or_404(BugReport, pk=pk, reported_by=request.user)
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response({'error': 'Conteúdo do comentário é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        BugReportComment.objects.create(
            bug_report=report,
            author=request.user,
            content=content,
            is_internal=False
        )
        
        return Response({'success': True, 'message': 'Resposta enviada com sucesso!'})

class BuzzFeedAPIView(APIView):
    """
    Retorna o Feed do Netgram (Buzz).
    GET /api/v1/buzz/feed/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated and getattr(request.user, 'is_netgram_suspended', False):
            return Response({"error": "Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso."}, status=status.HTTP_403_FORBIDDEN)
        all_blocked_ids = set()
        if request.user.is_authenticated:
            blocked_by_me = list(request.user.blocked_users.values_list('id', flat=True))
            blocked_me = list(request.user.blocked_by_users.values_list('id', flat=True))
            all_blocked_ids = set(blocked_by_me + blocked_me)

        shares = BuzzShare.objects.select_related(
            'employee', 'post', 'employee__user', 'post__employee__user'
        ).order_by('-created_at')

        if request.user.is_authenticated and all_blocked_ids:
            shares = shares.exclude(employee__user__id__in=all_blocked_ids)
            shares = shares.exclude(post__employee__user__id__in=all_blocked_ids)

        shares = shares[:30]
        data = []

        current_emp = getattr(request.user, 'employee', None)
        
        for share in shares:
            author = share.employee
            first = author.first_name[0] if author.first_name else ''
            last = author.last_name[0] if author.last_name else ''
            initials = (first + last).upper()
            if not initials and author.first_name and len(author.first_name) >= 2:
                initials = author.first_name[:2].upper()

            liked = False
            if current_emp:
                liked = BuzzLikeOnShare.objects.filter(share=share, employee=current_emp).exists()

            photos = []
            if share.post:
                for photo_obj in share.post.photos.all():
                    if photo_obj.photo:
                        photos.append(request.build_absolute_uri(photo_obj.photo.url))
            
            text = share.text
            if not text and share.post:
                text = share.post.text

            comments_data = []
            for comment in share.comments.select_related('employee', 'employee__user').all():
                c_author = comment.employee
                c_user = getattr(c_author, 'user', None)
                if c_user and c_user.id in all_blocked_ids:
                    continue

                c_first = c_author.first_name[0] if c_author.first_name else ''
                c_last = c_author.last_name[0] if c_author.last_name else ''
                c_initials = (c_first + c_last).upper()
                if not c_initials and c_author.first_name and len(c_author.first_name) >= 2:
                    c_initials = c_author.first_name[:2].upper()

                c_picture = ''
                try:
                    if hasattr(c_author, 'picture') and c_author.picture and c_author.picture.picture:
                        c_picture = request.build_absolute_uri(c_author.picture.picture.url)
                except Exception:
                    pass

                comments_data.append({
                    'id': comment.id,
                    'author_id': c_user.id if c_user else None,
                    'author_name': f"{c_author.first_name} {c_author.last_name}".strip(),
                    'author_initials': c_initials,
                    'author_picture': c_picture,
                    'text': comment.text,
                    'created_at': comment.created_at.isoformat(),
                })
                
            a_picture = ''
            try:
                if hasattr(author, 'picture') and author.picture and author.picture.picture:
                    a_picture = request.build_absolute_uri(author.picture.picture.url)
            except Exception:
                pass

            a_user = getattr(author, 'user', None)

            data.append({
                'id': share.id,
                'author': {
                    'id': a_user.id if a_user else None,
                    'name': f"{author.first_name} {author.last_name}".strip(),
                    'initials': initials,
                    'picture': a_picture,
                },
                'text': text,
                'photos': photos,
                'num_of_likes': share.num_of_likes,
                'num_of_comments': share.num_of_comments,
                'is_liked': liked,
                'comments': comments_data,
                'created_at': share.created_at.isoformat(),
            })

        return Response(data)

class CreateBuzzPostAPIView(APIView):
    """
    Cria uma nova postagem no Feed.
    POST /api/v1/buzz/feed/post/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_authenticated and getattr(request.user, 'is_netgram_suspended', False):
            return Response({"error": "Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso."}, status=status.HTTP_403_FORBIDDEN)
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Perfil de funcionário não encontrado."}, status=status.HTTP_400_BAD_REQUEST)
        
        text = request.data.get('text', '').strip()
        photos = request.FILES.getlist('photos')
        if not photos and request.FILES.get('photo'):
            photos = [request.FILES.get('photo')]

        if not text and not photos:
            return Response({"error": "A postagem não pode estar vazia."}, status=status.HTTP_400_BAD_REQUEST)

        
        post_obj = BuzzPost.objects.create(text=text, employee=employee)
        
        
        if photos:
            for photo in photos:
                BuzzPhoto.objects.create(post=post_obj, photo=photo)
            
        
        share = BuzzShare.objects.create(post=post_obj, employee=employee, type='post', text=text)
        
        from core.push_notifications import send_push_to_users
        from core.models import OrangeUser
        import threading
        
        users = OrangeUser.objects.filter(is_active=True).exclude(id=request.user.id)
        if users.exists():
            users_list = list(users)
            threading.Thread(
                target=send_push_to_users,
                args=(users_list, "Novo post no Netgram!", f"{employee.first_name} publicou algo novo. Vem conferir!", {'route': '/buzz'}),
                daemon=True
            ).start()
        
        return Response({"message": "Postagem criada!", "id": share.id}, status=status.HTTP_201_CREATED)

class ToggleBuzzLikeAPIView(APIView):
    """
    Dá like ou desfaz o like em uma postagem (share).
    POST /api/v1/buzz/feed/<id>/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.is_authenticated and getattr(request.user, 'is_netgram_suspended', False):
            return Response({"error": "Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso."}, status=status.HTTP_403_FORBIDDEN)
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Acesso negado."}, status=status.HTTP_400_BAD_REQUEST)

        share = get_object_or_404(BuzzShare, pk=pk)
        
        like, created = BuzzLikeOnShare.objects.get_or_create(share=share, employee=employee)
        
        if created:
            
            share.num_of_likes += 1
            share.save(update_fields=['num_of_likes'])
            liked = True
            
            owner_user = getattr(share.employee, 'user', None)
            if owner_user and owner_user.id != request.user.id:
                from core.push_notifications import send_push
                import threading
                threading.Thread(
                    target=send_push,
                    args=(owner_user, "Alguém curtiu seu post", f"{employee.first_name} curtiu sua postagem no Netgram.", {'route': '/buzz'}),
                    daemon=True
                ).start()
        else:
            
            like.delete()
            if share.num_of_likes > 0:
                share.num_of_likes -= 1
                share.save(update_fields=['num_of_likes'])
            liked = False
            
        return Response({"is_liked": liked, "num_of_likes": share.num_of_likes})

class AddBuzzCommentAPIView(APIView):
    """
    Adiciona um comentário a uma postagem no Feed.
    POST /api/v1/buzz/feed/<id>/comment/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.is_authenticated and getattr(request.user, 'is_netgram_suspended', False):
            return Response({"error": "Seu acesso ao Netgram foi suspenso devido a violação dos Termos de Uso."}, status=status.HTTP_403_FORBIDDEN)
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Perfil de funcionário não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        share = get_object_or_404(BuzzShare, pk=pk)
        text = request.data.get('text', '').strip()

        if not text:
            return Response({"error": "O comentário não pode estar vazio."}, status=status.HTTP_400_BAD_REQUEST)

        comment = BuzzComment.objects.create(share=share, employee=employee, text=text)
        
        share.num_of_comments += 1
        share.save(update_fields=['num_of_comments'])
        
        owner_user = getattr(share.employee, 'user', None)
        if owner_user and owner_user.id != request.user.id:
            from core.push_notifications import send_push
            import threading
            threading.Thread(
                target=send_push,
                args=(owner_user, "Novo comentário!", f"{employee.first_name} comentou: {text[:30]}", {'route': '/buzz'}),
                daemon=True
            ).start()
        
        c_first = employee.first_name[0] if employee.first_name else ''
        c_last = employee.last_name[0] if employee.last_name else ''
        c_initials = (c_first + c_last).upper()
        if not c_initials and employee.first_name and len(employee.first_name) >= 2:
            c_initials = employee.first_name[:2].upper()

        comment_data = {
            'id': comment.id,
            'author_name': f"{employee.first_name} {employee.last_name}".strip(),
            'author_initials': c_initials,
            'text': comment.text,
            'created_at': comment.created_at.isoformat(),
        }

        return Response({"message": "Comentário adicionado com sucesso!", "comment": comment_data}, status=status.HTTP_201_CREATED)


class ReportContentAPIView(APIView):
    """
    Recebe uma denúncia de conteúdo inapropriado no Netgram.
    Exigido pela Apple App Store Guideline 1.2 — User-Generated Content.

    POST /api/v1/buzz/report-content/
    Body: {
        "content_type": "post" | "comment",
        "content_id": <int>,
        "reason": "<string>"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response(
                {"error": "Perfil de funcionário não encontrado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        content_type = request.data.get('content_type', '').strip().lower()
        content_id = request.data.get('content_id')
        reason = request.data.get('reason', '').strip()

        # Validações
        if content_type not in ('post', 'comment'):
            return Response(
                {"error": "Tipo de conteúdo inválido. Use 'post' ou 'comment'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not content_id:
            return Response(
                {"error": "ID do conteúdo é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not reason:
            return Response(
                {"error": "O motivo da denúncia é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Impede denúncia duplicada do mesmo usuário para o mesmo conteúdo
        already_reported = ContentReport.objects.filter(
            content_type=content_type,
            content_id=content_id,
            reported_by=employee,
        ).exists()
        if already_reported:
            return Response(
                {"message": "Você já denunciou este conteúdo. Nossa equipe está analisando."},
                status=status.HTTP_200_OK
            )

        report = ContentReport.objects.create(
            content_type=content_type,
            content_id=content_id,
            reason=reason,
            reported_by=employee,
            status=ContentReport.STATUS_PENDING,
        )

        # Envia e-mails de notificação (para admins/RH e para o denunciante)
        try:
            from .views import send_content_report_email
            send_content_report_email(report)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Falha ao enviar email inicial da denuncia: {e}")

        return Response(
            {"message": "Denúncia enviada com sucesso. Nossa equipe irá analisar em até 24h."},
            status=status.HTTP_201_CREATED
        )


class BlockUserAPIView(APIView):
    """
    Bloqueia ou desbloqueia um usuário abusivo.
    POST /api/v1/buzz/block-user/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        target_user_id = request.data.get('target_user_id')
        if not target_user_id:
            return Response({"error": "ID do usuário alvo é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user_id = int(target_user_id)
        except ValueError:
            return Response({"error": "ID do usuário inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if target_user_id == request.user.id:
            return Response({"error": "Você não pode bloquear a si mesmo."}, status=status.HTTP_400_BAD_REQUEST)
            
        target_user = get_object_or_404(OrangeUser, id=target_user_id)
        
        if request.user.blocked_users.filter(id=target_user_id).exists():
            request.user.blocked_users.remove(target_user)
            return Response({
                "message": f"Usuário {target_user.username} desbloqueado com sucesso.",
                "blocked": False
            }, status=status.HTTP_200_OK)
        else:
            request.user.blocked_users.add(target_user)
            return Response({
                "message": f"Usuário {target_user.username} bloqueado com sucesso.",
                "blocked": True
            }, status=status.HTTP_200_OK)
