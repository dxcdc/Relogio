from django.db import models


class Kpi(models.Model):
    """KPIs (Indicadores-Chave de Desempenho)"""
    title = models.CharField(max_length=200, verbose_name='Título do KPI')
    job_title = models.ForeignKey(
        'admin_app.JobTitle', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Cargo'
    )
    min_rating = models.IntegerField(default=0, verbose_name='Nota Mínima')
    max_rating = models.IntegerField(default=10, verbose_name='Nota Máxima')
    is_default = models.BooleanField(default=False, verbose_name='KPI Padrão')
    added_by = models.ForeignKey('core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        ordering = ['title']

    def __str__(self):
        return self.title


class ReviewerGroup(models.Model):
    """Grupos de avaliadores (Supervisor, Subordinado, etc.)"""
    name = models.CharField(max_length=100, verbose_name='Grupo')
    pid = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Grupo de Avaliadores'

    def __str__(self):
        return self.name


class PerformanceReview(models.Model):
    """Avaliações de desempenho"""
    STATUS_INACTIVE = 'INACTIVE'
    STATUS_ACTIVATED = 'ACTIVATED'
    STATUS_IN_PROGRESS = 'IN PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CHOICES = [
        (STATUS_INACTIVE, 'Inativo'),
        (STATUS_ACTIVATED, 'Ativado'),
        (STATUS_IN_PROGRESS, 'Em Andamento'),
        (STATUS_COMPLETED, 'Concluído'),
    ]

    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE, related_name='performance_reviews', verbose_name='Funcionário'
    )
    job_title = models.ForeignKey(
        'admin_app.JobTitle', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Cargo'
    )
    department = models.ForeignKey(
        'admin_app.Subunit', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Departamento'
    )
    review_period_start = models.DateField(verbose_name='Início do Período')
    review_period_end = models.DateField(verbose_name='Fim do Período')
    due_date = models.DateField(null=True, blank=True, verbose_name='Prazo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INACTIVE, verbose_name='Status')
    final_rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Nota Final')
    overall_comment = models.TextField(blank=True, null=True, verbose_name='Comentário Geral')
    completed_date = models.DateField(null=True, blank=True, verbose_name='Data de Conclusão')

    class Meta:
        verbose_name = 'Avaliação de Desempenho'
        verbose_name_plural = 'Avaliações de Desempenho'
        ordering = ['-due_date']

    def __str__(self):
        return f"Avaliação de {self.employee} ({self.review_period_start} - {self.review_period_end})"


class Reviewer(models.Model):
    """Avaliadores vinculados a uma avaliação"""
    STATUS_ACTIVATED = 'ACTIVATED'
    STATUS_IN_PROGRESS = 'IN PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CHOICES = [
        (STATUS_ACTIVATED, 'Ativado'),
        (STATUS_IN_PROGRESS, 'Em Andamento'),
        (STATUS_COMPLETED, 'Concluído'),
    ]

    performance_review = models.ForeignKey(PerformanceReview, on_delete=models.CASCADE, related_name='reviewers')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, verbose_name='Avaliador')
    reviewer_group = models.ForeignKey(ReviewerGroup, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVATED)

    class Meta:
        verbose_name = 'Avaliador'
        unique_together = ['performance_review', 'employee']

    def __str__(self):
        return f"{self.employee} avalia {self.performance_review.employee}"


class ReviewerRating(models.Model):
    """Notas dadas pelo avaliador para cada KPI"""
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='ratings')
    kpi = models.ForeignKey(Kpi, on_delete=models.CASCADE, verbose_name='KPI')
    rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Nota')
    comment = models.TextField(blank=True, null=True, verbose_name='Comentário')

    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        unique_together = ['reviewer', 'kpi']

    def __str__(self):
        return f"{self.kpi} → {self.rating}"


