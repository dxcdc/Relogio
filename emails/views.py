
import resend
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

def teste_email_resend(request):
    resend.api_key = settings.RESEND_API_KEY

    html_content = render_to_string('emails/boas_vindas.html', {'nome': 'Desenvolvedor'})

    params = {
        "from": "Acme <onboarding@resend.dev>", 
        "to": ["rhnetlinetelecom@gmail.com"], 
        "subject": "Apenas teste",
        "html": html_content,
    }

    try:
        email_resposta = resend.Emails.send(params)
        return HttpResponse(f"Sucesso! E-mail enviado com ID: {email_resposta['id']}")
    except Exception as e:
        return HttpResponse(f"Erro ao enviar e-mail: {str(e)}")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmailTemplate

@login_required
def email_template_list(request):
    if not (request.user.is_superuser or request.user.is_admin or request.user.is_hr):
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    
    templates = EmailTemplate.objects.all().order_by('name')
    return render(request, 'emails/template_list.html', {'templates': templates})

@login_required
def email_template_edit(request, pk):
    if not (request.user.is_superuser or request.user.is_admin or request.user.is_hr):
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
        
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        template.subject = request.POST.get('subject')
        template.body_html = request.POST.get('body_html')
        template.save()
        messages.success(request, f"E-mail '{template.name}' atualizado com sucesso!")
        return redirect('email_template_list')
        
    return render(request, 'emails/template_form.html', {'template': template})