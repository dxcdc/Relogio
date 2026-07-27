from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.utils.timezone import now
from axes.helpers import get_client_ip_address
from axes.models import AccessAttempt
from datetime import timedelta

def lockout_response(request, credentials=None, *args, **kwargs):
    cooloff_hours = getattr(settings, 'AXES_COOLOFF_TIME', 0.5)
    if isinstance(cooloff_hours, timedelta):
        total_minutes = int(cooloff_hours.total_seconds() // 60)
    else:
        total_minutes = int(cooloff_hours * 60)
    remaining_minutes = total_minutes
    
    ip_address = get_client_ip_address(request)
    username = None
    if credentials:
        username = credentials.get('username')
    if not username and request.POST:
        username = request.POST.get('username')
        
    attempts = AccessAttempt.objects.filter(ip_address=ip_address)
    if username:
        attempts = attempts.filter(username=username)
        
    attempt = attempts.order_by('-attempt_time').first()
    if attempt:
        elapsed = now() - attempt.attempt_time
        remaining = timedelta(minutes=total_minutes) - elapsed
        if remaining.total_seconds() > 0:
            remaining_minutes = int(remaining.total_seconds() // 60) + 1
            
    message = f"Muitas tentativas inválidas. Por motivos de segurança, seu acesso foi bloqueado. Tente novamente em {remaining_minutes} minuto(s)."

    if request.path.startswith('/api/'):
        return JsonResponse(
            {'detail': message},
            status=429
        )
        
    return redirect(f'/login/?locked=1&time={remaining_minutes}')
