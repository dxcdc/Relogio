from django.db import models
from django.utils import timezone
from datetime import timedelta


class WorkSchedule(models.Model):
    """Escala de trabalho — define horários e intervalos para um grupo de funcionários."""
    name = models.CharField(max_length=100, verbose_name='Nome da Escala')
    entry_time = models.TimeField(null=True, blank=True, verbose_name='(Legado) Horário de Entrada')
    exit_time = models.TimeField(null=True, blank=True, verbose_name='(Legado) Horário de Saída')
    lunch_start = models.TimeField(null=True, blank=True, verbose_name='(Legado) Início do Almoço')
    lunch_end = models.TimeField(null=True, blank=True, verbose_name='(Legado) Fim do Almoço')
    tolerance_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name='Tolerância de Atraso (min)',
        help_text='Minutos de tolerância antes de marcar como atraso'
    )
    
    work_days = models.CharField(max_length=20, default='0,1,2,3,4', null=True, blank=True, verbose_name='(Legado) Dias de Trabalho')
    saturday_entry_time = models.TimeField(null=True, blank=True, verbose_name='(Legado) Entrada no Sábado')
    saturday_exit_time  = models.TimeField(null=True, blank=True, verbose_name='(Legado) Saída no Sábado')

    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    automatic_break_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name='Intervalo Automático (min)',
        help_text='Tempo deduzido automaticamente caso o funcionário não registre a saída/retorno do intervalo.'
    )

    class Meta:
        verbose_name = 'Escala de Trabalho'
        verbose_name_plural = 'Escalas de Trabalho'
        ordering = ['name']

    @property
    def work_days_list(self):
        """Nova versão: Retorna a lista de weekdays baseados nos WorkScheduleDays ativos."""
        return list(self.days.filter(is_work_day=True).values_list('weekday', flat=True))

    def work_hours_for_weekday(self, weekday):
        """Horas líquidas de trabalho para um dia específico da semana (0=Seg, 6=Dom)."""
        day_config = self.days.filter(weekday=weekday).first()
        if not day_config or not day_config.is_work_day or not day_config.entry_time or not day_config.exit_time:
            return 0
        from datetime import datetime, date as dt_date
        today = dt_date.today()
        entry = datetime.combine(today, day_config.entry_time)
        exit_ = datetime.combine(today, day_config.exit_time)
        
        total_minutes = (exit_ - entry).total_seconds() / 60
        lunch = day_config.lunch_duration_minutes
        
        
        if self.automatic_break_minutes > 0 and lunch == 0:
            lunch = self.automatic_break_minutes
            
        return max(0, round((total_minutes - lunch) / 60, 2))

    @property
    def work_hours_per_day(self):
        """Média gasta (fallback) para exibir na UI."""
        active_days = self.days.filter(is_work_day=True)
        if not active_days.exists():
            return 0
        total = sum(self.work_hours_for_weekday(d.weekday) for d in active_days)
        return round(total / active_days.count(), 1)


    @property
    def display_hours(self):
        h = self.work_hours_per_day
        if h == int(h):
            return f"{int(h)}h/dia (média)"
        return f"{h}h/dia (média)"
        
    @property
    def display_entry(self):
        day = self.days.filter(is_work_day=True).first()
        return day.entry_time if day else self.entry_time

    @property
    def display_exit(self):
        day = self.days.filter(is_work_day=True).first()
        return day.exit_time if day else self.exit_time

    @property
    def display_lunch_start(self):
        day = self.days.filter(is_work_day=True).first()
        return day.lunch_start if day else self.lunch_start

    @property
    def display_lunch_end(self):
        day = self.days.filter(is_work_day=True).first()
        return day.lunch_end if day else self.lunch_end


class WorkScheduleDay(models.Model):
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE, related_name='days')
    weekday = models.IntegerField(verbose_name='Dia da Semana') 
    is_work_day = models.BooleanField(default=True, verbose_name='Dia de Trabalho')
    entry_time = models.TimeField(null=True, blank=True, verbose_name='Horário de Entrada')
    exit_time = models.TimeField(null=True, blank=True, verbose_name='Horário de Saída')
    lunch_start = models.TimeField(null=True, blank=True, verbose_name='Início do Almoço')
    lunch_end = models.TimeField(null=True, blank=True, verbose_name='Fim do Almoço')

    class Meta:
        ordering = ['weekday']
        unique_together = ['schedule', 'weekday']

    @property
    def lunch_duration_minutes(self):
        if self.lunch_start and self.lunch_end:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.lunch_start)
            end = datetime.combine(date.today(), self.lunch_end)
            return int((end - start).total_seconds() / 60)
        return 0


