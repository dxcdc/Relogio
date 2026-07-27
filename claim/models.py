from django.db import models


class ClaimEvent(models.Model):
    """Eventos de reembolso (ex: Viagem, Treinamento)"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Nome do Evento')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    added_by = models.ForeignKey('core.OrangeUser', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Evento de Reembolso'
        verbose_name_plural = 'Eventos de Reembolso'
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseType(models.Model):
    """Tipos de despesa (Alimentação, Transporte, etc.)"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Tipo de Despesa')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    added_by = models.ForeignKey('core.OrangeUser', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Tipo de Despesa'
        verbose_name_plural = 'Tipos de Despesa'
        ordering = ['name']

    def __str__(self):
        return self.name


class ClaimRequest(models.Model):
    """Solicitação de reembolso"""
    STATUS_INITIATED = 'INITIATED'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_SUPERVISOR_APPROVED = 'SUPERVISOR_APPROVED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_PAID = 'PAID'
    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Iniciada'),
        (STATUS_SUBMITTED, 'Enviada'),
        (STATUS_SUPERVISOR_APPROVED, 'Ag. RH/Admin'),
        (STATUS_APPROVED, 'Aprovada'),
        (STATUS_REJECTED, 'Rejeitada'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_PAID, 'Paga'),
    ]

    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE, related_name='claim_requests', verbose_name='Funcionário'
    )
    claim_event = models.ForeignKey(ClaimEvent, on_delete=models.CASCADE, verbose_name='Evento')
    currency = models.ForeignKey(
        'admin_app.CurrencyType', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Moeda'
    )
    reference_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Referência')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED, verbose_name='Status')
    submitted_date = models.DateField(null=True, blank=True, verbose_name='Data de Envio')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Motivo da Rejeição')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Solicitação de Reembolso'
        verbose_name_plural = 'Solicitações de Reembolso'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.claim_event} ({self.status})"

    @property
    def total_amount(self):
        return sum(e.amount for e in self.expenses.all() if e.amount)


class ClaimExpense(models.Model):
    """Despesa individual dentro de uma solicitação"""
    claim_request = models.ForeignKey(ClaimRequest, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE, verbose_name='Tipo de Despesa')
    expense_date = models.DateField(verbose_name='Data')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor')
    note = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['expense_date']

    def __str__(self):
        return f"{self.expense_type} - R${self.amount}"


class ClaimAttachment(models.Model):
    """Notas fiscais e anexos"""
    claim_request = models.ForeignKey(ClaimRequest, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='claim_attachments/', verbose_name='Arquivo')
    file_name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'

    def __str__(self):
        return self.file_name
