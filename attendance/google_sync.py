import logging
import os
from datetime import timedelta, datetime
from django.utils import timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from core.models import GoogleIntegration

logger = logging.getLogger(__name__)

def get_calendar_service(integration):
    """
    Retorna o serviço autenticado da Google API do usuário.
    Realiza o refresh automático das credenciais caso o token esteja expirado.
    """
    try:
        creds = Credentials.from_authorized_user_info(integration.credentials)
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Salva o token renovado no banco de dados
                integration.credentials = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                integration.save()
            except Exception as re:
                logger.error("Erro ao renovar token do Google para usuario %s: %s", integration.user.username, re)
                return None
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        logger.error("Erro ao construir servico do Google Calendar: %s", e)
        return None


def sync_shift_override_to_google(override):
    """
    Sincroniza uma escala dinâmica (ShiftOverride) com o Google Calendar.
    Funciona tanto para escalas de trabalho quanto para folgas programadas.
    """
    # 1. Obter o usuário associado
    user = getattr(override.employee, 'user', None)
    if not user:
        return False

    # 2. Obter a integração Google ativa
    integration = GoogleIntegration.objects.filter(user=user).first()
    if not integration or not integration.calendar_id:
        return False

    service = get_calendar_service(integration)
    if not service:
        return False

    # ID de evento compatível com a restrição base32hex do Google Calendar (apenas a-v e 0-9)
    # Convertemos o ID estruturado para hexadecimal para garantir caracteres de 0-9 e a-f (que são subconjunto de a-v)
    raw_id = f"override{override.id}x{override.employee.id}"
    event_id = raw_id.encode('utf-8').hex()

    from attendance.models import ShiftOverride
    
    # Monta o corpo do evento
    event_body = {
        'id': event_id,
        'summary': '',
        'description': '',
        'status': 'confirmed',
        'transparency': 'opaque', # Ocupado na agenda
    }

    if override.override_type == ShiftOverride.TYPE_WORK:
        if not override.entry_time or not override.exit_time:
            return False
            
        dt_start = datetime.combine(override.date, override.entry_time)
        if override.exit_time <= override.entry_time:
            # Plantão noturno (saída no dia seguinte)
            dt_end = datetime.combine(override.date + timedelta(days=1), override.exit_time)
        else:
            dt_end = datetime.combine(override.date, override.exit_time)

        # Tratar timezone (America/Sao_Paulo)
        local_tz = timezone.get_current_timezone()
        if timezone.is_naive(dt_start):
            dt_start = timezone.make_aware(dt_start, local_tz)
        if timezone.is_naive(dt_end):
            dt_end = timezone.make_aware(dt_end, local_tz)

        event_body['summary'] = f"Turno: {override.entry_time.strftime('%H:%M')} - {override.exit_time.strftime('%H:%M')}"
        if override.reason:
            display_reason = override.reason.replace("Escala Viva - ", "").replace("Turno via Excel", "Turno")
            event_body['summary'] = f"Turno: {display_reason} ({override.entry_time.strftime('%H:%M')}-{override.exit_time.strftime('%H:%M')})"
            
        event_body['description'] = f"Escala de trabalho agendada no CDC Core.\nTurno: {override.entry_time.strftime('%H:%M')} ate {override.exit_time.strftime('%H:%M')}.\nMotivo: {override.reason or 'Nao informado'}"
        event_body['start'] = {
            'dateTime': dt_start.isoformat(),
            'timeZone': 'America/Sao_Paulo'
        }
        event_body['end'] = {
            'dateTime': dt_end.isoformat(),
            'timeZone': 'America/Sao_Paulo'
        }

    elif override.override_type == ShiftOverride.TYPE_REST:
        # Folga é um evento de dia inteiro
        event_body['summary'] = "Folga / DSR"
        event_body['description'] = f"Dia de descanso programado.\nMotivo: {override.reason or 'Folga / DSR'}"
        event_body['transparency'] = 'transparent' # Disponível na agenda
        
        event_body['start'] = {
            'date': override.date.strftime("%Y-%m-%d")
        }
        event_body['end'] = {
            'date': (override.date + timedelta(days=1)).strftime("%Y-%m-%d")
        }

    # Executa a escrita (insert or update)
    try:
        # Tenta atualizar o evento caso ele já exista
        service.events().update(
            calendarId=integration.calendar_id,
            eventId=event_id,
            body=event_body
        ).execute()
        logger.info("Evento de escala %s atualizado no Google Calendar com sucesso.", event_id)
    except Exception as e:
        # Se falhar (404), insere um novo evento
        try:
            service.events().insert(
                calendarId=integration.calendar_id,
                body=event_body
            ).execute()
            logger.info("Novo evento de escala %s inserido no Google Calendar com sucesso.", event_id)
        except Exception as ins_err:
            logger.error("Erro ao inserir escala no Google Calendar para o usuario %s: %s", user.username, ins_err)
            return False

    return True