class AttendanceRecord(models.Model):
    """Registro de ponto diário, atuando como cabeçalho para Batidas N-1."""

    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now, verbose_name='Data do Ponto')

    class Meta:
        verbose_name = 'Registro de Ponto Diário'
        verbose_name_plural = 'Registros de Ponto Diários'
        ordering = ['-date']
        # Índice composto para acelerar a query do context processor (roda em toda requisição)
        indexes = [
            models.Index(fields=['employee', 'date'], name='attendance_employee_date_idx'),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date}"

    @property
    def current_state(self):
        """Retorna 'IN' se o funcionário está trabalhando (última batida IN), 'OUT' se saiu, ou None."""
        last_punch = self.punches.order_by('-timestamp_utc').first()
        if last_punch:
            return last_punch.punch_type
        return None

    @property
    def net_minutes_worked(self):
        # Usa punches prefetchados se disponível (evita query extra)
        if hasattr(self, '_prefetched_objects_cache') and 'punches' in self._prefetched_objects_cache:
            punches = sorted(list(self.punches.all()), key=lambda p: p.timestamp_user)
        else:
            punches = list(self.punches.order_by('timestamp_user'))

        minutes = 0
        last_in = None
        for p in punches:
            if p.punch_type == 'IN':
                if not last_in:
                    last_in = p.timestamp_utc
            elif p.punch_type == 'OUT':
                if last_in:
                    minutes += (p.timestamp_utc - last_in).total_seconds() / 60
                    last_in = None

        if last_in:
            if self.date == timezone.now().date():
                minutes += (timezone.now() - last_in).total_seconds() / 60

        if len(punches) <= 2:
            # Reutiliza cache injetado para evitar 5 queries ocultas por registro
            if hasattr(self, '_prefetched_work_info'):
                work_info = self._prefetched_work_info
            else:
                work_info = get_work_info_for_date(self.employee, self.date)
            auto_break = work_info.get('automatic_break_minutes', 0)
            if auto_break > 0 and minutes > auto_break:
                minutes -= auto_break

        return max(0, minutes)

    @property
    def net_hours_worked(self):
        minutes = self.net_minutes_worked
        if minutes <= 0:
            return "0h 00m"
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins:02d}m"

    @property
    def net_seconds_worked(self):
        """Retorna os segundos líquidos trabalhados com precisão total (sem truncamento de minutos).
        Usado pelo app Flutter para sincronizar o cronômetro com o servidor."""
        # Usa punches prefetchados se disponível
        if hasattr(self, '_prefetched_objects_cache') and 'punches' in self._prefetched_objects_cache:
            punches = sorted(list(self.punches.all()), key=lambda p: p.timestamp_user)
        else:
            punches = list(self.punches.order_by('timestamp_user'))

        seconds = 0
        last_in = None
        for p in punches:
            if p.punch_type == 'IN':
                if not last_in:
                    last_in = p.timestamp_utc
            elif p.punch_type == 'OUT':
                if last_in:
                    seconds += (p.timestamp_utc - last_in).total_seconds()
                    last_in = None
        if last_in:
            if self.date == timezone.now().date():
                seconds += (timezone.now() - last_in).total_seconds()

        if len(punches) <= 2:
            # Reutiliza cache injetado para evitar 5 queries ocultas por registro
            if hasattr(self, '_prefetched_work_info'):
                work_info = self._prefetched_work_info
            else:
                work_info = get_work_info_for_date(self.employee, self.date)
            auto_break = work_info.get('automatic_break_minutes', 0)
            if auto_break > 0 and seconds > auto_break * 60:
                seconds -= auto_break * 60

        return max(0, int(seconds))

    @property
    def total_extra_formatted(self):
        if hasattr(self, 'dailytimebalance'):
            dtb = self.dailytimebalance
            total = dtb.extra_60_minutes + dtb.extra_100_minutes
            if total > 0:
                hours = int(total // 60)
                mins = int(total % 60)
                return f"{hours}h {mins:02d}m"
        return "0h 00m"

    @property
    def is_late(self):
        # Otimização: verifica se punches já estão em memória via prefetch_related
        if hasattr(self, '_prefetched_objects_cache') and 'punches' in self._prefetched_objects_cache:
            punches = [p for p in self.punches.all() if p.punch_type == 'IN']
            punches.sort(key=lambda x: x.timestamp_user)
            first_in = punches[0] if punches else None
        else:
            first_in = self.punches.filter(punch_type='IN').order_by('timestamp_user').first()

        if not first_in or not first_in.timestamp_user:
            return False
            
        # Otimização: verifica se work_info foi injetado (bulk cache)
        if hasattr(self, '_prefetched_work_info'):
            work_info = self._prefetched_work_info
        else:
            work_info = get_work_info_for_date(self.employee, self.date)
            
        if not work_info.get('is_work_day') or not work_info.get('entry_time'):
            return False
            
        from datetime import datetime, timedelta
        expected = datetime.combine(self.date, work_info['entry_time'])
        
        tolerance_minutes = 15 
        # Tenta ler a tolerância sem bater no banco (caso schedule_obj exista no cache)
        if hasattr(self.employee, 'work_schedule') and self.employee.work_schedule:
            tolerance_minutes = getattr(self.employee.work_schedule, 'tolerance_minutes', 15)
            
        tolerance = timedelta(minutes=tolerance_minutes)
        actual = first_in.timestamp_user.replace(tzinfo=None)
        return actual > (expected + tolerance)


class AttendancePunch(models.Model):
    """Uma batida de ponto isolada e flexível (Entrada ou Saída)."""
    PUNCH_IN = 'IN'
    PUNCH_OUT = 'OUT'
    PUNCH_TYPE_CHOICES = [
        (PUNCH_IN, 'Entrada/Retorno (Iniciar)'),
        (PUNCH_OUT, 'Saída/Pausa (Pausar)'),
    ]

    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='punches')
    punch_type = models.CharField(max_length=10, choices=PUNCH_TYPE_CHOICES, verbose_name='Ação')
    
    timestamp_utc = models.DateTimeField(verbose_name='Horário (UTC)')
    timestamp_user = models.DateTimeField(verbose_name='Horário (Local)')
    note = models.TextField(blank=True, null=True, verbose_name='Observação')
    photo = models.ImageField(upload_to='attendance_photos/', null=True, blank=True, verbose_name='Foto Capturada')
    
    
    latitude = models.FloatField(null=True, blank=True, verbose_name='Latitude')
    longitude = models.FloatField(null=True, blank=True, verbose_name='Longitude')
    ip_address = models.CharField(max_length=50, blank=True, null=True, verbose_name='IP')
    location_address = models.TextField(blank=True, null=True, verbose_name='Endereço Aproximado')
    
    is_flagged_location = models.BooleanField(default=False, verbose_name='Fora do Local Autorizado')
    fraud_reason = models.TextField(blank=True, null=True, verbose_name='Detalhes de Fraude')

    class Meta:
        verbose_name = 'Batida de Ponto'
        verbose_name_plural = 'Batidas de Ponto'
        ordering = ['timestamp_utc']

    def __str__(self):
        return f"{self.get_punch_type_display()} - {self.attendance_record.employee} em {self.timestamp_user.strftime('%d/%m/%Y %H:%M')}"


class AttendanceAdjustment(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SUPERVISOR_APPROVED = 'SUPERVISOR_APPROVED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_SUPERVISOR_APPROVED, 'Ag. RH'),
        (STATUS_APPROVED, 'Aprovado'),
        (STATUS_REJECTED, 'Rejeitado')
    ]

    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='attendance_adjustments')
    attendance_record = models.ForeignKey(AttendanceRecord, null=True, blank=True, on_delete=models.SET_NULL, related_name='adjustments')
    date = models.DateField(verbose_name='Data do Ajuste')
    
    requested_punches = models.JSONField(default=list, verbose_name='Horários Solicitados')
    
    reason = models.TextField(verbose_name='Motivo do Ajuste')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL)
    review_note = models.TextField(blank=True, null=True, verbose_name='Nota de Revisão')

    class Meta:
        verbose_name = 'Solicitação de Ajuste'
        verbose_name_plural = 'Solicitações de Ajuste'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ajuste de {self.employee} - {self.date} ({self.get_status_display()})"







