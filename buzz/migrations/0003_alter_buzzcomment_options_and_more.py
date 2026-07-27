

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buzz', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='buzzcomment',
            options={'ordering': ['created_at'], 'verbose_name': 'Comentario', 'verbose_name_plural': 'Comentarios'},
        ),
        migrations.AlterModelOptions(
            name='buzzlikeoncomment',
            options={'verbose_name': 'Curtida no Comentario'},
        ),
        migrations.AlterField(
            model_name='buzzcomment',
            name='text',
            field=models.TextField(verbose_name='Comentario'),
        ),
        migrations.CreateModel(
            name='BugReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Titulo')),
                ('description', models.TextField(verbose_name='Descricao detalhada')),
                ('screenshot', models.ImageField(blank=True, null=True, upload_to='bug_screenshots/', verbose_name='Captura de tela')),
                ('status', models.CharField(choices=[('OPEN', 'Aberto'), ('ANALYZING', 'Em analise'), ('RESOLVED', 'Resolvido'), ('WONTFIX', 'Nao sera corrigido')], default='OPEN', max_length=20, verbose_name='Status')),
                ('priority', models.CharField(choices=[('LOW', 'Baixa'), ('MEDIUM', 'Media'), ('HIGH', 'Alta'), ('CRITICAL', 'Critica')], default='MEDIUM', max_length=20, verbose_name='Prioridade')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bug_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reporte de Bug',
                'verbose_name_plural': 'Reportes de Bug',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BugReportComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Resposta')),
                ('is_internal', models.BooleanField(default=False, verbose_name='Nota interna (so Admin ve)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bug_comments', to=settings.AUTH_USER_MODEL)),
                ('bug_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='buzz.bugreport')),
            ],
            options={
                'verbose_name': 'Comentario de Bug',
                'verbose_name_plural': 'Comentarios de Bug',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChangelogPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Titulo')),
                ('version', models.CharField(blank=True, max_length=30, verbose_name='Versao/Tag')),
                ('category', models.CharField(choices=[('FEATURE', 'Nova Funcionalidade'), ('BUGFIX', 'Correcao de Bug'), ('IMPROVEMENT', 'Melhoria'), ('SECURITY', 'Seguranca')], default='FEATURE', max_length=20, verbose_name='Categoria')),
                ('content', models.TextField(verbose_name='Conteudo')),
                ('pinned', models.BooleanField(default=False, verbose_name='Fixar no topo')),
                ('published_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='changelog_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Nota de Atualizacao',
                'verbose_name_plural': 'Notas de Atualizacao',
                'ordering': ['-pinned', '-published_at'],
            },
        ),
    ]
