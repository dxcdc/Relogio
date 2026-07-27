

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_app', '0001_initial'),
        ('pim', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewerGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Grupo')),
                ('pid', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Grupo de Avaliadores',
            },
        ),
        migrations.CreateModel(
            name='Kpi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título do KPI')),
                ('min_rating', models.IntegerField(default=0, verbose_name='Nota Mínima')),
                ('max_rating', models.IntegerField(default=10, verbose_name='Nota Máxima')),
                ('is_default', models.BooleanField(default=False, verbose_name='KPI Padrão')),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.jobtitle', verbose_name='Cargo')),
            ],
            options={
                'verbose_name': 'KPI',
                'verbose_name_plural': 'KPIs',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='PerformanceReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_period_start', models.DateField(verbose_name='Início do Período')),
                ('review_period_end', models.DateField(verbose_name='Fim do Período')),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Prazo')),
                ('status', models.CharField(choices=[('INACTIVE', 'Inativo'), ('ACTIVATED', 'Ativado'), ('IN PROGRESS', 'Em Andamento'), ('COMPLETED', 'Concluído')], default='INACTIVE', max_length=20, verbose_name='Status')),
                ('final_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Nota Final')),
                ('overall_comment', models.TextField(blank=True, null=True, verbose_name='Comentário Geral')),
                ('completed_date', models.DateField(blank=True, null=True, verbose_name='Data de Conclusão')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.subunit', verbose_name='Departamento')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_reviews', to='pim.employee', verbose_name='Funcionário')),
                ('job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.jobtitle', verbose_name='Cargo')),
            ],
            options={
                'verbose_name': 'Avaliação de Desempenho',
                'verbose_name_plural': 'Avaliações de Desempenho',
                'ordering': ['-due_date'],
            },
        ),
        migrations.CreateModel(
            name='PerformanceTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracker_name', models.CharField(max_length=200, verbose_name='Nome do Rastreador')),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_trackers', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Rastreador de Desempenho',
                'verbose_name_plural': 'Rastreadores de Desempenho',
            },
        ),
        migrations.CreateModel(
            name='PerformanceTrackerLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log', models.TextField(verbose_name='Observação')),
                ('achievement', models.IntegerField(default=0, verbose_name='Conquista (0-5)')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pim.employee')),
                ('tracker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='performance.performancetracker')),
            ],
            options={
                'verbose_name': 'Log do Rastreador',
                'ordering': ['-added_at'],
            },
        ),
        migrations.CreateModel(
            name='Reviewer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ACTIVATED', 'Ativado'), ('IN PROGRESS', 'Em Andamento'), ('COMPLETED', 'Concluído')], default='ACTIVATED', max_length=20)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee', verbose_name='Avaliador')),
                ('performance_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviewers', to='performance.performancereview')),
                ('reviewer_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.reviewergroup')),
            ],
            options={
                'verbose_name': 'Avaliador',
                'unique_together': {('performance_review', 'employee')},
            },
        ),
        migrations.CreateModel(
            name='PerformanceTrackerReviewer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee')),
                ('tracker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviewers', to='performance.performancetracker')),
            ],
            options={
                'verbose_name': 'Revisor do Rastreador',
                'unique_together': {('tracker', 'reviewer')},
            },
        ),
        migrations.CreateModel(
            name='ReviewerRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Nota')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comentário')),
                ('kpi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.kpi', verbose_name='KPI')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='performance.reviewer')),
            ],
            options={
                'verbose_name': 'Nota',
                'verbose_name_plural': 'Notas',
                'unique_together': {('reviewer', 'kpi')},
            },
        ),
    ]