class ShiftPattern(models.Model):
    """Padrão de turno — pode ser semanal (dias fixos) ou livre (ciclo rotativo)."""
    TYPE_WEEKLY = 'WEEKLY'
    TYPE_FREE   = 'FREE'
    TYPE_CHOICES = [
        (TYPE_WEEKLY, 'Padrão Semanal'),
        (TYPE_FREE,   'Padrão Livre'),
    ]

    name         = models.CharField(max_length=100, verbose_name='Nome do Padrão')
    pattern_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipo')
    description  = models.TextField(blank=True, verbose_name='Descrição')
    is_active    = models.BooleanField(default=True, verbose_name='Ativo')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Padrão de Turno'
        verbose_name_plural = 'Padrões de Turno'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_pattern_type_display()})"

    @property
    def cycle_length(self):
        return self.days.count()

    @property
    def work_days_count(self):
        return self.days.filter(is_work_day=True).count()

    @property
    def rest_days_count(self):
        return self.days.filter(is_work_day=False).count()


class ShiftPatternDay(models.Model):
    """Um dia dentro de um padrão de turno.
    - WEEKLY: position = dia da semana (0=Seg ... 6=Dom)
    - FREE:   position = índice no ciclo (0, 1, 2 ... N-1)
    """
    pattern     = models.ForeignKey(ShiftPattern, on_delete=models.CASCADE, related_name='days')
    position    = models.PositiveIntegerField(verbose_name='Posição no Ciclo')
    is_work_day = models.BooleanField(default=True, verbose_name='Dia de Trabalho')
    entry_time  = models.TimeField(null=True, blank=True, verbose_name='Entrada')
    exit_time   = models.TimeField(null=True, blank=True, verbose_name='Saída')

    class Meta:
        ordering = ['position']
        unique_together = ['pattern', 'position']
        verbose_name = 'Dia do Padrão'
        verbose_name_plural = 'Dias do Padrão'

    def __str__(self):
        label = 'Trabalho' if self.is_work_day else 'Folga'
        return f"{self.pattern.name} — Dia {self.position + 1} ({label})"

    @property
    def theo_minutes(self):
        """Minutos teóricos de trabalho neste dia."""
        if not self.is_work_day or not self.entry_time or not self.exit_time:
            return 0
        from datetime import datetime, date
        e = datetime.combine(date.today(), self.entry_time)
        x = datetime.combine(date.today(), self.exit_time)
        return max(0, (x - e).total_seconds() / 60)

    @property
    def weekday_name(self):
        """Apenas para padrões WEEKLY — retorna nome do dia da semana."""
        names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return names[self.position] if 0 <= self.position <= 6 else f'Dia {self.position}'


class WorkScheduleAssignment(models.Model):
    """Histórico inteligente de Escalas de Trabalho para um funcionário."""
    from pim.models import Employee as _Employee
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='schedule_assignments', verbose_name='Funcionário'
    )
    schedule = models.ForeignKey(
        'attendance.WorkSchedule', on_delete=models.PROTECT,
        verbose_name='Escala de Trabalho'
    )
    start_date = models.DateField(default=timezone.now, verbose_name='Data de Início')
    end_date = models.DateField(null=True, blank=True, verbose_name='Data de Fim')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Designação de Escala'
        verbose_name_plural = 'Designações de Escalas'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'start_date'], name='wschedassign_emp_start_idx'),
        ]

    def __str__(self):
        return f"{self.employee} → {self.schedule.name} ({self.start_date} até {self.end_date or 'Atual'})"


class EmployeeShiftAssignment(models.Model):
    """Atribui um padrão de turno a um funcionário, com data de início (e fim opcional)."""
    from pim.models import Employee as _Employee  
    employee   = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='shift_assignments', verbose_name='Funcionário'
    )
    pattern    = models.ForeignKey(
        ShiftPattern, on_delete=models.PROTECT,
        related_name='assignments', verbose_name='Padrão de Turno'
    )
    start_date = models.DateField(verbose_name='Data de Início do Ciclo')
    end_date   = models.DateField(null=True, blank=True, verbose_name='Data de Fim (opcional)')
    notes      = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Atribuição de Turno'
        verbose_name_plural = 'Atribuições de Turno'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'start_date'], name='shiftassign_emp_start_idx'),
        ]

    def __str__(self):
        return f"{self.employee} → {self.pattern.name} (desde {self.start_date})"


class ShiftOverride(models.Model):
    """Exceção de turno pontual (ex: troca de plantão no fim de semana)."""
    from pim.models import Employee as _Employee
    
    TYPE_WORK = 'WORK'
    TYPE_REST = 'REST'
    TYPE_CHOICES = [
        (TYPE_WORK, 'Dia de Trabalho'),
        (TYPE_REST, 'Dia de Folga'),
    ]

    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='shift_overrides', verbose_name='Funcionário'
    )
    date = models.DateField(verbose_name='Data da Exceção')
    override_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipo de Exceção')
    entry_time = models.TimeField(null=True, blank=True, verbose_name='Entrada')
    exit_time = models.TimeField(null=True, blank=True, verbose_name='Saída')
    reason = models.CharField(max_length=200, blank=True, verbose_name='Motivo')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Exceção de Turno'
        verbose_name_plural = 'Exceções de Turno'
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"Exceção: {self.employee} em {self.date} ({self.get_override_type_display()})"

    @property
    def theo_minutes(self):
        """Minutos teóricos da exceção."""
        if self.override_type == self.TYPE_REST or not self.entry_time or not self.exit_time:
            return 0
        from datetime import datetime, date
        e = datetime.combine(date.today(), self.entry_time)
        x = datetime.combine(date.today(), self.exit_time)
        return max(0, (x - e).total_seconds() / 60)


