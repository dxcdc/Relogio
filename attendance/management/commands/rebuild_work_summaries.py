"""
Comando de gestão para pré-popular a tabela DailyWorkSummary.

Uso:
    # Pré-popula últimos 3 meses + próximos 30 dias para todos os funcionários ativos
    python manage.py rebuild_work_summaries

    # Pré-popula últimos 6 meses
    python manage.py rebuild_work_summaries --months=6

    # Pré-popula apenas um funcionário
    python manage.py rebuild_work_summaries --employee=42

    # Intervalo específico de datas
    python manage.py rebuild_work_summaries --start=2026-01-01 --end=2026-06-30

    # Limpa antes de recomputar
    python manage.py rebuild_work_summaries --months=6 --clear
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Pré-popula a tabela DailyWorkSummary para acelerar consultas de calendário, banco de horas e registros de ponto.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months', type=int, default=3,
            help='Meses passados a processar (padrão: 3). Também inclui os próximos 30 dias.'
        )
        parser.add_argument('--start', type=str, help='Data de início (YYYY-MM-DD)')
        parser.add_argument('--end', type=str, help='Data de fim (YYYY-MM-DD)')
        parser.add_argument('--employee', type=int, help='ID de funcionário específico')
        parser.add_argument(
            '--clear', action='store_true',
            help='Remove entradas existentes antes de recomputar'
        )

    def handle(self, *args, **options):
        from attendance.models import DailyWorkSummary, _compute_work_info_range
        from pim.models import Employee

        today = timezone.now().date()

        # Define período
        if options.get('start'):
            start_date = date.fromisoformat(options['start'])
        else:
            months = options['months']
            # Início do mês, N meses atrás
            start_date = today.replace(day=1)
            for _ in range(months):
                start_date = (start_date - timedelta(days=1)).replace(day=1)

        if options.get('end'):
            end_date = date.fromisoformat(options['end'])
        else:
            end_date = today + timedelta(days=30)  # Inclui próximos 30 dias

        # Define funcionários
        if options.get('employee'):
            employees = list(Employee.objects.filter(pk=options['employee']))
            if not employees:
                self.stdout.write(self.style.ERROR(f"Funcionário {options['employee']} não encontrado."))
                return
        else:
            employees = list(Employee.objects.filter(state='ACTIVE').order_by('id'))

        total = len(employees)
        days_span = (end_date - start_date).days + 1

        self.stdout.write(
            f'\nDailyWorkSummary - Rebuild\n'
            f'   Periodo : {start_date} -> {end_date} ({days_span} dias)\n'
            f'   Funcionarios: {total}\n'
            f'   Total de linhas: ~{total * days_span:,}\n'
        )

        if options.get('clear'):
            deleted, _ = DailyWorkSummary.objects.filter(
                date__range=[start_date, end_date]
            ).delete()
            self.stdout.write(f'   🗑  {deleted} entradas removidas.\n')

        errors = 0
        for i, emp in enumerate(employees, 1):
            try:
                # Remove entradas existentes do período para este funcionário
                DailyWorkSummary.objects.filter(
                    employee=emp, date__range=[start_date, end_date]
                ).delete()

                # Computa usando a implementação interna (5 queries para o range completo)
                computed = _compute_work_info_range(emp, start_date, end_date)

                # Insere em lote (1 bulk insert)
                to_create = []
                for d, info in computed.items():
                    to_create.append(DailyWorkSummary(
                        employee=emp,
                        date=d,
                        is_work_day=info.get('is_work_day', False),
                        entry_time=info.get('entry_time'),
                        exit_time=info.get('exit_time'),
                        theo_minutes=info.get('theo_minutes', 0),
                        source=info.get('source', 'default'),
                        title=info.get('title', '') or '',
                        tolerance_minutes=info.get('tolerance_minutes', 15),
                        automatic_break_minutes=info.get('automatic_break_minutes', 0),
                    ))

                if to_create:
                    DailyWorkSummary.objects.bulk_create(to_create, ignore_conflicts=True)

                self.stdout.write(
                    f'   [{i:>4}/{total}] OK {getattr(emp, "full_name", str(emp)):<30} {len(to_create)} dias',
                    ending='\r'
                )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'\n   [{i}/{total}] {getattr(emp, "full_name", str(emp))}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nConcluido!\n'
                f'   {total - errors} funcionarios processados com sucesso.\n'
                f'   {errors} erros.\n'
                f'   Proximo acesso ao calendario/banco de horas sera instantaneo!\n'
            )
        )
