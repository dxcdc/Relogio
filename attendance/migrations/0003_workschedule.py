

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome da Escala')),
                ('entry_time', models.TimeField(verbose_name='Horário de Entrada')),
                ('exit_time', models.TimeField(verbose_name='Horário de Saída')),
                ('lunch_start', models.TimeField(blank=True, null=True, verbose_name='Início do Almoço')),
                ('lunch_end', models.TimeField(blank=True, null=True, verbose_name='Fim do Almoço')),
                ('tolerance_minutes', models.PositiveIntegerField(default=5, help_text='Minutos de tolerância antes de marcar como atraso', verbose_name='Tolerância de Atraso (min)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
            ],
            options={
                'verbose_name': 'Escala de Trabalho',
                'verbose_name_plural': 'Escalas de Trabalho',
                'ordering': ['name'],
            },
        ),
    ]