class DailyWorkSummary(models.Model):
    """Tabela de resumo diário pré-computada — equivalente a uma Materialized View.

    Substituição definitiva de get_work_info_for_date_range:
    Uma única query indexada em vez de 5-6 queries com JOINs por requisição.

    Funcionamento:
        1ª consulta → computa normalmente (5 queries) → persiste aqui
        2ª+ consulta → lê desta tabela (1 query) → retorna instantaneamente

    Invalidação automática via sinais Django quando:
        - Leave é aprovada/cancelada      - ShiftOverride muda
        - WorkScheduleAssignment muda     - EmployeeShiftAssignment muda
        - Holiday é criada/alterada

    Para popular em produção (executar 1x):
        python manage.py rebuild_work_summaries --months=6
    """
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='daily_summaries', db_index=False  # coberto pelo índice composto
    )
    date = models.DateField()
    is_work_day = models.BooleanField(default=True)
    entry_time = models.TimeField(null=True, blank=True)
    exit_time = models.TimeField(null=True, blank=True)
    theo_minutes = models.FloatField(default=0)
    source = models.CharField(max_length=30, default='default')
    title = models.CharField(max_length=200, blank=True)
    tolerance_minutes = models.SmallIntegerField(default=15)
    automatic_break_minutes = models.SmallIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['employee', 'date'], name='dailyworksum_emp_date_idx'),
        ]
        verbose_name = 'Resumo Diário de Trabalho'
        verbose_name_plural = 'Resumos Diários de Trabalho'

    def __str__(self):
        return f"{self.employee} | {self.date} | {'Trabalho' if self.is_work_day else 'Folga'} | {self.source}"


class MonthlyAttendanceSummary(models.Model):
    """Totais mensais pré-computados por funcionário.

    Armazena o resultado do loop de cálculo do banco de horas para um mês inteiro,
    eliminando a necessidade de iterar todos os registros e batidas a cada acesso.

    Powered by: time_bank_modal, relatórios HR, cálculo de folha de pagamento.

    Invalidação automática via sinais quando:
        - AttendancePunch é adicionado/removido
        - DailyTimeBalance muda
        - DailyWorkSummary do mês é atualizado

    Para popular (executar 1x):
        python manage.py rebuild_monthly_summaries --months=6
    """
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='monthly_summaries', db_index=False
    )
    year = models.SmallIntegerField()
    month = models.SmallIntegerField()

    # Minutos trabalhados vs esperados
    worked_minutes = models.IntegerField(default=0)
    expected_minutes = models.IntegerField(default=0)
    balance_minutes = models.IntegerField(default=0)   # worked - expected (pode ser negativo)
    extra_minutes = models.IntegerField(default=0)     # saldo positivo acumulado
    deficit_minutes = models.IntegerField(default=0)   # saldo negativo acumulado (valor absoluto)

    # Contadores de dias
    days_worked = models.SmallIntegerField(default=0)
    late_days = models.SmallIntegerField(default=0)
    absence_days = models.SmallIntegerField(default=0)

    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'year', 'month']
        indexes = [
            models.Index(fields=['employee', 'year', 'month'], name='monthlyattsum_emp_ym_idx'),
        ]
        verbose_name = 'Resumo Mensal de Presenca'
        verbose_name_plural = 'Resumos Mensais de Presenca'

    def __str__(self):
        return f"{self.employee} | {self.year}/{self.month:02d} | {self.balance_minutes:+d}min"

    @property
    def balance_str(self):
        sign = '+' if self.balance_minutes >= 0 else '-'
        m = abs(self.balance_minutes)
        return f"{sign}{m // 60:02d}h{m % 60:02d}m"


