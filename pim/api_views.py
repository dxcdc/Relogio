from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from .models import Employee, EmpPicture
from .serializers import EmployeeSerializer
from attendance.models import get_work_info_for_date
from leave.models import LeaveRequest
from buzz.models import ChangelogPost


def _get_role_label(user, employee):
    """Returns a display label based on OrangeUser.role field."""
    # Use the system's own role field on OrangeUser
    role = getattr(user, 'role', None)
    if role:
        return role  # 'Admin', 'HR', 'Supervisor', 'ESS'
    # Fallback: job title from Employee (FK field is .title not .name)
    if employee.job_title:
        return employee.job_title.title
    return 'Funcionário'


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para buscar listar os funcionários (apenas leitura para o app por enquanto)
    """
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class DashboardAPIView(APIView):
    """
    Endpoint para alimentar o Dashboard do app mobile.
    PERFORMANCE: resposta cacheada 60s por funcionário.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Funcionario nao encontrado"}, status=404)

        from django.core.cache import cache as _cache
        _ck = f'dashboard_api_{employee.pk}'
        # Se for uma requisição de atualização forçada (pull-to-refresh), remove o cache
        if request.query_params.get('refresh') == 'true':
            _cache.delete(_ck)
        else:
            _cached = _cache.get(_ck)
            if _cached is not None:
                return Response(_cached)

        today = timezone.now().date()

        # ── Time ──────────────────────────────────────────────────────────────
        team_members = []
        department_name = "SEM DEPARTAMENTO"
        if employee.sub_division:
            department_name = employee.sub_division.name
            colleagues = Employee.objects.filter(
                sub_division=employee.sub_division,
                state=Employee.STATE_ACTIVE
            ).exclude(id=employee.id)[:6]

            for col in colleagues:
                first = col.first_name[0] if col.first_name else ''
                last = col.last_name[0] if col.last_name else ''
                initials = (first + last).upper()
                if not initials and col.first_name and len(col.first_name) >= 2:
                    initials = col.first_name[:2].upper()
                team_members.append({
                    "initials": initials,
                    "color": "#f8fafc",
                    "text_color": "#64748b"
                })

        # ── Managers ──────────────────────────────────────────────────────────
        managers = []
        supervisors = employee.supervisors.all()
        for sup in supervisors:
            first = sup.first_name[0] if sup.first_name else ''
            last = sup.last_name[0] if sup.last_name else ''
            initials = (first + last).upper()
            if not initials and sup.first_name and len(sup.first_name) >= 2:
                initials = sup.first_name[:2].upper()
            managers.append({
                "initials": initials,
                "color": "#e8f0fe",
                "text_color": "#3C78D8"
            })

        if not managers and employee.sub_division and getattr(employee.sub_division, 'supervisor', None):
            sup = employee.sub_division.supervisor
            first = sup.first_name[0] if sup.first_name else ''
            last = sup.last_name[0] if sup.last_name else ''
            initials = (first + last).upper()
            managers.append({
                "initials": initials,
                "color": "#e8f0fe",
                "text_color": "#3C78D8"
            })

        # ── Announcements ─────────────────────────────────────────────────────
        from core.models import Announcement
        from django.db.models import Q

        announcement_query = Q(is_active=True)
        dept_query = Q(visibility=Announcement.VISIBILITY_ALL)
        if employee.sub_division:
            dept_query |= Q(visibility=Announcement.VISIBILITY_DEPT, department=employee.sub_division)

        announcements_qs = Announcement.objects.filter(announcement_query & dept_query).order_by('-created_at')

        announcement_items = []
        for ann in announcements_qs:
            announcement_items.append({
                "id": ann.id,
                "title": ann.title,
                "content": ann.content,
                "date": ann.created_at.strftime('%d/%m/%Y'),
                "image": request.build_absolute_uri(ann.image.url) if ann.image else None,
            })

        announcements = {
            "has_announcements": len(announcement_items) > 0,
            "items": announcement_items
        }

        # ── Leave stats — 3 queries → 1 aggregate ────────────────────────────
        from django.db.models import Count, Case, When, IntegerField
        leave_agg = LeaveRequest.objects.filter(employee=employee).aggregate(
            pending_count=Count(Case(
                When(status=LeaveRequest.STATUS_PENDING, then=1),
                output_field=IntegerField()
            )),
            pending_or_sup=Count(Case(
                When(status__in=[LeaveRequest.STATUS_PENDING, LeaveRequest.STATUS_SUPERVISOR_APPROVED], then=1),
                output_field=IntegerField()
            )),
            future_approved=Count(Case(
                When(status=LeaveRequest.STATUS_APPROVED, from_date__gte=today, then=1),
                output_field=IntegerField()
            )),
        )
        pending_my_leaves = leave_agg['pending_count']
        pending_days      = leave_agg['pending_or_sup']
        future_approved   = leave_agg['future_approved']

        notifications = {
            "has_notifications": False,
            "text": "Tudo limpo! Nenhuma pendencia."
        }
        if pending_my_leaves > 0:
            notifications = {
                "has_notifications": True,
                "text": f"Voce tem {pending_my_leaves} licenca(s) aguardando aprovacao."
            }

        absences = {
            "pending": pending_days,
            "approved": future_approved
        }

        # ── Work info + Attendance (prefetch punches em 1 query) ──────────────
        from attendance.models import AttendanceRecord
        work_info = get_work_info_for_date(employee, today)
        entry = work_info.get('entry_time')
        exit_time = work_info.get('exit_time')
        shift_start = entry.strftime('%H:%M') if entry else ''
        shift_end = exit_time.strftime('%H:%M') if exit_time else ''

        record = AttendanceRecord.objects.filter(
            employee=employee, date=today
        ).prefetch_related('punches').first()

        worked_seconds = record.net_seconds_worked if record else 0
        current_state = record.current_state if record else None
        next_action = 'OUT' if current_state == 'IN' else 'IN'

        # Usa punches já prefetchados (evita query extra de .exists())
        punches_list = list(record.punches.all()) if record else []
        has_punches = len(punches_list) > 0

        # RoleModuleAccess — usa cache de 5 min compartilhado com context_processor
        config_require_all = False
        if request.user and getattr(request.user, 'role', None):
            _acc_key = f'module_perms_{request.user.pk}_{request.user.role}'
            _acc_data = _cache.get(_acc_key)
            if _acc_data is not None:
                config_require_all = _acc_data.get('attendance_photo_all_punches', False)
            else:
                from core.models import RoleModuleAccess
                acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
                if acc:
                    config_require_all = getattr(acc, 'attendance_photo_all_punches', False)

        require_photo = True if not has_punches else config_require_all

        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        journey = {
            "worked_time": format_time(worked_seconds),
            "shift_start": shift_start,
            "shift_end": shift_end,
            "current_state": current_state,
            "next_action": next_action,
            "require_photo": require_photo,
        }

        # ── Display name ──────────────────────────────────────────────────────
        fn = (employee.first_name or '').strip()
        full = (employee.full_name or '').strip()
        full_parts = full.split() if full else []
        display_first = (
            fn
            or (full_parts[0] if full_parts else None)
            or (request.user.first_name or '').strip()
            or request.user.username
        )

        # ── Surveys — query direta em vez de loop Python ───────────────────
        pending_surveys = []
        try:
            from performance.models import Survey, SurveyResponse
            now_dt = timezone.now()

            answered_ids = SurveyResponse.objects.filter(
                employee=employee
            ).values_list('survey_id', flat=True)

            target_filter = (
                Q(target_type='ALL') |
                Q(target_type='LEGAL_ENTITY', target_legal_entity_id=getattr(employee, 'legal_entity_id', None)) |
                Q(target_type='SUBUNIT', target_subunit_id=getattr(employee, 'sub_division_id', None)) |
                Q(target_type='CITY', target_city_id=getattr(employee, 'city_id', None))
            )

            for s in Survey.objects.filter(
                status='PUBLISHED',
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now_dt)
            ).filter(target_filter).exclude(id__in=answered_ids).order_by('-created_at')[:5]:
                pending_surveys.append({
                    'id': s.id,
                    'title': s.title,
                    'description': s.description or '',
                    'is_anonymous': s.is_anonymous,
                })
        except Exception:
            pending_surveys = []

        # ── Profile picture ───────────────────────────────────────────────────
        user_picture = ''
        try:
            if hasattr(employee, 'picture') and employee.picture and employee.picture.picture:
                user_picture = request.build_absolute_uri(employee.picture.picture.url)
        except Exception:
            pass

        allow_shift_swaps = False
        try:
            if hasattr(employee, 'sub_division') and employee.sub_division:
                allow_shift_swaps = getattr(employee.sub_division, 'allow_shift_swaps', False)
                role_access_data = getattr(employee, 'get_role_access', lambda: None)()
                if role_access_data and not role_access_data.get('swap', True):
                    allow_shift_swaps = False
        except Exception:
            pass

        # ── Monta resposta e cacheia 60s ───────────────────────────────────
        response_data = {
            "user": {
                "id": request.user.id,
                "first_name": display_first,
                "full_name": full or request.user.get_full_name() or request.user.username,
                "role": _get_role_label(request.user, employee),
                "job_title": employee.job_title.title if employee.job_title else '',
                "picture": user_picture,
                "allow_shift_swaps": allow_shift_swaps,
                "is_supervisor": request.user.is_supervisor(),
                "is_netgram_suspended": getattr(request.user, 'is_netgram_suspended', False),
            },
            "team": {
                "department": department_name.upper(),
                "colleagues": team_members
            },
            "managers": managers,
            "announcements": announcements,
            "notifications": notifications,
            "absences": absences,
            "journey": journey,
            "pending_surveys": pending_surveys,
        }
        _cache.set(_ck, response_data, 60)
        return Response(response_data)