def delete_shift_override_from_google(override):
    """
    Remove o evento da escala do Google Calendar caso a escala seja excluída.
    """
    user = getattr(override.employee, 'user', None)
    if not user:
        return False

    integration = GoogleIntegration.objects.filter(user=user).first()
    if not integration or not integration.calendar_id:
        return False

    service = get_calendar_service(integration)
    if not service:
        return False

    raw_id = f"override{override.id}x{override.employee.id}"
    event_id = raw_id.encode('utf-8').hex()

    try:
        service.events().delete(
            calendarId=integration.calendar_id,
            eventId=event_id
        ).execute()
        logger.info("Evento de escala %s removido do Google Calendar.", event_id)
        return True
    except Exception as e:
        logger.warning("Erro (esperado caso nao exista) ao excluir escala %s do Google Calendar: %s", event_id, e)
        return False


def sync_leave_to_google(leave):
    """
    Sincroniza uma licença ou afastamento aprovado (Leave) com o Google Calendar.
    """
    if leave.status != 'APPROVED':
        # Se não estiver mais aprovado, removemos
        return delete_leave_from_google(leave)

    user = getattr(leave.employee, 'user', None)
    if not user:
        return False

    integration = GoogleIntegration.objects.filter(user=user).first()
    if not integration or not integration.calendar_id:
        return False

    service = get_calendar_service(integration)
    if not service:
        return False

    raw_id = f"leave{leave.id}x{leave.employee.id}"
    event_id = raw_id.encode('utf-8').hex()

    desc = f"Licenca / Afastamento aprovado.\nTipo: {leave.leave_type.name}."
    if leave.duration_type == 'half_day':
        desc += "\nPeriodo: Meio Periodo."
        summary = f"Licenca (Meio Periodo): {leave.leave_type.name}"
    else:
        summary = f"Licenca: {leave.leave_type.name}"

    event_body = {
        'id': event_id,
        'summary': summary,
        'description': desc,
        'transparency': 'transparent', # Disponível
        'status': 'confirmed',
        'start': {
            'date': leave.date.strftime("%Y-%m-%d")
        },
        'end': {
            'date': (leave.date + timedelta(days=1)).strftime("%Y-%m-%d")
        }
    }

    try:
        service.events().update(
            calendarId=integration.calendar_id,
            eventId=event_id,
            body=event_body
        ).execute()
    except Exception:
        try:
            service.events().insert(
                calendarId=integration.calendar_id,
                body=event_body
            ).execute()
        except Exception as ins_err:
            logger.error("Erro ao sincronizar licenca no Google Calendar: %s", ins_err)
            return False

    return True