def _get_work_info_uncached(employee, target_date):

    """Implementação interna — use get_work_info_for_date() que tem cache de 5 minutos."""
    from django.db.models import Q

    override = ShiftOverride.objects.filter(employee=employee, date=target_date).first()
    if override:
        return {
            'is_work_day'  : override.override_type == ShiftOverride.TYPE_WORK,
            'entry_time'   : override.entry_time,
            'exit_time'    : override.exit_time,
            'theo_minutes' : override.theo_minutes,
            'tolerance_minutes': 0,
            'source'       : 'shift_override',
            'title'        : override.reason or (f'Trabalho Extra' if override.override_type == ShiftOverride.TYPE_WORK else 'Folga Extra'),
        }

    from leave.models import Leave, Holiday
    approved_leave = Leave.objects.filter(
        employee=employee,
        date=target_date
    ).exclude(status__in=[Leave.STATUS_REJECTED, Leave.STATUS_CANCELLED]).select_related('leave_type').first()
    if approved_leave:
        theo_min = 0 if approved_leave.duration_type == Leave.LENGTH_FULL else 240
        return {
            'is_work_day': approved_leave.duration_type != Leave.LENGTH_FULL,
            'entry_time': None,
            'exit_time': None,
            'theo_minutes': theo_min,
            'tolerance_minutes': 0,
            'source': 'leave',
            'title': approved_leave.leave_type.name,
        }

    base_query = Q(date=target_date) | Q(recurring=True, date__month=target_date.month, date__day=target_date.day)
    holidays = Holiday.objects.filter(base_query)

    if employee.city_id:
        holidays = holidays.filter(Q(is_global=True) | Q(cities__id=employee.city_id))
    else:
        holidays = holidays.filter(is_global=True)

    first_h = holidays.first()
    if first_h:
        theo_min = 0 if first_h.length == 0 else 240
        return {
            'is_work_day': first_h.length != 0,
            'entry_time': None,
            'exit_time': None,
            'theo_minutes': theo_min,
            'tolerance_minutes': 0,
            'source': 'holiday',
            'title': first_h.name,
        }

    assignment = EmployeeShiftAssignment.objects.filter(
        employee=employee,
        start_date__lte=target_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
    ).order_by('-start_date').first()

    if assignment:
        pattern = assignment.pattern
        days    = pattern.days.all()
        day_obj = None

        if pattern.pattern_type == ShiftPattern.TYPE_WEEKLY:
            day_obj = days.filter(position=target_date.weekday()).first()
        else:
            total = days.count()
            if total > 0:
                elapsed  = (target_date - assignment.start_date).days
                if elapsed >= 0:
                    pos     = elapsed % total
                    day_obj = days.filter(position=pos).first()

        if day_obj is not None:
            return {
                'is_work_day'  : day_obj.is_work_day,
                'entry_time'   : day_obj.entry_time,
                'exit_time'    : day_obj.exit_time,
                'theo_minutes' : day_obj.theo_minutes,
                'tolerance_minutes': 15,
                'source'       : 'shift_pattern',
            }

    hist_assignment = WorkScheduleAssignment.objects.filter(
        employee=employee,
        start_date__lte=target_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
    ).order_by('-start_date').first()

    if hist_assignment:
        schedule = hist_assignment.schedule
    else:
        schedule = getattr(employee, 'work_schedule', None)

    if schedule:
        day_config = schedule.days.filter(weekday=target_date.weekday()).first()
        if day_config and day_config.is_work_day:
            # Calcula theo_minutes inline — evita query extra de work_hours_for_weekday()
            _e, _x = day_config.entry_time, day_config.exit_time
            if _e and _x:
                from datetime import datetime, date as _dt
                _td = _dt.today()
                _mins = (datetime.combine(_td, _x) - datetime.combine(_td, _e)).total_seconds() / 60
                _lunch = day_config.lunch_duration_minutes
                if schedule.automatic_break_minutes > 0 and _lunch == 0:
                    _lunch = schedule.automatic_break_minutes
                _theo = max(0, _mins - _lunch)
            else:
                _theo = 0
            return {
                'is_work_day'  : True,
                'entry_time'   : day_config.entry_time,
                'exit_time'    : day_config.exit_time,
                'theo_minutes' : _theo,
                'automatic_break_minutes': schedule.automatic_break_minutes,
                'tolerance_minutes': getattr(schedule, 'tolerance_minutes', 15),
                'source'       : 'work_schedule',
            }
        return {'is_work_day': False, 'entry_time': None, 'exit_time': None,
                'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'work_schedule'}

    if target_date.weekday() < 5:
        return {'is_work_day': True, 'entry_time': None, 'exit_time': None,
                'theo_minutes': 480, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}
    return {'is_work_day': False, 'entry_time': None, 'exit_time': None,
            'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}


def get_work_info_for_date(employee, target_date):
    """Retorna informações de trabalho para um funcionário em uma data específica.

    Returns dict:
        {
          'is_work_day': bool,
          'entry_time': time | None,
          'exit_time': time | None,
          'theo_minutes': float,
          'source': 'shift_pattern' | 'work_schedule' | 'default'
        }

    Prioridade: ShiftOverride → ShiftPattern → WorkSchedule → Default (Seg-Sex, 8h)

    PERFORMANCE: Cache de 5 minutos por funcionário+data.
    Dados de escala são estáveis no dia — mudam raramente.
    O cache é automaticamente expirado quando punch_action invalida punch_ctx.
    """
    from django.core.cache import cache as _cache
    _ck = f'work_info_{employee.pk}_{target_date}'
    _cached = _cache.get(_ck)
    if _cached is not None:
        return _cached
    _result = _get_work_info_uncached(employee, target_date)
    _cache.set(_ck, _result, 300)  # 5 minutos — seguro para dados de escala
    return _result




def _compute_work_info_range(employee, start_date, end_date):
    """
    Implementação interna — 5 queries para carregar todos os dados do período.
    Use get_work_info_for_date_range() que adiciona cache persistente via DailyWorkSummary.
    Retorna um dicionário: {data: work_info_dict}
    """
    from django.db.models import Q
    from datetime import timedelta
    from leave.models import Leave, Holiday

    # 1. Overrides
    overrides_qs = ShiftOverride.objects.filter(employee=employee, date__range=[start_date, end_date])
    overrides = {o.date: o for o in overrides_qs}

    # 2. Leaves
    leaves_qs = Leave.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    ).exclude(status__in=[Leave.STATUS_REJECTED, Leave.STATUS_CANCELLED]).select_related('leave_type')
    leaves = {l.date: l for l in leaves_qs}

    # 3. Holidays
    holidays_qs = Holiday.objects.filter(
        Q(date__range=[start_date, end_date]) | Q(recurring=True)
    )
    if employee.city_id:
        holidays_qs = holidays_qs.filter(Q(is_global=True) | Q(cities__id=employee.city_id))
    else:
        holidays_qs = holidays_qs.filter(is_global=True)

    holidays_list = list(holidays_qs)

    # 4. Shift Assignments
    assignments = list(EmployeeShiftAssignment.objects.filter(
        employee=employee,
        start_date__lte=end_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=start_date)
    ).select_related('pattern').prefetch_related('pattern__days').order_by('-start_date'))

    # 5. Work Schedule Assignments
    hist_assignments = list(WorkScheduleAssignment.objects.filter(
        employee=employee,
        start_date__lte=end_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=start_date)
    ).select_related('schedule').prefetch_related('schedule__days').order_by('-start_date'))

    default_schedule = getattr(employee, 'work_schedule', None)

    # Pré-computa days de cada schedule e pattern para evitar queries repetidas dentro do loop
    schedule_days_map = {}
    for _a in hist_assignments:
        _sid = getattr(_a, 'schedule_id', None)
        if _sid is not None and _sid not in schedule_days_map:
            schedule_days_map[_sid] = list(_a.schedule.days.all())  # usa prefetch cache
    if default_schedule and default_schedule.pk not in schedule_days_map:
        schedule_days_map[default_schedule.pk] = list(default_schedule.days.all())

    pattern_days_map = {}
    for _a in assignments:
        _pid = getattr(_a, 'pattern_id', None)
        if _pid is not None and _pid not in pattern_days_map:
            pattern_days_map[_pid] = list(_a.pattern.days.all())  # usa prefetch cache

    def get_info_for_day(target_date):
        # Override
        if target_date in overrides:
            o = overrides[target_date]
            return {
                'is_work_day'  : o.override_type == ShiftOverride.TYPE_WORK,
                'entry_time'   : o.entry_time,
                'exit_time'    : o.exit_time,
                'theo_minutes' : o.theo_minutes,
                'tolerance_minutes': 0,
                'source'       : 'shift_override',
                'title'        : o.reason or (f'Trabalho Extra' if o.override_type == ShiftOverride.TYPE_WORK else 'Folga Extra'),
            }
            
        # Leave
        if target_date in leaves:
            l = leaves[target_date]
            theo_min = 0 if l.duration_type == Leave.LENGTH_FULL else 240
            return {
                'is_work_day': l.duration_type != Leave.LENGTH_FULL,
                'entry_time': None,
                'exit_time': None,
                'theo_minutes': theo_min,
                'tolerance_minutes': 0,
                'source': 'leave',
                'title': l.leave_type.name,
            }
            
        # Holiday
        first_h = None
        for h in holidays_list:
            if h.date == target_date or (h.recurring and h.date.month == target_date.month and h.date.day == target_date.day):
                first_h = h
                break
        if first_h:
            theo_min = 0 if first_h.length == 0 else 240
            return {
                'is_work_day': first_h.length != 0,
                'entry_time': None,
                'exit_time': None,
                'theo_minutes': theo_min,
                'tolerance_minutes': 0,
                'source': 'holiday',
                'title': first_h.name,
            }
            
        # Assignment
        assignment = next((a for a in assignments if a.start_date <= target_date and (a.end_date is None or a.end_date >= target_date)), None)
        if assignment:
            pattern = assignment.pattern
            days = pattern_days_map.get(getattr(pattern, 'id', None), list(pattern.days.all()))
            day_obj = None
            if pattern.pattern_type == ShiftPattern.TYPE_WEEKLY:
                day_obj = next((d for d in days if d.position == target_date.weekday()), None)
            else:
                total = len(days)
                if total > 0:
                    elapsed = (target_date - assignment.start_date).days
                    if elapsed >= 0:
                        pos = elapsed % total
                        day_obj = next((d for d in days if d.position == pos), None)
            if day_obj:
                return {
                    'is_work_day'  : day_obj.is_work_day,
                    'entry_time'   : day_obj.entry_time,
                    'exit_time'    : day_obj.exit_time,
                    'theo_minutes' : day_obj.theo_minutes,
                    'tolerance_minutes': 15,
                    'source'       : 'shift_pattern',
                }
                
        # Hist Assignment
        hist_assignment = next((a for a in hist_assignments if a.start_date <= target_date and (a.end_date is None or a.end_date >= target_date)), None)
        schedule = hist_assignment.schedule if hist_assignment else default_schedule
        if schedule:
            s_days = schedule_days_map.get(getattr(schedule, 'pk', None), list(schedule.days.all()))
            day_config = next((d for d in s_days if d.weekday == target_date.weekday()), None)
            if day_config and day_config.is_work_day:
                # Calculo in-memory para evitar bater no banco em schedule.work_hours_for_weekday()
                theo_min = 0
                if day_config.entry_time and day_config.exit_time:
                    from datetime import datetime, date as dt_date
                    today_dt = dt_date.today()
                    entry = datetime.combine(today_dt, day_config.entry_time)
                    exit_ = datetime.combine(today_dt, day_config.exit_time)
                    total_minutes = (exit_ - entry).total_seconds() / 60
                    lunch = day_config.lunch_duration_minutes
                    if schedule.automatic_break_minutes > 0 and lunch == 0:
                        lunch = schedule.automatic_break_minutes
                    theo_min = max(0, total_minutes - lunch)

                return {
                    'is_work_day'  : True,
                    'entry_time'   : day_config.entry_time,
                    'exit_time'    : day_config.exit_time,
                    'theo_minutes' : theo_min,
                    'automatic_break_minutes': schedule.automatic_break_minutes,
                    'tolerance_minutes': getattr(schedule, 'tolerance_minutes', 15),
                    'source'       : 'work_schedule',
                }
            return {'is_work_day': False, 'entry_time': None, 'exit_time': None,
                    'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'work_schedule'}
                    
        # Default
        if target_date.weekday() < 5:
            return {'is_work_day': True, 'entry_time': None, 'exit_time': None,
                    'theo_minutes': 480, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}
        return {'is_work_day': False, 'entry_time': None, 'exit_time': None,
                'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}

    results = {}
    cur_date = start_date
    while cur_date <= end_date:
        results[cur_date] = get_info_for_day(cur_date)
        cur_date += timedelta(days=1)

    return results


def get_work_info_for_date_range(employee, start_date, end_date):
    """
    Versão com cache persistente via DailyWorkSummary (materialized view).

    PERFORMANCE:
        1ª chamada → 5 queries (computa) + 1 bulk insert (persiste)
        2ª+ chamada → 1 query indexada (DailyWorkSummary) — instantâneo

    Invalidação automática via sinais quando Leave, ShiftOverride,
    WorkScheduleAssignment, EmployeeShiftAssignment ou Holiday mudam.

    Para pré-popular todo o histórico:
        python manage.py rebuild_work_summaries --months=6
    """
    from datetime import timedelta

    # 1. Tenta carregar tudo do cache persistente (1 query indexada)
    summaries = DailyWorkSummary.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    ).values('date', 'is_work_day', 'entry_time', 'exit_time', 'theo_minutes',
             'source', 'title', 'tolerance_minutes', 'automatic_break_minutes')

    result = {}
    for row in summaries:
        result[row['date']] = {
            'is_work_day': row['is_work_day'],
            'entry_time': row['entry_time'],
            'exit_time': row['exit_time'],
            'theo_minutes': row['theo_minutes'],
            'source': row['source'],
            'title': row['title'] or '',
            'tolerance_minutes': row['tolerance_minutes'],
            'automatic_break_minutes': row['automatic_break_minutes'],
        }

    # 2. Encontra datas ainda não no cache
    missing = []
    cur = start_date
    while cur <= end_date:
        if cur not in result:
            missing.append(cur)
        cur += timedelta(days=1)

    if not missing:
        return result  # 100% cache hit — 1 única query!

    # 3. Computa datas faltando (5 queries para o range)
    computed = _compute_work_info_range(employee, min(missing), max(missing))

    # 4. Persiste no cache para futuras requisições (bulk insert)
    to_create = []
    for d in missing:
        info = computed.get(d)
        if info is not None:
            to_create.append(DailyWorkSummary(
                employee=employee,
                date=d,
                is_work_day=info.get('is_work_day', False),
                entry_time=info.get('entry_time'),
                exit_time=info.get('exit_time'),
                theo_minutes=info.get('theo_minutes', 0),
                source=info.get('source', 'default'),
                title=info.get('title', '') or '',
                tolerance_minutes=info.get('tolerance_minutes', 15),
                automatic_break_minutes=info.get('automatic_break_minutes', 0),
            ))
    if to_create:
        try:
            DailyWorkSummary.objects.bulk_create(to_create, ignore_conflicts=True)
        except Exception:
            pass  # Falha silenciosa — dados serão recomputados na próxima vez

    result.update(computed)
    return result


def get_work_info_for_date_bulk(employees, target_date):
    """
    Versão bulk para otimização do painel (dashboard) e relatórios diários.
    Busca regras de uma lista de funcionários para UMA data em O(1) queries.
    Retorna um dicionário: {employee_id: work_info_dict}
    """
    from django.db.models import Q
    from leave.models import Leave, Holiday
    
    emp_ids = [e.id if hasattr(e, 'id') else e for e in employees]
    if not emp_ids:
        return {}

    # 1. Overrides
    overrides_qs = ShiftOverride.objects.filter(employee_id__in=emp_ids, date=target_date)
    overrides = {o.employee_id: o for o in overrides_qs}

    # 2. Leaves
    leaves_qs = Leave.objects.filter(
        employee_id__in=emp_ids,
        date=target_date
    ).exclude(status__in=[Leave.STATUS_REJECTED, Leave.STATUS_CANCELLED]).select_related('leave_type')
    leaves = {l.employee_id: l for l in leaves_qs}

    # 3. Holidays
    holidays_qs = Holiday.objects.filter(
        Q(date=target_date) | Q(recurring=True, date__month=target_date.month, date__day=target_date.day)
    ).prefetch_related('cities')
    holidays_list = list(holidays_qs)

    # 4. Shift Assignments
    assignments = list(EmployeeShiftAssignment.objects.filter(
        employee_id__in=emp_ids,
        start_date__lte=target_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
    ).select_related('pattern').prefetch_related('pattern__days').order_by('-start_date'))
    
    # 5. Work Schedule Assignments
    hist_assignments = list(WorkScheduleAssignment.objects.filter(
        employee_id__in=emp_ids,
        start_date__lte=target_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
    ).select_related('schedule').prefetch_related('schedule__days').order_by('-start_date'))

    results = {}
    
    for emp in employees:
        emp_id = emp.id if hasattr(emp, 'id') else emp
        
        # Override
        if emp_id in overrides:
            o = overrides[emp_id]
            results[emp_id] = {
                'is_work_day'  : o.override_type == ShiftOverride.TYPE_WORK,
                'entry_time'   : o.entry_time,
                'exit_time'    : o.exit_time,
                'theo_minutes' : o.theo_minutes,
                'tolerance_minutes': 0,
                'source'       : 'shift_override',
                'title'        : o.reason or (f'Trabalho Extra' if o.override_type == ShiftOverride.TYPE_WORK else 'Folga Extra'),
            }
            continue
            
        # Leave
        if emp_id in leaves:
            l = leaves[emp_id]
            theo_min = 0 if l.duration_type == Leave.LENGTH_FULL else 240
            results[emp_id] = {
                'is_work_day': l.duration_type != Leave.LENGTH_FULL,
                'entry_time': None,
                'exit_time': None,
                'theo_minutes': theo_min,
                'tolerance_minutes': 0,
                'source': 'leave',
                'title': l.leave_type.name,
            }
            continue
            
        # Holiday
        first_h = None
        for h in holidays_list:
            if h.is_global or (hasattr(emp, 'city_id') and emp.city_id and h.cities.filter(id=emp.city_id).exists()):
                first_h = h
                break
        if first_h:
            theo_min = 0 if first_h.length == 0 else 240
            results[emp_id] = {
                'is_work_day': first_h.length != 0,
                'entry_time': None,
                'exit_time': None,
                'theo_minutes': theo_min,
                'tolerance_minutes': 0,
                'source': 'holiday',
                'title': first_h.name,
            }
            continue
            
        # Assignment
        assignment = next((a for a in assignments if a.employee_id == emp_id and a.start_date <= target_date and (a.end_date is None or a.end_date >= target_date)), None)
        if assignment:
            pattern = assignment.pattern
            days = list(pattern.days.all())
            day_obj = None
            if pattern.pattern_type == ShiftPattern.TYPE_WEEKLY:
                day_obj = next((d for d in days if d.position == target_date.weekday()), None)
            else:
                total = len(days)
                if total > 0:
                    elapsed = (target_date - assignment.start_date).days
                    if elapsed >= 0:
                        pos = elapsed % total
                        day_obj = next((d for d in days if d.position == pos), None)
            if day_obj:
                results[emp_id] = {
                    'is_work_day'  : day_obj.is_work_day,
                    'entry_time'   : day_obj.entry_time,
                    'exit_time'    : day_obj.exit_time,
                    'theo_minutes' : day_obj.theo_minutes,
                    'tolerance_minutes': 15,
                    'source'       : 'shift_pattern',
                }
                continue
                
        # Hist Assignment
        hist_assignment = next((a for a in hist_assignments if a.employee_id == emp_id and a.start_date <= target_date and (a.end_date is None or a.end_date >= target_date)), None)
        schedule = hist_assignment.schedule if hist_assignment else getattr(emp, 'work_schedule', None)
        if schedule:
            s_days = list(schedule.days.all())
            day_config = next((d for d in s_days if d.weekday == target_date.weekday()), None)
            if day_config and day_config.is_work_day:
                theo_min = 0
                if day_config.entry_time and day_config.exit_time:
                    from datetime import datetime, date as dt_date
                    today_dt = dt_date.today()
                    entry = datetime.combine(today_dt, day_config.entry_time)
                    exit_ = datetime.combine(today_dt, day_config.exit_time)
                    total_minutes = (exit_ - entry).total_seconds() / 60
                    lunch = day_config.lunch_duration_minutes
                    if schedule.automatic_break_minutes > 0 and lunch == 0:
                        lunch = schedule.automatic_break_minutes
                    theo_min = max(0, total_minutes - lunch)

                results[emp_id] = {
                    'is_work_day'  : True,
                    'entry_time'   : day_config.entry_time,
                    'exit_time'    : day_config.exit_time,
                    'theo_minutes' : theo_min,
                    'automatic_break_minutes': schedule.automatic_break_minutes,
                    'tolerance_minutes': getattr(schedule, 'tolerance_minutes', 15),
                    'source'       : 'work_schedule',
                }
                continue
            results[emp_id] = {'is_work_day': False, 'entry_time': None, 'exit_time': None,
                    'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'work_schedule'}
            continue
                    
        # Default
        if target_date.weekday() < 5:
            results[emp_id] = {'is_work_day': True, 'entry_time': None, 'exit_time': None,
                    'theo_minutes': 480, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}
        else:
            results[emp_id] = {'is_work_day': False, 'entry_time': None, 'exit_time': None,
                    'theo_minutes': 0, 'automatic_break_minutes': 0, 'tolerance_minutes': 15, 'source': 'default'}

    return results

class ShiftSwapRequest(models.Model):
    """Solicitação para troca pontual de turno entre colegas de setor num dia específico."""
    requester = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='swap_requests_made', verbose_name='Solicitante')
    target_employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='swap_requests_received', verbose_name='Colega Alvo')
    date = models.DateField(verbose_name='Data da Troca')
    reason = models.TextField(blank=True, verbose_name='Motivo')
    status = models.CharField(
        max_length=30, 
        choices=[
            ('PENDING_TARGET', 'Aguardando Colega'), 
            ('PENDING_SUPERVISOR', 'Aguardando Supervisor'), 
            ('PENDING_HR', 'Aguardando RH'), 
            ('APPROVED', 'Aprovado'), 
            ('REJECTED', 'Rejeitado')
        ], 
        default='PENDING_TARGET', verbose_name='Status'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey('core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Resolvido por')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Troca de Turno'
        verbose_name_plural = 'Solicitações de Troca de Turno'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.requester} <-> {self.target_employee} em {self.date} ({self.status})'