class PerformanceTracker(models.Model):
    """Rastreador de desempenho contínuo"""
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE, related_name='performance_trackers'
    )
    tracker_name = models.CharField(max_length=200, verbose_name='Nome do Rastreador')
    added_by = models.ForeignKey('core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL)
    modified_date = models.DateTimeField(auto_now=True)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rastreador de Desempenho'
        verbose_name_plural = 'Rastreadores de Desempenho'

    def __str__(self):
        return f"{self.tracker_name} - {self.employee}"


class PerformanceTrackerReviewer(models.Model):
    """Revisores do rastreador"""
    tracker = models.ForeignKey(PerformanceTracker, on_delete=models.CASCADE, related_name='reviewers')
    reviewer = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Revisor do Rastreador'
        unique_together = ['tracker', 'reviewer']

    def __str__(self):
        return f"{self.reviewer} → {self.tracker}"


class PerformanceTrackerLog(models.Model):
    """Logs/notas do rastreador"""
    tracker = models.ForeignKey(PerformanceTracker, on_delete=models.CASCADE, related_name='logs')
    reviewer = models.ForeignKey('pim.Employee', null=True, on_delete=models.SET_NULL)
    log = models.TextField(verbose_name='Observação')
    achievement = models.IntegerField(default=0, verbose_name='Conquista (0-5)')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log do Rastreador'
        ordering = ['-added_at']

    def __str__(self):
        return f"Log de {self.tracker} em {self.added_at}"

class Survey(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Rascunho'),
        (STATUS_PUBLISHED, 'Publicada'),
        (STATUS_CLOSED, 'Encerrada'),
    ]

    TARGET_ALL = 'ALL'
    TARGET_LEGAL_ENTITY = 'LEGAL_ENTITY'
    TARGET_SUBUNIT = 'SUBUNIT'
    TARGET_CITY = 'CITY'
    TARGET_CHOICES = [
        (TARGET_ALL, 'Todos os Funcionários'),
        (TARGET_LEGAL_ENTITY, 'Empresa / CNPJ'),
        (TARGET_SUBUNIT, 'Departamento Específico'),
        (TARGET_CITY, 'Filial Específica (Cidade)'),
    ]

    title = models.CharField(max_length=255, verbose_name='Título da Pesquisa')
    description = models.TextField(blank=True, null=True, verbose_name='Instruções / Descrição')
    is_anonymous = models.BooleanField(default=False, verbose_name='Pesquisa Anônima')
    is_leadership_survey = models.BooleanField(default=False, verbose_name='Pesquisa de Liderança')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default=TARGET_ALL, verbose_name='Público Alvo')
    target_legal_entity = models.ForeignKey('admin_app.LegalEntity', on_delete=models.SET_NULL, null=True, blank=True)
    target_subunit = models.ForeignKey('admin_app.Subunit', on_delete=models.SET_NULL, null=True, blank=True)
    target_city = models.ForeignKey('admin_app.City', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey('core.OrangeUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='Data e Hora Limite')

    class Meta:
        verbose_name = 'Pesquisa/Questionário'
        verbose_name_plural = 'Pesquisas e Questionários'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class SurveyQuestion(models.Model):
    TYPE_TEXT = 'TEXT'
    TYPE_RATING_10 = 'RATING_10'
    TYPE_GOOD_BAD = 'GOOD_BAD'
    TYPE_MULTIPLE_CHOICE = 'MULTIPLE_CHOICE'
    TYPE_CHOICES = [
        (TYPE_TEXT, 'Resposta em Texto Escrito'),
        (TYPE_RATING_10, 'Avaliação de 1 a 10'),
        (TYPE_GOOD_BAD, 'Bom, Regular, Ruim'),
        (TYPE_MULTIPLE_CHOICE, 'Múltipla Escolha'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500, verbose_name='Pergunta')
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXT)
    choices = models.TextField(blank=True, null=True, help_text="Para múltipla escolha, separe as opções por ponto e vírgula (;)")
    order = models.IntegerField(default=0, verbose_name='Ordem')
    is_required = models.BooleanField(default=True, verbose_name='Obrigatória')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_text

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE, related_name='survey_responses')
    submitted_at = models.DateTimeField(auto_now_add=True)
    evaluated_leader = models.ForeignKey('pim.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_leadership_evaluations', verbose_name='Líder Avaliado')
    department = models.ForeignKey('admin_app.Subunit', on_delete=models.SET_NULL, null=True, blank=True, related_name='leadership_evaluations', verbose_name='Setor/Departamento')

    class Meta:
        unique_together = ['survey', 'employee'] 
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Resposta para {self.survey.title}"

class SurveyAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    
    text_answer = models.TextField(blank=True, null=True)
    rating_answer = models.IntegerField(blank=True, null=True)
    choice_answer = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Resposta de {self.response} - {self.question}"

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Survey)
def notify_new_survey(sender, instance, created, **kwargs):
    # Sends push when created as PUBLISHED or updated to PUBLISHED
    # To avoid duplicate pushes if someone saves an already published survey,
    # it's usually better to have a track field, but we can do a simple check 
    # here using a custom flag that could be set in the view, or we just accept it might resend if re-saved as published.
    
    if instance.status == Survey.STATUS_PUBLISHED:
        try:
            from core.models import OrangeUser
            from core.push_notifications import send_push_to_users

            users = OrangeUser.objects.filter(is_active=True).exclude(fcm_token='').exclude(fcm_token__isnull=True)
            
            if instance.target_type == Survey.TARGET_LEGAL_ENTITY and instance.target_legal_entity:
                users = users.filter(employee__location__city__country__legal_entity=instance.target_legal_entity)
            elif instance.target_type == Survey.TARGET_SUBUNIT and instance.target_subunit:
                users = users.filter(employee__department=instance.target_subunit)
            elif instance.target_type == Survey.TARGET_CITY and instance.target_city:
                users = users.filter(employee__location__city=instance.target_city)

            send_push_to_users(
                users,
                "Nova Pesquisa Disponível",
                f"{instance.title}",
                data={'route': '/performance/'}
            )
        except Exception as e:
            logger.warning("Erro ao enviar push de pesquisa: %s", e)