def delete_leave_from_google(leave):
    """
    Remove uma licença excluída do Google Calendar.
    """
    user = getattr(leave.employee, 'user', None)
    if not user:
        return False

    integration = GoogleIntegration.objects.filter(user=user).first()
    if not integration or not integration.calendar_id:
        return False

    service = get_calendar_service(integration)
    if not service:
        return False

    raw_id = f"leave{leave.id}x{leave.employee.id}"
    event_id = raw_id.encode('utf-8').hex()

    try:
        service.events().delete(
            calendarId=integration.calendar_id,
            eventId=event_id
        ).execute()
        return True
    except Exception as e:
        logger.warning("Erro ao remover licenca %s do Google Calendar: %s", event_id, e)
        return False


def populate_google_calendar(integration):
    """
    Sincroniza em lote as escalas dos proximos 60 dias para a conta Google do usuario recem-conectado.
    """
    from attendance.models import ShiftOverride
    from leave.models import Leave
    
    employee = getattr(integration.user, 'employee', None)
    if not employee:
        return

    today = timezone.localdate()
    start_date = today - timedelta(days=5) # Retroage 5 dias
    end_date = today + timedelta(days=60)   # Avanca 60 dias

    # Sincroniza exceções de turno
    overrides = ShiftOverride.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    )
    for ov in overrides:
        try:
            sync_shift_override_to_google(ov)
        except Exception as ex:
            logger.error("Erro no lote de override %s: %s", ov.id, ex)

    # Sincroniza licenças
    leaves = Leave.objects.filter(
        employee=employee,
        status='APPROVED',
        date__range=[start_date, end_date]
    )
    for lv in leaves:
        try:
            sync_leave_to_google(lv)
        except Exception as ex:
            logger.error("Erro no lote de licenca %s: %s", lv.id, ex)



def _get_corporate_calendar_service():
    """
    Retorna (service, calendar_id) do calendario corporativo usando Service Account.
    Autentica automaticamente sem necessidade de login manual de nenhum usuario.
    """
    import os
    from django.conf import settings

    calendar_id = os.environ.get('GOOGLE_CORP_CALENDAR_ID', '')
    if not calendar_id or calendar_id == 'primary':
        logger.warning("[Agenda Corporativa] GOOGLE_CORP_CALENDAR_ID nao configurado no .env.")
        return None, None

    # Caminho do arquivo da service account
    sa_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')
    if not os.path.isabs(sa_json):
        sa_json = os.path.join(settings.BASE_DIR, sa_json)

    if not os.path.exists(sa_json) and not os.environ.get('GOOGLE_SERVICE_ACCOUNT_B64'):
        logger.warning("[Agenda Corporativa] Nenhuma credencial (arquivo %s ou variável GOOGLE_SERVICE_ACCOUNT_B64) encontrada.", sa_json)
        return None, None

    try:
        from google.oauth2 import service_account
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        b64_cred = os.environ.get('GOOGLE_SERVICE_ACCOUNT_B64')
        if b64_cred:
            import json, base64
            cred_dict = json.loads(base64.b64decode(b64_cred).decode('utf-8'))
            creds = service_account.Credentials.from_service_account_info(cred_dict, scopes=SCOPES)
            logger.info("[Agenda Corporativa] Service Account autenticada via B64 (.env).")
        else:
            creds = service_account.Credentials.from_service_account_file(sa_json, scopes=SCOPES)
            logger.info("[Agenda Corporativa] Service Account autenticada via arquivo JSON com sucesso.")
            
        service = build('calendar', 'v3', credentials=creds)
        return service, calendar_id
    except Exception as e:
        logger.error("[Agenda Corporativa] Erro ao autenticar Service Account: %s", e)
        return None, None


