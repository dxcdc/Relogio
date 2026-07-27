from django.db import models
from django.conf import settings
from django.utils import timezone
from pim.models import Employee
from admin_app.models import Subunit
from agenda.models import Event


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('tech', 'Tecnologia'),
        ('soft', 'Comportamental'),
        ('language', 'Idioma'),
        ('tool', 'Ferramenta / Software'),
        ('other', 'Outros'),
    ]
    name     = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tech', verbose_name="Categoria")
    icon     = models.CharField(max_length=60, blank=True, default='bi-star', verbose_name="Ícone Bootstrap")

    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class JobOpening(models.Model):
    STATUS_CHOICES = [
        ('OPEN',   'Aberta'),
        ('CLOSED', 'Fechada/Preenchida'),
    ]
    title           = models.CharField(max_length=200, verbose_name="Título da Vaga")
    department      = models.ForeignKey(Subunit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Setor/Departamento")
    job_title       = models.ForeignKey('admin_app.JobTitle', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cargo da Vaga")
    description     = models.TextField(verbose_name="Descrição da Vaga")
    quantity        = models.PositiveIntegerField(default=1, verbose_name="Quantidade de Vagas")
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name="Status")
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='required_for_jobs',  verbose_name="Skills Obrigatórias")
    desired_skills  = models.ManyToManyField(Skill, blank=True, related_name='desired_for_jobs',   verbose_name="Skills Desejáveis")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vaga"
        verbose_name_plural = "Vagas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def remaining_quantity(self):
        hired_count = self.candidates.filter(status='HIRED', onboarded=True).count()
        return max(0, self.quantity - hired_count)


class Candidate(models.Model):
    STAGE_CHOICES = [
        ('screening',          'Triagem'),
        ('interview',          'Entrevista'),
        ('psych_test',         'Teste Psicológico'),
        ('practical_test',     'Teste Prático'),
        ('probation_45',       'Estágio 45 d'),
        ('probation_90',       'Estágio 90 d'),
        ('hired',              'Efetivação'),
    ]
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'Em Andamento'),
        ('HIRED',       'Contratado'),
        ('REJECTED',    'Reprovado'),
    ]
    name          = models.CharField(max_length=200, verbose_name="Nome Completo")
    email         = models.EmailField(verbose_name="E-mail")
    phone         = models.CharField(max_length=20, verbose_name="Telefone/Celular", blank=True, null=True)
    linkedin_url  = models.URLField(blank=True, null=True, verbose_name="LinkedIn")
    resume        = models.FileField(upload_to='resumes/', verbose_name="Currículo (CV)", blank=True, null=True)
    job_opening   = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='candidates', verbose_name="Vaga Pretendida")
    skills        = models.ManyToManyField(Skill, blank=True, related_name='candidates', verbose_name="Skills")
    match_score   = models.FloatField(default=0.0, verbose_name="Match Score (%)")
    current_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='screening', verbose_name="Etapa Atual")
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS', verbose_name="Situação")
    stage_updated_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Atualização da Etapa")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motivo da Reprovação")
    onboarded        = models.BooleanField(default=False, verbose_name="Cadastro Criado no Sistema")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Candidato"
        verbose_name_plural = "Candidatos"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Candidate.objects.get(pk=self.pk)
            if orig.current_stage != self.current_stage:
                self.stage_updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def match_color(self):
        if self.match_score >= 80:
            return 'success'
        elif self.match_score >= 50:
            return 'warning'
        return 'danger'


class PublicApplication(models.Model):
    """Solicitação de candidatura vinda do portal público — aguarda aprovação do RH."""
    STATUS_CHOICES = [
        ('PENDING',  'Aguardando Análise'),
        ('ACCEPTED', 'Aceito → Pipeline'),
        ('REJECTED', 'Rejeitado'),
    ]
    name         = models.CharField(max_length=200, verbose_name="Nome Completo")
    email        = models.EmailField(verbose_name="E-mail")
    phone        = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    resume       = models.FileField(upload_to='public_resumes/', blank=True, null=True, verbose_name="Currículo")
    job_opening  = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='applications', verbose_name="Vaga")
    skills       = models.ManyToManyField(Skill, blank=True, related_name='applications', verbose_name="Skills Declaradas")
    match_score  = models.FloatField(default=0.0, verbose_name="Match Score (%)")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    rh_notes     = models.TextField(blank=True, verbose_name="Observações do RH")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Candidatura Pública"
        verbose_name_plural = "Candidaturas Públicas"
        ordering = ['-match_score', '-created_at']
        # Unique together: same email can't apply twice to the same vacancy
        unique_together = [['email', 'job_opening']]

    def __str__(self):
        return f"{self.name} → {self.job_opening.title}"

    def match_color(self):
        if self.match_score >= 80:
            return 'success'
        elif self.match_score >= 50:
            return 'warning'
        return 'danger'


class Interview(models.Model):
    STAGE_CHOICES = [
        ('interview',         'Entrevista'),
        ('psych_test',        'Teste Psicológico'),
        ('practical_test',    'Teste Prático'),
    ]
    STATUS_CHOICES = [
        ('SCHEDULED',  'Agendada'),
        ('COMPLETED',  'Realizada'),
        ('CANCELLED',  'Cancelada'),
    ]
    candidate     = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews', verbose_name="Candidato")
    stage         = models.CharField(max_length=50, choices=STAGE_CHOICES, verbose_name="Etapa da Entrevista")
    date          = models.DateTimeField(verbose_name="Data/Hora Agendada")
    interviewers  = models.ManyToManyField(Employee, related_name='recruitment_interviews', verbose_name="Entrevistadores")
    notes         = models.TextField(blank=True, null=True, verbose_name="Instruções/Pauta")
    linked_event  = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_interviews', verbose_name="Evento na Agenda")
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name="Status")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entrevista"
        verbose_name_plural = "Entrevistas"
        ordering = ['date']

    def __str__(self):
        return f"{self.candidate.name} - {self.get_stage_display()}"


class InterviewFeedback(models.Model):
    interview    = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Entrevista")
    interviewer  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='submitted_feedbacks', verbose_name="Entrevistador")
    score        = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Pontuação (1-5)")
    feedback_text = models.TextField(verbose_name="Feedback / Parecer Técnico")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback de Entrevista"
        verbose_name_plural = "Feedbacks de Entrevista"
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback de {self.interviewer.full_name} para {self.interview.candidate.name}"
