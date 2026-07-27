

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0006_city'),
        ('performance', '0001_initial'),
        ('pim', '0005_alter_employee_city'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Título da Pesquisa')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Instruções / Descrição')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='Pesquisa Anônima')),
                ('status', models.CharField(choices=[('DRAFT', 'Rascunho'), ('PUBLISHED', 'Publicada'), ('CLOSED', 'Encerrada')], default='DRAFT', max_length=20)),
                ('target_type', models.CharField(choices=[('ALL', 'Todos os Funcionários'), ('LEGAL_ENTITY', 'Filial Específica'), ('SUBUNIT', 'Departamento Específico')], default='ALL', max_length=20, verbose_name='Público Alvo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Data de Encerramento')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('target_legal_entity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.legalentity')),
                ('target_subunit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.subunit')),
            ],
            options={
                'verbose_name': 'Pesquisa/Questionário',
                'verbose_name_plural': 'Pesquisas e Questionários',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.CharField(max_length=500, verbose_name='Pergunta')),
                ('question_type', models.CharField(choices=[('TEXT', 'Resposta em Texto Escrito'), ('RATING_10', 'Avaliação de 1 a 10'), ('GOOD_BAD', 'Bom, Regular, Ruim'), ('MULTIPLE_CHOICE', 'Múltipla Escolha')], default='TEXT', max_length=20)),
                ('choices', models.TextField(blank=True, help_text='Para múltipla escolha, separe as opções por ponto e vírgula (;)', null=True)),
                ('order', models.IntegerField(default=0, verbose_name='Ordem')),
                ('is_required', models.BooleanField(default=True, verbose_name='Obrigatória')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='performance.survey')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='SurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_responses', to='pim.employee')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='performance.survey')),
            ],
            options={
                'ordering': ['-submitted_at'],
                'unique_together': {('survey', 'employee')},
            },
        ),
        migrations.CreateModel(
            name='SurveyAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_answer', models.TextField(blank=True, null=True)),
                ('rating_answer', models.IntegerField(blank=True, null=True)),
                ('choice_answer', models.CharField(blank=True, max_length=255, null=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.surveyquestion')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='performance.surveyresponse')),
            ],
        ),
    ]
