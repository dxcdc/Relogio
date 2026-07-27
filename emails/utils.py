from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
from django.utils.html import strip_tags
from .models import EmailTemplate

def send_custom_email(identifier, context_data, to_email):
    """
    Busca o template no banco, substitui as tags usando o context_data e envia o e-mail.
    Retorna True se enviado, False se o template não existir.
    """
    try:
        template = EmailTemplate.objects.get(identifier=identifier, is_active=True)
    except EmailTemplate.DoesNotExist:
        return False
        
    # Processar o Assunto
    t_subject = Template(template.subject)
    c_subject = Context(context_data)
    subject = t_subject.render(c_subject)
    
    # Processar o HTML
    t_body = Template(template.body_html)
    c_body = Context(context_data)
    html_content = t_body.render(c_body)
    
    # Gerar o texto limpo
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email] if isinstance(to_email, str) else to_email
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)
    
    return True
