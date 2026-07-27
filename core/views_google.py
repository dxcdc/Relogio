import os
import logging
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import OrangeUser, GoogleIntegration

logger = logging.getLogger(__name__)

# Escopos necessários: perfil básico (email) e acesso de escrita ao calendário do usuário
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]

def _get_client_config():
    """
    Retorna as credenciais do Google lidas das configurações do Django ou variáveis de ambiente.
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID'))
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', os.environ.get('GOOGLE_CLIENT_SECRET'))
    
    if not client_id or not client_secret:
        return None
        
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
    }


def google_login_init(request):
    """
    Inicia o fluxo OAuth 2.0 do Google. Redireciona o usuário para a tela de login/consentimento.
    """
    client_config = _get_client_config()
    if not client_config:
        messages.error(request, "A integração com o Google não está configurada no servidor. Por favor, adicione GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no .env.")
        return redirect('login')

    # Cria o fluxo de autorização
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    
    # Define a URI de redirecionamento dinamicamente
    # No Windows/ngrok, precisamos garantir que o protocolo seja HTTP ou HTTPS conforme o ngrok.
    # O Google exige HTTPS para domínios de produção, mas permite HTTP para localhost.
    redirect_uri = request.build_absolute_uri(reverse('google_login_callback'))
    if 'ngrok-free.dev' in redirect_uri and redirect_uri.startswith('http://'):
        redirect_uri = redirect_uri.replace('http://', 'https://')
        
    flow.redirect_uri = redirect_uri

    # Gera a URL de autorização e salva o 'state' e 'code_verifier' na sessão para proteção CSRF e PKCE
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent' # Garante que o refresh_token seja enviado
    )
    
    request.session['google_oauth_state'] = state
    request.session['google_oauth_code_verifier'] = flow.code_verifier
    return redirect(authorization_url)


def google_login_callback(request):
    """
    Callback do Google OAuth 2.0. Recebe o código, troca pelo token, autentica ou vincula o usuário.
    """
    state = request.session.get('google_oauth_state')
    if not state or request.GET.get('state') != state:
        return HttpResponseBadRequest("Estado de segurança inválido (CSRF detectado). Tente novamente.")

    client_config = _get_client_config()
    if not client_config:
        messages.error(request, "Configuração do Google não encontrada.")
        return redirect('login')

    code_verifier = request.session.get('google_oauth_code_verifier')

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier
    )
    
    redirect_uri = request.build_absolute_uri(reverse('google_login_callback'))
    if 'ngrok-free.dev' in redirect_uri and redirect_uri.startswith('http://'):
        redirect_uri = redirect_uri.replace('http://', 'https://')
        
    flow.redirect_uri = redirect_uri

    # Recebe a resposta e troca o código pelo token de acesso/atualização
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
    except Exception as e:
        logger.error("Erro ao obter token do Google: %s", e)
        messages.error(request, f"Erro ao autenticar com o Google: {str(e)}")
        return redirect('login')

    credentials = flow.credentials

    # 1. Obter informações do usuário (Email)
    try:
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
        email = user_info.get('email')
    except Exception as e:
        logger.error("Erro ao obter dados do usuário do Google: %s", e)
        messages.error(request, "Não foi possível ler as informações de e-mail do seu perfil do Google.")
        return redirect('login')

    if not email:
        messages.error(request, "O Google não forneceu um e-mail válido para esta conta.")
        return redirect('login')

    # 2. Identificar ou Logar o Usuário
    user = None
    if request.user.is_authenticated:
        user = request.user
    else:
        # Se o usuário não estiver logado, tentamos achar o usuário correspondente ao e-mail
        # Primeiro buscamos em OrangeUser (que pode ter o e-mail ou seu Employee ter o e-mail)
        user = OrangeUser.objects.filter(email__iexact=email, is_active=True, is_deleted=False).first()
        
        if not user:
            # Tenta encontrar o e-mail pelo cadastro de Employee
            from pim.models import Employee
            employee = Employee.objects.filter(work_email__iexact=email).first()
            if employee:
                user = OrangeUser.objects.filter(employee=employee, is_active=True, is_deleted=False).first()

        if not user:
            messages.error(request, f"A conta Google '{email}' não está associada a nenhum funcionário ativo no CDC Core.")
            return redirect('login')
            
        # Loga o usuário no Django
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # 3. Salvar ou atualizar as credenciais no Banco de Dados
    credentials_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token or request.session.get('google_refresh_token'),
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Se o Google enviou o refresh_token, salvamos. Se não enviou (porque já foi concedido), tentamos manter o antigo.
    integration, created = GoogleIntegration.objects.get_or_create(user=user, defaults={'credentials': credentials_data})
    if not created:
        # Atualiza mantendo o refresh_token antigo se o novo vier em branco
        if not credentials_data['refresh_token'] and 'refresh_token' in integration.credentials:
            credentials_data['refresh_token'] = integration.credentials['refresh_token']
        integration.credentials = credentials_data
        integration.save()
    
    # Salva na sessão caso precise em callbacks futuros
    if credentials.refresh_token:
        request.session['google_refresh_token'] = credentials.refresh_token

    # 4. Criar a agenda exclusiva para as escalas no Google Calendar do usuário (se necessário)
    try:
        creds = Credentials.from_authorized_user_info(integration.credentials)
        calendar_service = build('calendar', 'v3', credentials=creds)
        
        # Verifica se já temos um ID de agenda salvo e se ela ainda existe no Google
        calendar_exists = False
        if integration.calendar_id:
            try:
                calendar_service.calendars().get(calendarId=integration.calendar_id).execute()
                calendar_exists = True
            except Exception:
                pass
                
        if not calendar_exists:
            # Cria uma agenda exclusiva
            calendar_body = {
                'summary': 'CDC Core - Escala de Trabalho',
                'description': 'Agenda sincronizada automaticamente em tempo real com as escalas de trabalho e folgas do portal CDC Core.',
                'timeZone': 'America/Sao_Paulo'
            }
            new_calendar = calendar_service.calendars().insert(body=calendar_body).execute()
            integration.calendar_id = new_calendar['id']
            integration.save()
            
            # Opcional: Popular a agenda com as escalas existentes imediatamente
            try:
                from attendance.google_sync import populate_google_calendar
                populate_google_calendar(integration)
            except Exception as ex:
                logger.error("Erro ao popular agenda criada: %s", ex)
                
            # messages.success(request, f"Integração Google Calendar ativada com sucesso! Criamos a agenda 'CDC Core - Escala de Trabalho' no seu Google Agenda.")
        else:
            # messages.success(request, f"Conexão com a conta Google '{email}' ativa e sincronizada com sucesso!")
            pass

    except Exception as e:
        logger.error("Erro ao configurar agenda do Google Calendar: %s", e)
        messages.warning(request, f"Login efetuado! Porém, não conseguimos sincronizar com seu calendário do Google no momento: {str(e)}")

    # Redireciona o usuário logado para o dashboard
    return redirect('home')


@login_required
def google_integration_disconnect(request):
    """
    Remove a integração com o Google Calendar do usuário logado.
    """
    integration = GoogleIntegration.objects.filter(user=request.user).first()
    if integration:
        # Se desejar, pode tentar excluir a agenda secundária do Google do usuário antes de apagar do banco
        try:
            creds = Credentials.from_authorized_user_info(integration.credentials)
            calendar_service = build('calendar', 'v3', credentials=creds)
            if integration.calendar_id:
                calendar_service.calendars().delete(calendarId=integration.calendar_id).execute()
        except Exception:
            pass
            
        integration.delete()
        messages.success(request, "A sessão do Google foi encerrada.")
    else:
        messages.info(request, "Você não tem nenhuma integração com o Google Agenda ativa.")
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('profile')
