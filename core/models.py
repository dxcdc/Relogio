from django.contrib.auth.models import AbstractUser
from django.db import models
import logging

logger = logging.getLogger(__name__)


class OrangeUser(AbstractUser):
    """Usuário do sistemo CDC"""
    ROLE_ADMIN = 'Admin'
    ROLE_HR = 'HR'
    ROLE_ESS = 'ESS'
    ROLE_SUPERVISOR = 'Supervisor'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador'),
        (ROLE_HR, 'Recursos Humanos (RH)'),
        (ROLE_ESS, 'Funcionário (ESS)'),
        (ROLE_SUPERVISOR, 'Supervisor'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ESS)
    is_deleted = models.BooleanField(default=False)
    employee = models.OneToOneField(
        'pim.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='user'
    )
    fcm_token = models.CharField(
        max_length=500, null=True, blank=True,
        verbose_name='Token FCM (Push Notification)',
        help_text='Token do dispositivo móvel para envio de push notifications via Firebase.'
    )
    blocked_users = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='blocked_by_users',
        blank=True,
        verbose_name='Usuários Bloqueados'
    )
    is_netgram_suspended = models.BooleanField(
        default=False,
        verbose_name='Acesso ao Netgram Suspenso',
        help_text='Indica se o usuário está suspenso de utilizar a rede social interna (Netgram).'
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_HR]
        
    def is_hr(self):
        return self.role == self.ROLE_HR

    def is_supervisor(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_HR, self.ROLE_SUPERVISOR]


class RoleModuleAccess(models.Model):
    """Controle de Feature Toggles por Cargo/Tipo de Usuário"""
    role = models.CharField(max_length=20, choices=OrangeUser.ROLE_CHOICES, unique=True, verbose_name="Tipo de Usuário")
    netgram = models.BooleanField(default=True, verbose_name="Módulo Netgram")
    netgram_post = models.BooleanField(default=True, verbose_name="Permitir Postagens no Netgram")
    org_chart = models.BooleanField(default=True, verbose_name="Módulo Organograma")
    attendance = models.BooleanField(default=True, verbose_name="Meus Registros de Ponto")
    attendance_photo_all_punches = models.BooleanField(default=False, verbose_name="Exigir foto em todas as batidas")
    attendance_block_early_punch = models.BooleanField(default=False, verbose_name="Bloquear ponto antecipado")
    attendance_block_off_days = models.BooleanField(default=False, verbose_name="Bloquear ponto em dias de folga")
    leave = models.BooleanField(default=True, verbose_name="Férias/Ausências")
    swap = models.BooleanField(default=True, verbose_name="Módulo de Trocas DSR")
    claim = models.BooleanField(default=True, verbose_name="Reembolsos/Despesas")
    performance = models.BooleanField(default=True, verbose_name="Desempenho/Avaliações")
    agenda = models.BooleanField(default=True, verbose_name="Agenda Corporativa")
    
    
    endpoints = models.BooleanField(default=True, verbose_name="Endpoints API")
    team_employees = models.BooleanField(default=True, verbose_name="Equipe: Funcionários")
    team_approvals = models.BooleanField(default=True, verbose_name="Equipe: Central de Aprovações")
    team_attendance = models.BooleanField(default=True, verbose_name="Equipe: Ponto/Relatórios")
    admin_core = models.BooleanField(default=True, verbose_name="Admin: Cadastros Base")
    admin_attendance = models.BooleanField(default=True, verbose_name="Admin: Escalas e Fechamento")
    audit = models.BooleanField(default=True, verbose_name="Log de Auditoria")
    support_tickets = models.BooleanField(default=True, verbose_name="Suporte & Chamados")
    announcements = models.BooleanField(default=True, verbose_name="Mural de Avisos")
    reports = models.BooleanField(default=True, verbose_name="Relatórios Gerenciais")
    integrations = models.BooleanField(default=True, verbose_name="Integrações & API (Em Construção)")

    class Meta:
        verbose_name = 'Controle de Módulo por Cargo'
        verbose_name_plural = 'Controles de Módulos por Cargo'

    def __str__(self):
        return f"Acessos Módulos: {self.get_role_display()}"


class Config(models.Model):
    """Configurações do sistema"""
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

    def __str__(self):
        return self.name


class EmailConfiguration(models.Model):
    """Configuração de email SMTP"""
    mail_type = models.CharField(max_length=50, default='smtp')
    sent_as = models.EmailField(max_length=100, null=True, blank=True)
    smtp_host = models.CharField(max_length=100, null=True, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=100, null=True, blank=True)
    smtp_password = models.CharField(max_length=100, null=True, blank=True)
    smtp_auth_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = 'Configuração de Email'

    def __str__(self):
        return f"Email Config ({self.smtp_host})"

