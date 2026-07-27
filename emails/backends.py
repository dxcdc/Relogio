from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import get_connection
from .models import EmailConfiguration
import logging

logger = logging.getLogger(__name__)

class CustomEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.connection = None
        self.fail_silently = fail_silently
        self.init_connection(**kwargs)

    def init_connection(self, **kwargs):
        # Evita conflitos de argumentos que o Django passa automaticamente no get_connection
        kwargs.pop('host', None)
        kwargs.pop('port', None)
        kwargs.pop('username', None)
        kwargs.pop('password', None)
        kwargs.pop('use_tls', None)
        kwargs.pop('use_ssl', None)
        try:
            config = EmailConfiguration.objects.filter(is_active=True).first()
            if not config:
                import os
                env_smtp_host = os.environ.get('EMAIL_HOST')
                if env_smtp_host:
                    self.connection = SMTPEmailBackend(
                        host=env_smtp_host,
                        port=int(os.environ.get('EMAIL_PORT', 587)),
                        username=os.environ.get('EMAIL_HOST_USER', ''),
                        password=os.environ.get('EMAIL_HOST_PASSWORD', ''),
                        use_tls=os.environ.get('EMAIL_USE_TLS', 'True') == 'True',
                        use_ssl=os.environ.get('EMAIL_USE_SSL', 'False') == 'True',
                        fail_silently=self.fail_silently,
                        **kwargs
                    )
                    return

                env_resend_key = os.environ.get('RESEND_API_KEY')
                if env_resend_key:
                    # Configura automaticamente usando a chave do .env se o banco estiver vazio
                    self.connection = get_connection(
                        'anymail.backends.resend.EmailBackend',
                        fail_silently=self.fail_silently,
                        api_key=env_resend_key
                    )
                    return
                
                self.connection = get_connection('django.core.mail.backends.console.EmailBackend', fail_silently=self.fail_silently)
                return

            if config.backend_type == 'smtp':
                self.connection = SMTPEmailBackend(
                    host=config.host or '',
                    port=config.port or 587,
                    username=config.username or '',
                    password=config.password or '',
                    use_tls=config.use_tls,
                    use_ssl=config.use_ssl,
                    fail_silently=self.fail_silently,
                    **kwargs
                )
            elif config.backend_type == 'resend':
                
                
                
                self.connection = get_connection(
                    'anymail.backends.resend.EmailBackend', 
                    fail_silently=self.fail_silently, 
                    api_key=config.api_key
                )
            elif config.backend_type == 'sendgrid':
                self.connection = get_connection(
                    'anymail.backends.sendgrid.EmailBackend', 
                    fail_silently=self.fail_silently, 
                    api_key=config.api_key
                )
            else:
                self.connection = get_connection('django.core.mail.backends.console.EmailBackend', fail_silently=self.fail_silently)

        except Exception as e:
            logger.warning(f"Erro ao carregar configurações de e-mail do banco: {e}")
            self.connection = get_connection('django.core.mail.backends.console.EmailBackend', fail_silently=self.fail_silently)

    def send_messages(self, email_messages):
        if not email_messages or not self.connection:
            return 0
        return self.connection.send_messages(email_messages)
