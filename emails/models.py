from django.db import models

class EmailConfiguration(models.Model):
    BACKEND_CHOICES = [
        ('smtp', 'SMTP Tradicional'),
        ('resend', 'Resend API (Anymail)'),
        ('sendgrid', 'SendGrid API (Anymail)'),
    ]

    backend_type = models.CharField(max_length=50, choices=BACKEND_CHOICES, default='smtp', verbose_name="Tipo de Servidor")
    
    
    host = models.CharField(max_length=255, help_text="e.g. smtp.gmail.com", verbose_name="Servidor SMTP", blank=True, null=True)
    port = models.IntegerField(default=587, verbose_name="Porta SMTP", blank=True, null=True)
    username = models.CharField(max_length=255, verbose_name="Usuário SMTP", blank=True, null=True)
    password = models.CharField(max_length=255, verbose_name="Senha SMTP", blank=True, null=True)
    use_tls = models.BooleanField(default=True, verbose_name="Usar TLS (SMTP)")
    use_ssl = models.BooleanField(default=False, verbose_name="Usar SSL (SMTP)")

    
    api_key = models.CharField(max_length=255, verbose_name="Token de Acesso / API Key", help_text="Chave da API para Resend, Sendgrid, etc.", blank=True, null=True)

    default_from_email = models.EmailField(verbose_name="E-mail Padrão (From)", help_text="e.g. no-reply@seusite.com")
    is_active = models.BooleanField(default=False, help_text="Apenas uma configuração pode estar ativa por vez.", verbose_name="Ativo")

    class Meta:
        verbose_name = "Configuração de E-mail"
        verbose_name_plural = "Configurações de E-mail"

    def __str__(self):
        return f"[{self.get_backend_type_display()}] {self.host or 'API'} - {self.default_from_email}"

    def save(self, *args, **kwargs):
        if self.is_active:
            EmailConfiguration.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class EmailTemplate(models.Model):
    identifier = models.CharField(max_length=100, unique=True, verbose_name="Identificador", help_text="Código interno (ex: event_invitation)")
    name = models.CharField(max_length=200, verbose_name="Nome da Comunicação")
    subject = models.CharField(max_length=255, verbose_name="Assunto do E-mail")
    body_html = models.TextField(verbose_name="Corpo (HTML)")
    body_text = models.TextField(verbose_name="Corpo (Texto Simples)", blank=True, null=True)
    variables_help = models.TextField(verbose_name="Variáveis Disponíveis", blank=True, null=True, help_text="Referência das variáveis que podem ser usadas neste template.")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template de E-mail"
        verbose_name_plural = "Templates de E-mail"

    def __str__(self):
        return f"{self.name} ({self.identifier})"