class Notification(models.Model):
    """Notificações in-app do usuário"""
    user = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notificação para {self.user.username}"





from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.contrib import messages

@receiver(user_logged_in)
def trigger_birthday_notification(sender, user, request, **kwargs):
    """
    Automação CDC: Quando o usuário faz login, verifica se é o aniversário 
    dele e gera uma notificação in-app + mensagem flash.
    """
    try:
        employee = getattr(user, 'employee', None)
        if not employee or not employee.birthday:
            return
            
        today = timezone.localdate()
        if employee.birthday.day == today.day and employee.birthday.month == today.month:
            
            already_notified = Notification.objects.filter(
                user=user, 
                message__icontains='Feliz Aniversário',
                created_at__year=today.year
            ).exists()
            
            if not already_notified:
                msg = f'Feliz Aniversário, {employee.first_name}! O CDC lhe deseja um excelente dia!'
                
                Notification.objects.create(
                    user=user,
                    message=msg,
                    link='/pim/my-info/'
                )
                
                
                try:
                    from buzz.models import BuzzPost, BuzzShare
                    from pim.models import Employee
                    
                    
                    system_emp, _ = Employee.objects.get_or_create(
                        employee_id='SYS-0000',
                        defaults={
                            'first_name': 'Sistema', 
                            'last_name': 'CDC',
                            'work_email': 'sistema@netline.com',
                            'is_time_tracking_exempt': True
                        }
                    )
                    
                    buzz_text = (
                        f"🎉 Hoje é o aniversário de **{employee.full_name}**!\n\n"
                        f"Vamos todos desejar muita saúde, sucesso e realizações para mais este novo ciclo.\n"
                        f"Deixe seus parabéns nos comentários!"
                    )
                    
                    buzz_post = BuzzPost.objects.create(text=buzz_text, employee=system_emp)
                    BuzzShare.objects.create(post=buzz_post, employee=system_emp, type='post', text=buzz_text)
                    
                    # Notificar todos os outros funcionários
                    from core.push_notifications import send_push_to_users, send_push
                    from core.models import OrangeUser
                    
                    other_users = OrangeUser.objects.filter(is_active=True).exclude(id=user.id).exclude(fcm_token='').exclude(fcm_token__isnull=True)
                    
                    job_title = employee.job_title.title if getattr(employee, 'job_title', None) else "Membro"
                    department = employee.sub_division.name if getattr(employee, 'sub_division', None) else "nossa equipe"
                    
                    if job_title.lower() == department.lower():
                        role_text = f"do(a) {department}"
                    else:
                        role_text = f"{job_title} de {department}"
                    
                    send_push_to_users(
                        other_users,
                        "Aniversariante do Dia",
                        f"Hoje é o aniversário de {employee.first_name}, {role_text}. Deixe suas felicitações no Netgram.",
                        data={'route': '/buzz/'}
                    )
                    
                    # Notificar o próprio aniversariante
                    send_push(
                        user,
                        "Feliz Aniversário",
                        f"O CDC lhe deseja um excelente dia e um próspero novo ciclo, {employee.first_name}.",
                        data={'route': '/pim/my-info/'}
                    )
                    
                except Exception as e:
                    logger.warning("Erro ao espelhar aniversário para o Buzz ou Push: %s", e)

                
                if request:
                    messages.success(request, msg)
    except Exception:
        pass 





class PasswordResetToken(models.Model):
    """Token de 6 dígitos para redefinição de senha via e-mail."""
    user       = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, related_name='reset_tokens')
    code       = models.CharField(max_length=6)           
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()                   
    used       = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Token de Redefinição de Senha'
        ordering = ['-created_at']

    def is_valid(self):
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()

    def __str__(self):
        return f"Reset {self.user.username} — {self.code}"


