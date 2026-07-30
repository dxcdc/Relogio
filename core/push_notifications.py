"""
Serviço de Push Notifications via Firebase Cloud Messaging (FCM).

Como funciona:
  1. O app Flutter faz login → chama POST /api/v1/auth/register-fcm-token/
  2. O Django salva o token no campo fcm_token do OrangeUser
  3. Quando ocorre um evento (aprovação, rejeição, etc.), chamamos send_push()
  4. O FCM entrega a notificação ao celular do funcionário (mesmo com app fechado)
"""

import logging
import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def _init_firebase():
    if not firebase_admin._apps:
        b64_cred = os.environ.get('FIREBASE_CREDENTIALS_B64')
        if b64_cred:
            import json, base64
            cred_dict = json.loads(base64.b64decode(b64_cred).decode('utf-8'))
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return True
            
        cred_path = os.path.join(settings.BASE_DIR, 'firebase-adminsdk.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
        else:
            logger.warning("[FCM] Arquivo firebase-adminsdk.json ou variável FIREBASE_CREDENTIALS_B64 não encontrados.")
            return False
    return True

def send_push(user, title: str, body: str, data: dict = None) -> bool:
    """
    Envia push notification para um usuário via FCM usando a nova API HTTP v1.
    """
    if not _init_firebase():
        return False

    token = getattr(user, 'fcm_token', None)
    if not token:
        logger.debug('[FCM] Usuário %s não possui fcm_token — push ignorado.', user.username)
        return False

    # Converte tudo de 'data' para string, pois FCM v1 só aceita strings no payload de data
    str_data = {}
    if data:
        for k, v in data.items():
            str_data[str(k)] = str(v)

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=str_data,
        token=token,
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='cdcrh_channel_id',
                sound='default'
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound='default')
            )
        )
    )

    try:
        response = messaging.send(message)
        logger.info('[FCM] Push enviado para %s (%s). ID: %s', user.username, title, response)
        
        from core.models import AppNotification
        route = data.get('route', '') if data else ''
        AppNotification.objects.create(
            user=user,
            title=title,
            body=body,
            route=route
        )
        return True
    except Exception as exc:
        logger.error('[FCM] Erro ao enviar push para %s: %s', user.username, exc)
        return False


def send_push_to_role(role: str, title: str, body: str, data: dict = None) -> int:
    """
    Envia push para TODOS os usuários de um cargo específico (ex: RH).
    """
    from core.models import OrangeUser
    users = OrangeUser.objects.filter(role=role, is_active=True).exclude(fcm_token='').exclude(fcm_token__isnull=True)
    return send_push_to_users(users, title, body, data)

def send_push_to_users(users, title: str, body: str, data: dict = None) -> int:
    """
    Envia push para uma lista ou QuerySet de usuários.
    Usa send_each_for_multicast para enviar para todos em uma única requisição.
    """
    if not _init_firebase():
        return 0

    tokens = []
    for user in users:
        token = getattr(user, 'fcm_token', None)
        if token:
            tokens.append(token)
            
    if not tokens:
        return 0

    str_data = {}
    if data:
        for k, v in data.items():
            str_data[str(k)] = str(v)

    batch_size = 500
    total_sent = 0
    
    for i in range(0, len(tokens), batch_size):
        batch_tokens = tokens[i:i + batch_size]
        message = messaging.MulticastMessage(
            tokens=batch_tokens,
            notification=messaging.Notification(title=title, body=body),
            data=str_data,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='cdcrh_channel_id',
                    sound='default'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(sound='default'))
            )
        )
        try:
            response = messaging.send_each_for_multicast(message)
            total_sent += response.success_count
            logger.info('[FCM] Lote multicast enviado: %d com sucesso, %d falhas', response.success_count, response.failure_count)
            
            # Save notifications in DB
            from core.models import AppNotification
            route = str_data.get('route', '') if str_data else ''
            
            # Get the users for this batch of tokens
            from core.models import OrangeUser
            batch_users = OrangeUser.objects.filter(fcm_token__in=batch_tokens)
            
            notifications = []
            for bu in batch_users:
                notifications.append(AppNotification(
                    user=bu,
                    title=title,
                    body=body,
                    route=route
                ))
            if notifications:
                AppNotification.objects.bulk_create(notifications)
                
        except Exception as exc:
            logger.error('[FCM] Erro ao enviar lote multicast: %s', exc)

    return total_sent
