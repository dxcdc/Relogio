

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0003_add_supervisor_approved_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='hr_reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo da Rejeição'),
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='reviewed_by_hr',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hr_approved_leaves', to=settings.AUTH_USER_MODEL, verbose_name='Aprovado por (RH)'),
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='reviewed_by_supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor_approved_leaves', to=settings.AUTH_USER_MODEL, verbose_name='Pré-aprovado por'),
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='supervisor_reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='LeaveActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('SUBMIT', 'Solicitado'), ('SUPERVISOR_APPROVE', 'Pré-aprovado pelo Supervisor'), ('HR_APPROVE', 'Aprovado pelo RH'), ('REJECT', 'Rejeitado'), ('CANCEL', 'Cancelado'), ('COMMENT', 'Comentário adicionado')], max_length=30)),
                ('note', models.TextField(blank=True, null=True)),
                ('performed_at', models.DateTimeField(auto_now_add=True)),
                ('leave_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='leave.leaverequest')),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log de Ação',
                'verbose_name_plural': 'Logs de Ação',
                'ordering': ['performed_at'],
            },
        ),
    ]
