from django.contrib import admin
from .models import EmailConfiguration
from django.core.mail import send_mail
from django.contrib import messages
from django.core.mail import get_connection

@admin.action(description='Testar envio de e-mail com a configuração selecionada')
def test_email_configuration(modeladmin, request, queryset):
    for config in queryset:
        if not request.user.email:
            messages.error(request, f'O seu usuário não possui um endereço de e-mail cadastrado para receber o teste.')
            continue
        try:
            if config.backend_type == 'smtp':
                from django.core.mail.backends.smtp import EmailBackend
                backend = EmailBackend(
                    host=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    use_tls=config.use_tls,
                    use_ssl=config.use_ssl,
                    fail_silently=False,
                )
            elif config.backend_type == 'resend':
                backend = get_connection('anymail.backends.resend.EmailBackend', fail_silently=False, api_key=config.api_key)
            elif config.backend_type == 'sendgrid':
                backend = get_connection('anymail.backends.sendgrid.EmailBackend', fail_silently=False, api_key=config.api_key)
            else:
                backend = get_connection('django.core.mail.backends.console.EmailBackend')

            send_mail(
                subject=f'Teste de Configuração de E-mail ({config.get_backend_type_display()})',
                message=f'Este é um e-mail de teste utilizando o provedor: {config.get_backend_type_display()}.',
                from_email=config.default_from_email,
                recipient_list=[request.user.email],
                connection=backend,
            )
            messages.success(request, f'E-mail de teste enviado com sucesso via {config.get_backend_type_display()}.')
        except Exception as e:
            messages.error(request, f'Erro ao enviar e-mail via {config.get_backend_type_display()}: {str(e)}')

@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('backend_type', 'host', 'default_from_email', 'is_active')
    list_filter = ('backend_type', 'is_active',)
    search_fields = ('host', 'username', 'default_from_email')
    actions = [test_email_configuration]
    
    
    fieldsets = (
        ('Tipo de Provedor', {
            'fields': ('backend_type', 'is_active', 'default_from_email')
        }),
        ('Autenticação API (Anymail)', {
            'fields': ('api_key',),
            'description': 'Preencha apenas se estiver utilizando Resend ou Sendgrid.',
        }),
        ('Autenticação SMTP Tradicional', {
            'fields': ('host', 'port', 'username', 'password', 'use_tls', 'use_ssl'),
            'description': 'Preencha apenas se estiver utilizando um servidor SMTP próprio.',
        }),
    )
