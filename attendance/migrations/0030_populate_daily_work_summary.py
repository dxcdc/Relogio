"""
Migration 0030: Popula automaticamente a tabela DailyWorkSummary na criação.

Ao rodar 'python manage.py migrate', esta migration:
1. Busca todos os funcionários ativos
2. Computa os dados de escala dos últimos 3 meses + próximos 30 dias
3. Salva na DailyWorkSummary via bulk_create

Assim o sistema já vai ao ar com o cache quente — sem precisar de
nenhum comando extra em produção.
"""
from django.db import migrations


def populate_daily_work_summary(apps, schema_editor):
    """
    Popula DailyWorkSummary para todos os funcionários ativos.
    Executado automaticamente como parte da migration.
    """
    from datetime import date, timedelta

    try:
        from attendance.models import _compute_work_info_range, DailyWorkSummary
        from pim.models import Employee
    except ImportError:
        return  # Segurança: não quebra em ambientes sem dados

    today = date.today()

    # Últimos 3 meses + próximos 30 dias
    # (suficiente para ter calendário, banco de horas e agendamentos)
    start_date = (today.replace(day=1) - timedelta(days=92)).replace(day=1)
    end_date = today + timedelta(days=30)

    employees = Employee.objects.filter(state='ACTIVE')

    for emp in employees.iterator():
        try:
            # _compute_work_info_range usa 5 queries para o range todo
            computed = _compute_work_info_range(emp, start_date, end_date)

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

        except Exception:
            # Não interrompe a migration inteira por dados de 1 funcionário
            pass


def reverse_populate(apps, schema_editor):
    """Reverte: limpa a tabela inteira."""
    try:
        from attendance.models import DailyWorkSummary
        DailyWorkSummary.objects.all().delete()
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0029_add_monthly_attendance_summary'),
    ]

    operations = [
        migrations.RunPython(populate_daily_work_summary, reverse_populate),
    ]
