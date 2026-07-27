from django.db import models
from django.utils import timezone


class WorkWeek(models.Model):
    """Configura quais dias são dias de trabalho"""
    DAY_CHOICES = [
        (0, 'Segunda'),
        (1, 'Terça'),
        (2, 'Quarta'),
        (3, 'Quinta'),
        (4, 'Sexta'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    TYPE_CHOICES = [
        ('working_day', 'Dia de Trabalho'),
        ('non_working_day', 'Folga'),
        ('half_day', 'Meio Período'),
    ]

    day = models.IntegerField(choices=DAY_CHOICES, unique=True, verbose_name='Dia')
    day_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='working_day', verbose_name='Tipo')

    class Meta:
        verbose_name = 'Semana de Trabalho'
        ordering = ['day']

    def __str__(self):
        return f"{self.get_day_display()} - {self.get_day_type_display()}"


class Holiday(models.Model):
    """Feriados"""
    name = models.CharField(max_length=200, verbose_name='Nome do Feriado')
    date = models.DateField(verbose_name='Data')
    recurring = models.BooleanField(default=False, verbose_name='Recorrente (Anual)')
    length = models.IntegerField(default=0, choices=[(0, 'Dia Inteiro'), (4, 'Meio Período')], verbose_name='Duração')
    is_global = models.BooleanField(default=True, verbose_name='Feriado Global (Todos os locais)')
    cities = models.ManyToManyField('admin_app.City', blank=True, verbose_name='Cidades (Se não for global)')

    class Meta:
        verbose_name = 'Feriado'
        verbose_name_plural = 'Feriados'
        ordering = ['date']
        indexes = [
            models.Index(fields=['date'], name='holiday_date_idx'),
        ]

    def __str__(self):
        if self.is_global:
            return f"{self.name} ({self.date}) - Global"
        return f"{self.name} ({self.date}) - Regional"


class LeaveType(models.Model):
    """Tipos de licença (Férias, Médica, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Tipo de Licença')
    is_deleted = models.BooleanField(default=False)
    operational_country = models.ForeignKey(
        'admin_app.Country', null=True, blank=True, on_delete=models.SET_NULL
    )
    leave_type_applicable_all = models.BooleanField(default=True)
    default_days = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Dias Automáticos',
        help_text='Quantos dias consecutivos o sistema deve calcular automaticamente. Ex: 3 (para Casamento).'
    )

    class Meta:
        verbose_name = 'Tipo de Licença'
        verbose_name_plural = 'Tipos de Licença'

    def __str__(self):
        return self.name


class LeaveEntitlementType(models.Model):
    """Tipo de Direito de Licença"""
    name = models.CharField(max_length=100, verbose_name='Nome')
    is_editable = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Direito'

    def __str__(self):
        return self.name


class LeaveEntitlement(models.Model):
    """Cotas de licença por funcionário"""
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='leave_entitlements')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, verbose_name='Tipo')
    entitlement_type = models.ForeignKey(LeaveEntitlementType, on_delete=models.SET_NULL, null=True)
    from_date = models.DateField(verbose_name='De')
    to_date = models.DateField(verbose_name='Até')
    no_of_days = models.DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name='Dias')
    days_used = models.DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name='Dias Usados')
    created_by = models.ForeignKey(
        'core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Direito de Licença'
        verbose_name_plural = 'Direitos de Licença'

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.no_of_days} dias)"

    @property
    def days_remaining(self):
        return self.no_of_days - self.days_used


def leave_attachment_path(instance, filename):
    nome_pasta = "desconhecido"
    if instance.employee:
        nome_pasta = instance.employee.full_name.replace(" ", "_").lower()
    return f'leave_attachments/{nome_pasta}/{filename}'

class LeaveRequest(models.Model):
    """Solicitação de licença"""
    STATUS_PENDING = 'PENDING'
    STATUS_SUPERVISOR_APPROVED = 'SUPERVISOR_APPROVED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_MORE_INFO = 'REQUESTED_MORE_INFO'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_SUPERVISOR_APPROVED, 'Ag. aprovação do RH'),
        (STATUS_APPROVED, 'Aprovada'),
        (STATUS_REJECTED, 'Rejeitada'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_MORE_INFO, 'Aguardando Informações'),
    ]

    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, verbose_name='Tipo de Licença')
    date_applied = models.DateField(default=timezone.now, verbose_name='Data da Solicitação')
    from_date = models.DateField(verbose_name='De')
    to_date = models.DateField(verbose_name='Até')
    comment = models.TextField(blank=True, null=True, verbose_name='Comentário')
    attachment = models.FileField(
        upload_to=leave_attachment_path,
        null=True, blank=True,
        verbose_name='Atestado / Documento'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Status')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Motivo da Rejeição')
    reviewed_by_supervisor = models.ForeignKey(
        'core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='supervisor_approved_leaves', verbose_name='Pré-aprovado por'
    )
    reviewed_by_hr = models.ForeignKey(
        'core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='hr_approved_leaves', verbose_name='Aprovado por (RH)'
    )
    supervisor_reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Licença'
        verbose_name_plural = 'Solicitações de Licença'
        ordering = ['-date_applied']
        indexes = [
            models.Index(fields=['employee', 'status'], name='leavereq_emp_status_idx'),
            models.Index(fields=['employee', 'date_applied'], name='leavereq_emp_date_idx'),
        ]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.from_date} a {self.to_date})"


class LeaveRequestComment(models.Model):
    """Comentários na solicitação"""
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='comments')
    created_by = models.ForeignKey('core.OrangeUser', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(verbose_name='Comentário')

    class Meta:
        verbose_name = 'Comentário'
        ordering = ['created_at']

    def __str__(self):
        return f"Comentário em {self.leave_request}"


class LeaveActionLog(models.Model):
    """Histórico de ações em uma solicitação de licença"""
    ACTION_SUBMIT = 'SUBMIT'
    ACTION_SUPERVISOR_APPROVE = 'SUPERVISOR_APPROVE'
    ACTION_HR_APPROVE = 'HR_APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_CANCEL = 'CANCEL'
    ACTION_COMMENT = 'COMMENT'

    ACTION_CHOICES = [
        (ACTION_SUBMIT, 'Solicitado'),
        (ACTION_SUPERVISOR_APPROVE, 'Pré-aprovado pelo Supervisor'),
        (ACTION_HR_APPROVE, 'Aprovado pelo RH'),
        (ACTION_REJECT, 'Rejeitado'),
        (ACTION_CANCEL, 'Cancelado'),
        (ACTION_COMMENT, 'Comentário adicionado'),
    ]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='action_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey('core.OrangeUser', null=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Ação'
        verbose_name_plural = 'Logs de Ação'
        ordering = ['performed_at']

    def __str__(self):
        return f"{self.get_action_display()} — {self.leave_request} — {self.performed_at.strftime('%d/%m/%Y %H:%M')}"


class Leave(models.Model):
    """Registro de dia individual de licença"""
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_APPROVED, 'Aprovada'),
        (STATUS_REJECTED, 'Rejeitada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]
    LENGTH_FULL = 0
    LENGTH_HALF = 4
    LENGTH_CHOICES = [(LENGTH_FULL, 'Dia Inteiro'), (LENGTH_HALF, 'Meio Período')]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='leaves')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    date = models.DateField(verbose_name='Data')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    duration_type = models.IntegerField(choices=LENGTH_CHOICES, default=LENGTH_FULL)

    class Meta:
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'
        ordering = ['date']
        indexes = [
            models.Index(fields=['employee', 'date'], name='leave_emp_date_idx'),
            models.Index(fields=['employee', 'status'], name='leave_emp_status_idx'),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date}"


class LeavePeriodHistory(models.Model):
    """Histórico de períodos de licença"""
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    start_month = models.IntegerField(default=1)
    start_day = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Período de Licença'

    def __str__(self):
        return f"Período de {self.leave_type} partir de {self.start_month}/{self.start_day}"


from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone as tz

@receiver(pre_save, sender=LeaveRequest)
def notify_leave_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = LeaveRequest.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                from core.models import Notification, OrangeUser
                from core.push_notifications import send_push, send_push_to_role
                from emails.utils import send_custom_email
                
                emp_email = getattr(instance.employee, 'work_email', None) or getattr(instance.employee, 'other_email', None)
                
                context = {
                    'first_name': instance.employee.first_name,
                    'leave_type': instance.employee.first_name, # Fallback, wait
                    'leave_type': instance.leave_type.name,
                    'from_date': instance.from_date.strftime('%d/%m/%Y'),
                    'to_date': instance.to_date.strftime('%d/%m/%Y'),
                    'status_display': dict(LeaveRequest.STATUS_CHOICES).get(instance.status, instance.status),
                    'rejection_reason': getattr(instance, 'rejection_reason', '') or ''
                }

                
                if instance.status == LeaveRequest.STATUS_SUPERVISOR_APPROVED:
                    msg = (
                        f"Licença de {instance.employee.full_name} "
                        f"({instance.leave_type.name}, {instance.from_date.strftime('%d/%m')}) "
                        f"foi aprovada pelo supervisor e aguarda sua validação."
                    )
                    hr_users = OrangeUser.objects.filter(role=OrangeUser.ROLE_HR, is_active=True)
                    for hr_user in hr_users:
                        Notification.objects.create(user=hr_user, message=msg, link=f'/leave/{instance.pk}/')
                        send_push(hr_user, "Licença Aguardando Validação", msg, data={'route': '/leave/'})

                
                elif instance.status == LeaveRequest.STATUS_APPROVED:
                    msg = f"Aprovado: Sua licença de {instance.leave_type.name} ({instance.from_date.strftime('%d/%m')}) foi aprovada pelo RH."
                    if hasattr(instance.employee, 'user') and instance.employee.user:
                        Notification.objects.create(user=instance.employee.user, message=msg, link='/leave/')
                        send_push(
                            instance.employee.user,
                            "Licença Aprovada",
                            f"Sua licença de {instance.leave_type.name} ({instance.from_date.strftime('%d/%m/%Y')}) foi aprovada.",
                            data={'route': '/leave/'}
                        )
                    
                    if emp_email:
                        send_custom_email('leave_status_update', context, emp_email)
                    
                    try:
                        from decimal import Decimal
                        num_days = (instance.to_date - instance.from_date).days + 1
                        entitlement = LeaveEntitlement.objects.filter(
                            employee=instance.employee,
                            leave_type=instance.leave_type,
                            from_date__lte=instance.from_date,
                            to_date__gte=instance.to_date,
                        ).first()
                        if entitlement:
                            entitlement.days_used = min(
                                entitlement.days_used + Decimal(num_days),
                                entitlement.no_of_days
                            )
                            entitlement.save()
                    except Exception:
                        pass

                
                elif instance.status == LeaveRequest.STATUS_REJECTED:
                    msg = f"Rejeitado: Sua licença de {instance.leave_type.name} ({instance.from_date.strftime('%d/%m')}) foi recusada."
                    if hasattr(instance.employee, 'user') and instance.employee.user:
                        Notification.objects.create(user=instance.employee.user, message=msg, link='/leave/')
                        send_push(
                            instance.employee.user,
                            "Licença Recusada",
                            f"Sua solicitação de {instance.leave_type.name} ({instance.from_date.strftime('%d/%m/%Y')}) foi recusada.",
                            data={'route': '/leave/'}
                        )
                        
                    if emp_email:
                        send_custom_email('leave_status_update', context, emp_email)
        except Exception:
            pass


@receiver(post_save, sender=LeaveRequest)
def notify_new_leave_request(sender, instance, created, **kwargs):
    """Quando uma nova solicitação é criada, notifica supervisores e RH via push."""
    if created:
        try:
            from core.models import Notification, OrangeUser
            from core.push_notifications import send_push

            msg = (
                f"{instance.employee.full_name} solicitou licença de "
                f"{instance.leave_type.name} ({instance.from_date.strftime('%d/%m')} a {instance.to_date.strftime('%d/%m')})."
            )
            
            approvers = OrangeUser.objects.filter(
                role__in=[OrangeUser.ROLE_HR, OrangeUser.ROLE_SUPERVISOR, OrangeUser.ROLE_ADMIN],
                is_active=True
            )
            for approver in approvers:
                Notification.objects.create(approver, message=msg, link=f'/leave/{instance.pk}/') if False else None
                send_push(approver, "Nova Solicitação de Licença", msg, data={'route': '/leave/'})

            
            if hasattr(instance.employee, 'user') and instance.employee.user:
                send_push(
                    instance.employee.user,
                    "Solicitação Enviada",
                    f"Sua solicitação de {instance.leave_type.name} foi enviada e está em análise.",
                    data={'route': '/leave/'}
                )
        except Exception:
            pass

@receiver(post_save, sender=LeaveRequest)
def sync_leave_objects(sender, instance, created, **kwargs):
    from datetime import timedelta
    
    if created:
        current_date = instance.from_date
        while current_date <= instance.to_date:
            Leave.objects.get_or_create(
                leave_request=instance,
                employee=instance.employee,
                leave_type=instance.leave_type,
                date=current_date,
                defaults={'status': instance.status, 'duration_type': Leave.LENGTH_FULL}
            )
            current_date += timedelta(days=1)
    else:
        instance.leaves.update(status=instance.status)