class AuditLog(models.Model):
    """Registra ações importantes do sistema para auditoria."""
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LEAVE_APPROVE', 'Licença Aprovada'),
        ('LEAVE_REJECT', 'Licença Rejeitada'),
        ('ADJ_APPROVE', 'Ajuste Aprovado'),
        ('ADJ_REJECT', 'Ajuste Rejeitado'),
        ('EMP_CREATE', 'Funcionário Criado'),
        ('EMP_TERMINATE', 'Funcionário Desligado'),
        ('USER_CREATE', 'Usuário Criado'),
        ('USER_EDIT', 'Usuário Editado'),
        ('OTHER', 'Outro'),
    ]

    user = models.ForeignKey(OrangeUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, default='OTHER')
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} — {self.user} — {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class Announcement(models.Model):
    """Avisos Internos exibidos no Dashboard"""
    VISIBILITY_ALL = 'ALL'
    VISIBILITY_DEPT = 'DEPARTMENT_ONLY'
    VISIBILITY_CHOICES = [
        (VISIBILITY_ALL, 'Toda a Empresa (Público Geral)'),
        (VISIBILITY_DEPT, 'Apenas Departamento/Filial'),
    ]

    title = models.CharField(max_length=200, verbose_name='Título')
    content = models.TextField(verbose_name='Conteúdo do Aviso')
    image = models.ImageField(upload_to='announcements/', blank=True, null=True, verbose_name='Foto/Capa (Opcional)')
    author = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, verbose_name='Autor')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_ALL, verbose_name='Visibilidade')
    department = models.ForeignKey('admin_app.Subunit', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Departamento Restrito')
    expires_at = models.DateField(null=True, blank=True, verbose_name='Data de Fim (Opcional)')
    
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    buzz_post_id = models.IntegerField(null=True, blank=True, verbose_name='ID do Post no Netgram')

    class Meta:
        verbose_name = 'Mural de Aviso'
        verbose_name_plural = 'Mural de Avisos'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AnnouncementLike(models.Model):
    """Curtidas (Likes) em Avisos"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, related_name='announcement_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('announcement', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.announcement.title}"


class AnnouncementComment(models.Model):
    """Comentários em Avisos"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, related_name='announcement_comments')
    text = models.TextField(verbose_name='Comentário')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.announcement.title}"

from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=Announcement)
def create_buzz_post_for_announcement(sender, instance, created, **kwargs):
    if created and getattr(instance, 'buzz_post_id', None) is None:
        try:
            from buzz.models import BuzzPost, BuzzShare, BuzzPhoto
            from pim.models import Employee
            
            author_emp = getattr(instance.author, 'employee', None)
            if not author_emp:
                author_emp, _ = Employee.objects.get_or_create(
                    employee_id='SYS-0000',
                    defaults={
                        'first_name': 'Sistema', 
                        'last_name': 'CDC',
                        'work_email': 'sistema@netline.com',
                        'is_time_tracking_exempt': True
                    }
                )
            
            buzz_text = f"📢 **COMUNICADO OFICIAL:**\n\n**{instance.title}**\n\n{instance.content}"
            buzz_post = BuzzPost.objects.create(text=buzz_text, employee=author_emp)
            
            if instance.image:
                BuzzPhoto.objects.create(post=buzz_post, photo=instance.image)
                
            BuzzShare.objects.create(post=buzz_post, employee=author_emp, type='post', text=buzz_text)
            
            
            Announcement.objects.filter(pk=instance.pk).update(buzz_post_id=buzz_post.id)
            
        except Exception as e:
            logger.warning("Erro ao espelhar comunicado para Buzz: %s", e)

        # Enviar push notification para os usuários
        try:
            from core.models import OrangeUser
            from core.push_notifications import send_push_to_users

            if instance.visibility == Announcement.VISIBILITY_ALL:
                users = OrangeUser.objects.filter(is_active=True).exclude(fcm_token='').exclude(fcm_token__isnull=True)
            else:
                users = OrangeUser.objects.filter(
                    is_active=True,
                    employee__department=instance.department
                ).exclude(fcm_token='').exclude(fcm_token__isnull=True)

            send_push_to_users(
                users,
                "Novo Comunicado Oficial",
                f"{instance.title}",
                data={'route': '/buzz/'}
            )
        except Exception as e:
            logger.warning("Erro ao enviar push de comunicado: %s", e)

@receiver(post_delete, sender=Announcement)
def delete_buzz_post_for_announcement(sender, instance, **kwargs):
    if getattr(instance, 'buzz_post_id', None):
        try:
            from buzz.models import BuzzPost
            BuzzPost.objects.filter(id=instance.buzz_post_id).delete()
        except Exception:
            pass

class AppNotification(models.Model):
    user = models.ForeignKey(OrangeUser, on_delete=models.CASCADE, related_name='app_notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    route = models.CharField(max_length=255, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notificação para {self.user.username}: {self.title}"


class GoogleIntegration(models.Model):
    user = models.OneToOneField(OrangeUser, on_delete=models.CASCADE, related_name='google_integration')
    credentials = models.JSONField(help_text="Armazena o access_token, refresh_token, token_uri, client_id, etc.")
    calendar_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID da agenda exclusiva criada para as escalas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Integração Google'
        verbose_name_plural = 'Integrações Google'

    def __str__(self):
        return f"Google Integration — {self.user.username}"