class MyProfileAPIView(APIView):

    """
    Endpoint para o funcionário visualizar e editar seu próprio perfil pessoal no app mobile.
    GET  -> retorna dados pessoais editáveis
    PATCH -> atualiza campos pessoais (nome, celular, aniversário, email pessoal)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Funcionário não encontrado"}, status=404)

        picture_url = ''
        try:
            if hasattr(employee, 'picture') and employee.picture and employee.picture.picture:
                picture_url = request.build_absolute_uri(employee.picture.picture.url)
        except Exception:
            pass

        return Response({
            "first_name": employee.first_name or '',
            "last_name": employee.last_name or '',
            "mobile": employee.mobile or '',
            "birthday": employee.birthday.strftime('%Y-%m-%d') if employee.birthday else '',
            "other_email": employee.other_email or '',
            "job_title": employee.job_title.title if employee.job_title else '',
            "department": employee.sub_division.name if employee.sub_division else '',
            "picture": picture_url,
            "username": request.user.username,
            "email": request.user.email or '',
            # Address
            "street1": employee.street1 or '',
            "street2": employee.street2 or '',
            "zipcode": employee.zipcode or '',
            "home_telephone": employee.home_telephone or '',
            "city_id": employee.city_id if employee.city_id else None,
            "city_name": str(employee.city) if employee.city else '',
        })

    def patch(self, request):
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({"error": "Funcionário não encontrado"}, status=404)

        data = request.data

        # Personal fields the employee is allowed to edit themselves
        if 'first_name' in data and data['first_name'].strip():
            employee.first_name = data['first_name'].strip()
        if 'last_name' in data and data['last_name'].strip():
            employee.last_name = data['last_name'].strip()
        if 'mobile' in data:
            employee.mobile = data['mobile'].strip()
        if 'other_email' in data:
            employee.other_email = data['other_email'].strip() or None
        if 'birthday' in data and data['birthday']:
            try:
                from datetime import datetime
                employee.birthday = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Formato de data inválido. Use AAAA-MM-DD."}, status=400)

        # Address fields
        if 'street1' in data:
            employee.street1 = data['street1'].strip() or None
        if 'street2' in data:
            employee.street2 = data['street2'].strip() or None
        if 'zipcode' in data:
            employee.zipcode = data['zipcode'].strip() or None
        if 'home_telephone' in data:
            employee.home_telephone = data['home_telephone'].strip() or None
        if 'city_id' in data:
            try:
                from admin_app.models import City
                city_id = int(data['city_id'])
                employee.city = City.objects.get(pk=city_id)
            except (ValueError, TypeError, City.DoesNotExist):
                employee.city = None

        employee.save()

        # Handle profile picture upload
        if 'picture' in request.FILES:
            pic_file = request.FILES['picture']
            try:
                emp_pic = EmpPicture.objects.filter(employee=employee).first()
                if emp_pic:
                    emp_pic.picture = pic_file
                    emp_pic.file_name = pic_file.name
                    emp_pic.file_type = pic_file.content_type
                    emp_pic.save()
                else:
                    EmpPicture.objects.create(
                        employee=employee,
                        picture=pic_file,
                        file_name=pic_file.name,
                        file_type=pic_file.content_type,
                    )
            except Exception as e:
                return Response({"error": f"Erro ao salvar foto: {str(e)}"}, status=500)

        return Response({"success": True, "message": "Perfil atualizado com sucesso."})


class CitiesAPIView(APIView):
    """
    Retorna a lista de todas as cidades cadastradas para o seletor de Cidade Base no app mobile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from admin_app.models import City
        from django.core.cache import cache as _cache
        # Cidades raramente mudam — cache de 24 horas
        _ck = 'cities_list_api'
        data = _cache.get(_ck)
        if data is None:
            cities = City.objects.select_related('province').order_by('name')
            data = [
                {
                    'id': c.id,
                    'name': str(c),  # Ex: "CAJAZEIRAS - PB"
                }
                for c in cities
            ]
            _cache.set(_ck, data, 60 * 60 * 24)  # 24 horas
        return Response(data)


