from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserSerializer


class MeView(APIView):
    """
    Retorna os dados detalhados do usuário atualmente autenticado via JWT Token.
    Util para o Flutter app resgatar perfil assim que logar.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RegisterFCMTokenView(APIView):
    """
    Registra o token FCM do dispositivo móvel do usuário.

    O Flutter deve chamar este endpoint logo após o login bem-sucedido,
    passando o token gerado pelo Firebase Messaging.

    POST /api/v1/auth/register-fcm-token/
    Body: { "fcm_token": "<token_do_dispositivo>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token', '').strip()
        if not token:
            return Response({'error': 'fcm_token é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure no other user has this same token (prevents receiving pushes for another user on the same device)
        from core.models import OrangeUser
        OrangeUser.objects.filter(fcm_token=token).exclude(id=request.user.id).update(fcm_token=None)

        request.user.fcm_token = token
        request.user.save(update_fields=['fcm_token'])
        return Response({'status': 'ok', 'message': 'Token FCM registrado com sucesso.'})


class UnregisterFCMTokenView(APIView):
    """
    Remove o token FCM ao fazer logout — evita push para dispositivos deslogados.

    POST /api/v1/auth/unregister-fcm-token/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.fcm_token = None
        request.user.save(update_fields=['fcm_token'])
        return Response({'status': 'ok', 'message': 'Token FCM removido.'})


class AppNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import AppNotification
        # 1 única query — conta unread em memória
        notifications_list = list(AppNotification.objects.filter(user=request.user)[:50])
        data = [{
            'id': n.id,
            'title': n.title,
            'body': n.body,
            'route': n.route,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications_list]
        
        unread_count = sum(1 for n in notifications_list if not n.is_read)
        return Response({'notifications': data, 'unread_count': unread_count})

    def delete(self, request):
        from .models import AppNotification
        AppNotification.objects.filter(user=request.user).delete()
        return Response({'status': 'ok'})

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from .models import AppNotification
        try:
            n = AppNotification.objects.get(pk=pk, user=request.user)
            n.is_read = True
            n.save(update_fields=['is_read'])
            return Response({'status': 'ok'})
        except AppNotification.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


from rest_framework.permissions import AllowAny
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from core.models import OrangeUser, PasswordResetToken

class ForgotPasswordRequestView(APIView):
    """
    Passo 1 — Usuário informa o e-mail e recebe o código de 6 dígitos via API.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'error': 'O campo email é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        user = OrangeUser.objects.filter(email=email, is_active=True, is_deleted=False).first()
        if user:
            # Desativa tokens anteriores não usados
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

            # Gera novo código de 6 dígitos
            code = f"{secrets.randbelow(1000000):06d}"
            PasswordResetToken.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=15),
            )

            # Prepara e envia e-mail HTML corporativo
            from django.conf import settings as dj_settings
            from django.templatetags.static import static
            
            recipient = user.email
            
            # Tenta pegar logo se possível
            logo_url = request.build_absolute_uri(static('img/netline_logo_white.png'))

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 0; background-color: #f7f7f7; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f7f7f7; padding: 40px 20px;">
                    <tr>
                        <td align="center">
                            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; max-width: 600px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-collapse: collapse;">
                                
                                <!-- Top Banner (Dark Blue) -->
                                <tr>
                                    <td style="background-color: #020066; padding: 35px 32px;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td align="left">
                                                    <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700;">Recuperação de Acesso!</h2>
                                                </td>
                                                <td align="right">
                                                    <img src="{logo_url}" alt="CDC" style="height: 32px; display: block; border: 0; outline: none; text-decoration: none;">
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Body -->
                                <tr>
                                    <td style="padding: 45px 32px;">
                                        <h2 style="margin: 0 0 10px; font-size: 22px; color: #00AA45; font-weight: bold;">Olá, {user.first_name or user.username}!</h2>
                                        <p style="margin: 0 0 18px; font-size: 14.5px; color: #111111; line-height: 1.6;">
                                            Esperamos que esteja tudo bem. Estamos enviando este e-mail devido a uma solicitação de redefinição de senha no aplicativo móvel.
                                        </p>
                                        <p style="margin: 0 0 24px; font-size: 14.5px; color: #111111; line-height: 1.6;">
                                            Para manter sua conta segura, utilize o código de verificação abaixo no aplicativo móvel. Este código é pessoal e intransferível, válido por apenas 15 minutos.
                                        </p>
                                        
                                        <!-- Center Box -->
                                        <div style="text-align: center; margin: 35px 0;">
                                            <div style="display:inline-block; border: 2px dashed #dddddd; padding: 24px 48px; background-color: #fafafa;">
                                                <span style="font-family: 'Courier New', monospace; font-size: 46px; font-weight: 900; color: #0a0a0a; letter-spacing: 14px; margin-left: 14px;">{code}</span>
                                            </div>
                                        </div>
                                        
                                        <!-- Fake button -->
                                        <div style="text-align: center; margin-bottom: 45px;">
                                            <span style="display:inline-block; background-color: #00AA45; color: #ffffff; font-weight: bold; padding: 14px 28px; font-size: 16px; border-radius: 100px;">
                                                Código do Aplicativo RH
                                            </span>
                                        </div>
                                        
                                        <!-- Footer Text Green -->
                                        <p style="margin: 0; font-size: 12px; color: #00AA45; text-align: left; line-height: 1.5;">
                                            Para maiores informações, entre em contato pelo Whatsapp 0800 281 4437 ou<br>acesse netlinetelecom.com.br.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Footer Banner (Dark Blue) -->
                                <tr>
                                    <td style="background-color: #020066; padding: 35px 0; text-align: center;">
                                        <img src="{logo_url}" alt="CDC" style="height: 28px; display: inline-block; border: 0; outline: none; text-decoration: none;">
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            try:
                from emails.utils import send_custom_email
                context_data = {
                    'user_name': user.first_name or user.username,
                    'code': code,
                    'logo_url': logo_url
                }
                
                sent = send_custom_email('password_reset', context_data, recipient)
                if not sent:
                    send_mail(
                        subject='Código de Redefinição de Senha — CDC Core',
                        message=f'Seu código de acesso é: {code}', 
                        html_message=html_content,
                        from_email=dj_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
            except Exception as e:
                return Response({'error': f'Erro ao enviar e-mail: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Sempre retorna sucesso por motivos de segurança (não vazar e-mails cadastrados)
        return Response({'status': 'ok', 'message': 'Se o e-mail estiver cadastrado, você receberá o código em breve.'})


class ForgotPasswordVerifyView(APIView):
    """
    Passo 2 — Verifica se o código de 6 dígitos é válido para o e-mail via API.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code = request.data.get('code', '').strip()

        if not email or not code:
            return Response({'error': 'E-mail e código são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        user = OrangeUser.objects.filter(email=email, is_active=True, is_deleted=False).first()
        if not user:
            return Response({'error': 'Código inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        token = PasswordResetToken.objects.filter(
            user=user, code=code, used=False
        ).order_by('-created_at').first()

        if token and token.is_valid():
            return Response({'status': 'ok', 'message': 'Código válido.'})
        else:
            return Response({'error': 'Código inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordNewPasswordView(APIView):
    """
    Passo 3 — Define a nova senha se o e-mail e o código forem válidos via API.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code = request.data.get('code', '').strip()
        password1 = request.data.get('password1', '')
        password2 = request.data.get('password2', '')

        if not email or not code or not password1 or not password2:
            return Response({'error': 'Todos os campos são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password1) < 8:
            return Response({'error': 'A senha deve ter pelo menos 8 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return Response({'error': 'As senhas não coincidem.'}, status=status.HTTP_400_BAD_REQUEST)

        user = OrangeUser.objects.filter(email=email, is_active=True, is_deleted=False).first()
        if not user:
            return Response({'error': 'Código inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        token = PasswordResetToken.objects.filter(
            user=user, code=code, used=False
        ).order_by('-created_at').first()

        if token and token.is_valid():
            # Consome o token
            token.used = True
            token.save()

            # Atualiza a senha
            user.set_password(password1)
            user.save()
            return Response({'status': 'ok', 'message': 'Senha redefinida com sucesso!'})
        else:
            return Response({'error': 'Código inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)
