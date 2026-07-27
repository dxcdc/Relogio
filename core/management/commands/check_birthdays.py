import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from pim.models import Employee
from core.models import Notification, OrangeUser
from buzz.models import BuzzPost, BuzzShare
from core.push_notifications import send_push_to_users, send_push

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica os aniversariantes de uma data específica (padrão: hoje), cria post e dispara Push'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Data no formato YYYY-MM-DD para verificar aniversariantes do passado')

    def handle(self, *args, **options):
        date_str = options.get('date')
        if date_str:
            import datetime
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Formato de data inválido. Use YYYY-MM-DD'))
                return
        else:
            target_date = timezone.localdate()
        
        # Encontra funcionários ativos que fazem aniversário na target_date
        birthday_employees = Employee.objects.filter(
            state=Employee.STATE_ACTIVE,
            birthday__day=target_date.day,
            birthday__month=target_date.month
        )

        count = 0
        for employee in birthday_employees:
            user = getattr(employee, 'user', None)
            if not user:
                continue

            # Verifica se já foi notificado no ano alvo
            already_notified = Notification.objects.filter(
                user=user, 
                message__icontains='Feliz Aniversário',
                created_at__year=target_date.year
            ).exists()
            
            if already_notified:
                continue
                
            try:
                # Define os textos baseados em se o aniversário é hoje ou passado
                is_today = (target_date == timezone.localdate())
                date_fmt = target_date.strftime('%d/%m')
                
                job_title = employee.job_title.title if getattr(employee, 'job_title', None) else "Colaborador(a)"

                if is_today:
                    msg_title = "Aniversariante do Dia"
                    msg_body = f"Hoje é o aniversário de {employee.first_name}, {job_title}. Deixe suas felicitações no Netgram."
                    buzz_text = (
                        f"🎉 Hoje é o aniversário de **{employee.full_name}**!\n\n"
                        f"Vamos todos desejar muita saúde, sucesso e realizações para mais este novo ciclo.\n"
                        f"Deixe seus parabéns nos comentários!"
                    )
                    personal_msg = f"A Netline lhe deseja um excelente dia e um próspero novo ciclo, {employee.first_name}."
                    in_app_msg = f'Feliz Aniversário, {employee.first_name}! A Netline lhe deseja um excelente dia!'
                else:
                    msg_title = "Aniversariante (Fim de Semana)"
                    msg_body = f"Dia {date_fmt} foi o aniversário de {employee.first_name}, {job_title}. Deixe suas felicitações atrasadas no Netgram."
                    buzz_text = (
                        f"🎉 Dia {date_fmt} foi o aniversário de **{employee.full_name}**!\n\n"
                        f"Ainda dá tempo de desejar muita saúde, sucesso e realizações para mais este novo ciclo.\n"
                        f"Deixe seus parabéns nos comentários!"
                    )
                    personal_msg = f"A Netline lhe deseja um próspero novo ciclo, {employee.first_name}. Esperamos que tenha tido um excelente aniversário!"
                    in_app_msg = f'Feliz Aniversário atrasado, {employee.first_name}! A Netline lhe deseja um excelente ano!'

                # 1. Notificação in-app para o aniversariante
                Notification.objects.create(
                    user=user,
                    message=in_app_msg,
                    link='/pim/my-info/'
                )
                
                # 2. Post Automático no Netgram
                system_emp, _ = Employee.objects.get_or_create(
                    employee_id='SYS-0000',
                    defaults={
                        'first_name': 'Sistema', 
                        'last_name': 'Netline',
                        'work_email': 'sistema@netline.com',
                        'is_time_tracking_exempt': True
                    }
                )
                
                buzz_post = BuzzPost.objects.create(text=buzz_text, employee=system_emp)
                BuzzShare.objects.create(post=buzz_post, employee=system_emp, type='post', text=buzz_text)
                
                # 3. Disparo de Push Notifications
                other_users = OrangeUser.objects.filter(is_active=True).exclude(id=user.id).exclude(fcm_token='').exclude(fcm_token__isnull=True)
                
                # Push para todos os outros
                send_push_to_users(
                    other_users,
                    msg_title,
                    msg_body,
                    data={'route': '/buzz/'}
                )
                
                # Push para o aniversariante
                send_push(
                    user,
                    "Feliz Aniversário",
                    personal_msg,
                    data={'route': '/pim/my-info/'}
                )
                
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Notificações disparadas com sucesso para {employee.full_name}'))
                
            except Exception as e:
                logger.error("Erro ao processar aniversário de %s: %s", employee.full_name, e)
                self.stdout.write(self.style.ERROR(f'Erro para {employee.full_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Processamento concluído. {count} aniversariante(s) processado(s).'))
