from django.db import models


class Customer(models.Model):
    """Clientes para projetos"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Nome')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    """Projetos"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='projects', verbose_name='Cliente')
    name = models.CharField(max_length=200, verbose_name='Nome do Projeto')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.customer})"


class ProjectActivity(models.Model):
    """Atividades do projeto"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities', verbose_name='Projeto')
    name = models.CharField(max_length=200, verbose_name='Atividade')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Atividade do Projeto'
        verbose_name_plural = 'Atividades do Projeto'

    def __str__(self):
        return f"{self.name} - {self.project}"


class ProjectAdmin(models.Model):
    """Administradores de projeto"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='admins')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Admin do Projeto'
        unique_together = ['project', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.project}"


class Timesheet(models.Model):
    """Timesheet semanal"""
    STATUS_NOT_SUBMITTED = 'NOT SUBMITTED'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_NOT_SUBMITTED, 'Não Enviado'),
        (STATUS_SUBMITTED, 'Enviado'),
        (STATUS_APPROVED, 'Aprovado'),
        (STATUS_REJECTED, 'Rejeitado'),
    ]

    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='timesheets')
    start_date = models.DateField(verbose_name='Início da Semana')
    end_date = models.DateField(verbose_name='Fim da Semana')
    state = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_SUBMITTED, verbose_name='Status')

    class Meta:
        verbose_name = 'Timesheet'
        verbose_name_plural = 'Timesheets'
        ordering = ['-start_date']
        unique_together = ['employee', 'start_date']

    def __str__(self):
        return f"{self.employee} - {self.start_date} a {self.end_date}"

    @property
    def total_hours(self):
        return sum(item.total_hours for item in self.items.all())


class TimesheetActionLog(models.Model):
    """Log de ações no timesheet"""
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='action_logs')
    performed_by = models.ForeignKey('core.OrangeUser', null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    comment = models.TextField(blank=True, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Ação'
        ordering = ['performed_at']

    def __str__(self):
        return f"{self.action} - {self.timesheet}"


class TimesheetItem(models.Model):
    """Item individual do timesheet (horas por dia/projeto)"""
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='items')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Projeto')
    activity = models.ForeignKey(ProjectActivity, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Atividade')
    date = models.DateField(verbose_name='Data')
    duration = models.TimeField(default='00:00', verbose_name='Horas')
    comment = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Item de Timesheet'
        verbose_name_plural = 'Itens de Timesheet'
        unique_together = ['timesheet', 'project', 'activity', 'date']

    def __str__(self):
        return f"{self.project} - {self.date}"

    @property
    def total_hours(self):
        return self.duration.hour + self.duration.minute / 60 if self.duration else 0
