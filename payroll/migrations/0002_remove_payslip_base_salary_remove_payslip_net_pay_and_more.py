

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payslip',
            name='base_salary',
        ),
        migrations.RemoveField(
            model_name='payslip',
            name='net_pay',
        ),
        migrations.RemoveField(
            model_name='payslip',
            name='total_deductions',
        ),
        migrations.RemoveField(
            model_name='payslip',
            name='total_earnings',
        ),
        migrations.AddField(
            model_name='payslip',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='payslips/', verbose_name='Arquivo PDF'),
        ),
        migrations.AlterField(
            model_name='payslip',
            name='status',
            field=models.CharField(choices=[('pending', 'Aguardando Assinatura'), ('signed', 'Assinado')], default='pending', max_length=20, verbose_name='Status'),
        ),
        migrations.DeleteModel(
            name='PayslipItem',
        ),
    ]
