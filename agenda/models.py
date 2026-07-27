from django.db import models
from django.conf import settings
from pim.models import Employee
from admin_app.models import Location, City

class EventType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Tipo")
    color = models.CharField(max_length=10, default='#3b82f6', verbose_name="Cor de Exibição")

    class Meta:
        verbose_name = 'Tipo de Compromisso'
        verbose_name_plural = 'Tipos de Compromisso'
        ordering = ['name']

    def __str__(self):
        return self.name

class Event(models.Model):
    EVENT_TYPES = [
        ('reuniao', 'Reunião'),
        ('integracao', 'Integração'),
        ('entrevista', 'Entrevista'),
        ('treinamento', 'Treinamento'),
        ('visita_tecnica', 'Visita Técnica'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('agendado', 'Agendado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    RECURRENCE_CHOICES = [
        ('none', 'Não Repetir'),
        ('daily', 'Diariamente'),
        ('weekly', 'Semanalmente'),
        ('monthly', 'Mensalmente'),
    ]

    title = models.CharField(max_length=200, verbose_name="Título")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='reuniao', verbose_name="Tipo de Evento")
    organizer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='organized_events', verbose_name="Organizador")
    employees = models.ManyToManyField(Employee, related_name='events', blank=True, verbose_name="Participantes (Colaboradores)")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localização")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cidade")
    start_date = models.DateTimeField(verbose_name="Data/Hora de Início")
    end_date = models.DateTimeField(verbose_name="Data/Hora de Término")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações/Pauta")
    meeting_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link da Reunião (Meet/Zoom)")
    external_participants = models.TextField(blank=True, null=True, verbose_name="Participantes Externos (E-mails)")
    color = models.CharField(max_length=10, default='#3b82f6', verbose_name="Cor de Exibição")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado', verbose_name="Status")
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="Motivo do Cancelamento")
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none', verbose_name="Recorrência")
    recurrence_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='recurrence_children', verbose_name="Evento Pai (Recorrência)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Evento da Agenda'
        verbose_name_plural = 'Eventos da Agenda'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"


class QuickNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quick_notes')
    title = models.CharField(max_length=150, verbose_name="Título", default="Nota Sem Título")
    content = models.TextField(verbose_name="Conteúdo")
    referenced_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_notes', verbose_name="Compromisso Referenciado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nota Rápida'
        verbose_name_plural = 'Notas Rápidas'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