def sync_corporate_event_to_google(event):
    """
    Sincroniza um evento da Agenda Corporativa com o CALENDARIO CORPORATIVO
    COMPARTILHADO da empresa.

    O calendario e gerenciado por um unico usuario (GOOGLE_CORP_CALENDAR_OWNER),
    sem depender de integracao individual de cada colaborador.
    Todos os funcionarios assinam esse calendario uma unica vez.
    """
    service, calendar_id = _get_corporate_calendar_service()
    if not service:
        return False

    # ID unico compativel com base32hex do Google Calendar
    raw_id = f"corpevent{event.id}"
    event_id = raw_id.encode('utf-8').hex()

    # Participantes listados na descricao (Service Account nao pode convidar attendees
    # sem Domain-Wide Delegation — todos recebem via assinatura do calendario)
    participants_desc = []
    for emp in event.employees.all():
        name = emp.full_name or str(emp)
        participants_desc.append(name)
    if event.external_participants:
        participants_desc.append(event.external_participants.strip())

    # Localizacao
    loc_parts = []
    if event.location:
        loc_parts.append(event.location.name)
    if event.city:
        loc_parts.append(event.city.name)
    loc_str = ', '.join(loc_parts)
    if event.meeting_link:
        loc_str = (loc_str + ' | ' if loc_str else '') + event.meeting_link

    # Descricao
    description = event.notes or ''
    if participants_desc:
        description += f"\n\nParticipantes: {', '.join(participants_desc)}"
    if event.meeting_link:
        description += f"\n\nLink da Reuniao: {event.meeting_link}"
    description += f"\n\n[Sincronizado automaticamente pelo CDC]"

    # Cor do evento no Google Calendar (mapeamento aproximado)
    COLOR_MAP = {
        '#3b82f6': '9',   # Blueberry
        '#10b981': '2',   # Sage
        '#ef4444': '11',  # Tomato
        '#f59e0b': '5',   # Banana
        '#8b5cf6': '3',   # Grape
        '#ec4899': '4',   # Flamingo
    }
    color_id = COLOR_MAP.get(event.color, '1')

    event_body = {
        'id': event_id,
        'summary': event.title,
        'description': description,
        'location': loc_str,
        'colorId': color_id,
        'visibility': 'public',
        'status': 'confirmed' if event.status != 'cancelado' else 'cancelled',
        'start': {
            'dateTime': event.start_date.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': event.end_date.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
    }

    try:
        service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event_body,
            sendUpdates='none',
        ).execute()
        logger.info("[Agenda Corporativa] Evento %s ('%s') atualizado no Google Calendar corporativo.", event.id, event.title)
    except Exception:
        try:
            service.events().insert(
                calendarId=calendar_id,
                body=event_body,
                sendUpdates='none',
            ).execute()
            logger.info("[Agenda Corporativa] Evento %s ('%s') inserido no Google Calendar corporativo.", event.id, event.title)
        except Exception as ins_err:
            logger.error("[Agenda Corporativa] Falha ao inserir evento %s no Google Calendar: %s", event.id, ins_err)
            return False

    return True


def delete_corporate_event_from_google(event):
    """
    Remove um evento do CALENDARIO CORPORATIVO COMPARTILHADO da empresa.
    """
    service, calendar_id = _get_corporate_calendar_service()
    if not service:
        return False

    raw_id = f"corpevent{event.id}"
    event_id = raw_id.encode('utf-8').hex()

    try:
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates='none',
        ).execute()
        logger.info("[Agenda Corporativa] Evento %s removido do Google Calendar corporativo.", event.id)
        return True
    except Exception as e:
        logger.warning("[Agenda Corporativa] Erro ao remover evento %s: %s", event_id, e)
        return False


def get_corporate_calendar_subscribe_url():
    """
    Retorna a URL publica para qualquer funcionario assinar o calendario corporativo.
    Formato: https://calendar.google.com/calendar/r?cid=<calendar_id_encoded>
    """
    import os, urllib.parse
    calendar_id = os.environ.get('GOOGLE_CORP_CALENDAR_ID', '')
    if not calendar_id or calendar_id == 'primary':
        return None
    encoded = urllib.parse.quote(calendar_id)
    return f"https://calendar.google.com/calendar/r?cid={encoded}"
