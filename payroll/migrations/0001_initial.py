

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pim', '0005_alter_employee_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payslip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_month', models.IntegerField(verbose_name='Mês Referência')),
                ('reference_year', models.IntegerField(verbose_name='Ano Referência')),
                ('base_salary', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Salário Base')),
                ('total_earnings', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Total Proventos')),
                ('total_deductions', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Total Descontos')),
                ('net_pay', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Líquido a Receber')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('pending', 'Pendente (Aguardando Assinatura)'), ('signed', 'Assinado')], default='draft', max_length=20, verbose_name='Status')),
                ('signed_at', models.DateTimeField(blank=True, null=True, verbose_name='Data/Hora da Assinatura')),
                ('signed_ip', models.CharField(blank=True, max_length=45, null=True, verbose_name='IP do Signatário')),
                ('signature_hash', models.CharField(blank=True, max_length=255, null=True, verbose_name='Código Hash de Autenticidade')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payslips', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Holerite',
                'verbose_name_plural': 'Holerites',
                'unique_together': {('employee', 'reference_month', 'reference_year')},
            },
        ),
        migrations.CreateModel(
            name='PayslipItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255, verbose_name='Descrição')),
                ('reference', models.CharField(blank=True, help_text='Ex: 220h, 50%, 11%', max_length=100, null=True, verbose_name='Referência')),
                ('item_type', models.CharField(choices=[('earning', 'Provento (Vencimento)'), ('deduction', 'Desconto')], max_length=20, verbose_name='Tipo')),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Valor')),
                ('payslip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='payroll.payslip')),
            ],
            options={
                'verbose_name': 'Item do Holerite',
                'verbose_name_plural': 'Itens do Holerite',
            },
        ),
    ]