class PendingPunchRequest(models.Model):
    """Batida de ponto que aguarda aprovação do supervisor por falha de foto ou GPS."""

    ACTION_IN  = 'IN'
    ACTION_OUT = 'OUT'
    ACTION_CHOICES = [
        (ACTION_IN,  'Entrada (Iniciar)'),
        (ACTION_OUT, 'Saída (Pausar)'),
    ]

    STATUS_PENDING  = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING,  'Aguardando Aprovação'),
        (STATUS_APPROVED, 'Aprovado'),
        (STATUS_REJECTED, 'Rejeitado'),
    ]

    employee     = models.ForeignKey('pim.Employee', on_delete=models.CASCADE,
                                     related_name='pending_punches', verbose_name='Funcionário')
    action_type  = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Tipo')
    requested_at = models.DateTimeField(verbose_name='Horário da Tentativa')
    photo        = models.ImageField(upload_to='attendance_photos/', null=True, blank=True,
                                     verbose_name='Foto Capturada')
    lat          = models.FloatField(null=True, blank=True, verbose_name='Latitude')
    lng          = models.FloatField(null=True, blank=True, verbose_name='Longitude')
    fail_reason  = models.TextField(verbose_name='Motivo da Pendência')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                    default=STATUS_PENDING, verbose_name='Status')
    reviewed_by  = models.ForeignKey('core.OrangeUser', null=True, blank=True,
                                     on_delete=models.SET_NULL, verbose_name='Revisado por')
    reviewed_at  = models.DateTimeField(null=True, blank=True, verbose_name='Revisado em')
    linked_record = models.ForeignKey('AttendanceRecord', null=True, blank=True,
                                      on_delete=models.SET_NULL, verbose_name='Registro Vinculado')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Batida Pendente de Aprovação'
        verbose_name_plural = 'Batidas Pendentes de Aprovação'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.employee} — {self.get_action_type_display()} em {self.requested_at.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"

    @property
    def elapsed_seconds(self):
        """Segundos decorridos desde a tentativa."""
        from django.utils import timezone
        return max(0, (timezone.now() - self.requested_at).total_seconds())







class AttendanceClosingSettings(models.Model):
    """Configurações globais ou por Filial/Empresa para o Banco de Horas e Adicionais."""
    legal_entity = models.OneToOneField(
        'admin_app.LegalEntity', 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='attendance_settings',
        verbose_name='Empresa / Filial (Vazio = Global)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Regra Ativa')
    payroll_closing_day = models.PositiveIntegerField(default=30, verbose_name='Dia de Fechamento da Folha')
    hour_bank_reset_months = models.CharField(max_length=50, default='4,10', verbose_name='Meses de Zeramento (ex: 4,10)')
    overtime_multiplier_weekday = models.FloatField(default=1.6, verbose_name='Multiplicador HE Semanal')
    overtime_multiplier_weekend = models.FloatField(default=2.0, verbose_name='Multiplicador HE DSR/Feriado')
    night_shift_start = models.TimeField(default='22:00:00', verbose_name='Início Adicional Noturno')
    night_shift_end = models.TimeField(default='05:00:00', verbose_name='Fim Adicional Noturno')
    
    class Meta:
        verbose_name = 'Configuração de Ponto'
        verbose_name_plural = 'Configurações de Ponto'

    def __str__(self):
        if self.legal_entity:
            return f"Regras de Ponto - {self.legal_entity.name}"
        return "Regras de Ponto - Padrão Global"

    @classmethod
    def get_settings(cls, legal_entity=None):
        if legal_entity:
            try:
                return cls.objects.get(legal_entity=legal_entity)
            except cls.DoesNotExist:
                pass
        obj, created = cls.objects.get_or_create(legal_entity=None)
        return obj


class TimesheetPeriod(models.Model):
    """Representa um Espelho de Ponto Fechado (Mensal) para um funcionário."""
    STATUS_OPEN = 'OPEN'
    STATUS_LOCKED = 'LOCKED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Aberto'),
        (STATUS_LOCKED, 'Em Análise'),
        (STATUS_CLOSED, 'Fechado/Pago'),
    ]

    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='attendance_periods')
    start_date = models.DateField(verbose_name='Data de Início')
    end_date = models.DateField(verbose_name='Data de Fim')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    
    total_regular_minutes = models.IntegerField(default=0)
    total_extra_60_minutes = models.IntegerField(default=0)
    total_extra_100_minutes = models.IntegerField(default=0)
    total_night_minutes = models.IntegerField(default=0)
    total_negative_minutes = models.IntegerField(default=0)
    
    accumulated_balance_minutes = models.IntegerField(default=0, verbose_name='Saldo Acumulado (Minutos)')
    is_hour_bank_zeroed = models.BooleanField(default=False, verbose_name='Banco Zerado Neste Mês')
    
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey('core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Espelho de Ponto'
        verbose_name_plural = 'Espelhos de Ponto'
        unique_together = ['employee', 'start_date', 'end_date']

    def __str__(self):
        return f"Espelho {self.employee} ({self.start_date.strftime('%b/%Y')})"


class DailyTimeBalance(models.Model):
    """Saldo Diário Consolidado e Frio processado por scripts."""
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='daily_balances')
    date = models.DateField()
    record = models.OneToOneField('AttendanceRecord', on_delete=models.CASCADE, null=True, blank=True)
    
    theo_minutes = models.IntegerField(default=0, verbose_name='Horas Teóricas')
    acted_minutes = models.IntegerField(default=0, verbose_name='Horas Trabalhadas')
    
    regular_minutes = models.IntegerField(default=0, verbose_name='Horas Normais')
    extra_60_minutes = models.IntegerField(default=0, verbose_name='HE 60%')
    extra_100_minutes = models.IntegerField(default=0, verbose_name='HE 100%')
    night_minutes = models.IntegerField(default=0, verbose_name='Horas Noturnas')
    negative_minutes = models.IntegerField(default=0, verbose_name='Atraso/Saída Antecipada')
    
    processed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Saldo Diário de Ponto'
        verbose_name_plural = 'Saldos Diários de Ponto'
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"Saldo {self.employee} em {self.date}"
