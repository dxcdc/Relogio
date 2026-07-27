

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_app', '0001_initial'),
        ('claim', '0001_initial'),
        ('pim', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='claimevent',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='claimrequest',
            name='claim_event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='claim.claimevent', verbose_name='Evento'),
        ),
        migrations.AddField(
            model_name='claimrequest',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.currencytype', verbose_name='Moeda'),
        ),
        migrations.AddField(
            model_name='claimrequest',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claim_requests', to='pim.employee', verbose_name='Funcionário'),
        ),
        migrations.AddField(
            model_name='claimexpense',
            name='claim_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='claim.claimrequest'),
        ),
        migrations.AddField(
            model_name='claimattachment',
            name='claim_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='claim.claimrequest'),
        ),
        migrations.AddField(
            model_name='expensetype',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='claimexpense',
            name='expense_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='claim.expensetype', verbose_name='Tipo de Despesa'),
        ),
    ]
