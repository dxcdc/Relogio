import threading
import logging
import datetime
from django.utils import timezone
from django.core.management import call_command
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Chave de cache para evitar consulta ao banco em toda requisição
_BIRTHDAY_CACHE_KEY = 'daily_task_birthday_done'


def run_birthday_check(dates_to_run):
    for d in dates_to_run:
        try:
            call_command('check_birthdays', date=d)
        except Exception as e:
            logger.error(f"Erro ao rodar check_birthdays automático para {d}: {e}")


class DailyTaskMiddleware:
    """
    Middleware que funciona como um "Cron Job Fake".
    Ele verifica em toda requisição se a rotina de aniversários já rodou hoje.
    Se não rodou, e já passou das 08:00 da manhã, ele dispara em segundo plano.
    Se ficou dias sem rodar (ex: fim de semana), ele recupera o atraso (até 3 dias).

    PERFORMANCE: A verificação agora usa cache em memória (sem hit no banco por request).
    O banco (Config) só é consultado uma vez por dia para sincronizar a data da última execução.
    Os dados de ponto e de sincronização de horários são 100% independentes deste middleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            now = timezone.localtime()
            # Só dispara os parabéns depois das 08:00 da manhã
            if now.hour >= 8:
                today_str = now.strftime('%Y-%m-%d')
                cache_key = f'{_BIRTHDAY_CACHE_KEY}_{today_str}'

                # Verifica no cache em memória — zero query ao banco
                if not cache.get(cache_key):
                    # Marca no cache ANTES de disparar a thread para evitar race condition
                    # TTL de 25 horas garante limpeza automática no próximo dia
                    cache.set(cache_key, True, 60 * 60 * 25)

                    # Agora verifica no banco se há dias atrasados para recuperar
                    from core.models import Config
                    config, created = Config.objects.get_or_create(name='LAST_BIRTHDAY_CHECK_DATE')

                    dates_to_run = [today_str]

                    if config.value and config.value != today_str:
                        try:
                            last_run = datetime.datetime.strptime(config.value, '%Y-%m-%d').date()
                            today_date = now.date()
                            delta = (today_date - last_run).days
                            # Limite de segurança: recupera apenas até 3 dias de atraso (ex: sexta a segunda)
                            if 1 < delta <= 3:
                                for i in range(1, delta):
                                    past_date = today_date - datetime.timedelta(days=i)
                                    dates_to_run.append(past_date.strftime('%Y-%m-%d'))
                        except Exception:
                            pass

                    # Persiste a data no banco
                    config.value = today_str
                    config.save()

                    # Inverte para rodar os dias mais antigos primeiro
                    dates_to_run.reverse()

                    # Roda o comando em uma thread separada (não bloqueia a requisição)
                    thread = threading.Thread(target=run_birthday_check, args=(dates_to_run,))
                    thread.daemon = True
                    thread.start()

        except Exception:
            pass

        return response