from django.db import transaction
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .utils import generate_uppercase_username, generate_random_temp_password
from core.models import OrangeUser
from admin_app.models import JobTitle, Subunit, LegalEntity, City
from attendance.models import WorkSchedule
from admin_app.models import WorkShift

class OnboardingAPIView(APIView):
    """
    Endpoint seguro para admissão de novos funcionários integrados ao Sesame HR.
    Cria o Employee, gera o OrangeUser (username maiúsculo), envia o e-mail de boas-vindas.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        
        # Validação de campos obrigatórios
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return Response({"error": f"O campo '{field}' é obrigatório."}, status=400)
        
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        email = data['email'].strip().lower()
        mobile = data.get('mobile', '').strip()
        birthday_str = data.get('birthday', '')
        cpf = data.get('cpf', '').strip()
        
        # Resolução de Modelos Relacionados por texto
        job_title = None
        if data.get('job_title'):
            job_title, _ = JobTitle.objects.get_or_create(title=data['job_title'].strip())
            
        subunit = None
        if data.get('department'):
            subunit, _ = Subunit.objects.get_or_create(name=data['department'].strip())
            
        legal_entity = None
        if data.get('legal_entity'):
            legal_entity = LegalEntity.objects.filter(name__iexact=data['legal_entity'].strip()).first()
            
        city = None
        if data.get('city'):
            city = City.objects.filter(name__iexact=data['city'].strip()).first()

        work_schedule = None
        if data.get('work_schedule'):
            work_schedule = WorkSchedule.objects.filter(name__iexact=data['work_schedule'].strip()).first()
            
        work_shift = None
        if data.get('work_shift'):
            work_shift = WorkShift.objects.filter(name__iexact=data['work_shift'].strip()).first()

        # 1. Criação do Perfil do Funcionário
        employee = Employee.objects.create(
            first_name=first_name,
            last_name=last_name,
            work_email=email,
            mobile=mobile,
            ssn_number=cpf or None,
            job_title=job_title,
            sub_division=subunit,
            legal_entity=legal_entity,
            city=city,
            work_schedule=work_schedule,
            work_shift=work_shift,
            state=Employee.STATE_ACTIVE
        )
        
        # 2. Geração automática de credenciais
        username = generate_uppercase_username(first_name, last_name)
        temp_password = generate_random_temp_password()
        
        # 3. Criação da Conta do Usuário e Vínculo
        user = OrangeUser.objects.create_user(
            username=username,
            email=email,
            password=temp_password,
            role=OrangeUser.ROLE_ESS,
            employee=employee
        )
        
        # 4. Disparo do E-mail de Boas-Vindas Premium
        try:
            from emails.utils import send_custom_email
            context = {
                'first_name': first_name,
                'username': username,
                'temp_password': temp_password,
            }
            
            email_sent = send_custom_email('onboard_welcome', context, email)
            if not email_sent:
                html_content = render_to_string('email/welcome_onboarding.html', context)
                email_msg = EmailMultiAlternatives(
                    subject="Bem-vindo(a) ao CDC. Suas credenciais de acesso",
                    body=f"Olá, {first_name}! Seu usuário é {username} e sua senha é {temp_password}.",
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@netlineplay.com.br'),
                    to=[email],
                )
                email_msg.attach_alternative(html_content, "text/html")
                email_msg.send(fail_silently=True)
                email_sent = True
        except Exception as e:
            email_sent = False
            # Registrar erro de disparo no log de auditoria, mas sem abortar o cadastro
            import logging
            logging.getLogger(__name__).error(f"Falha ao enviar e-mail de boas-vindas: {e}")

        return Response({
            "success": True,
            "employee_id": employee.employee_id,
            "username": username,
            "email_sent": email_sent
        }, status=201)
