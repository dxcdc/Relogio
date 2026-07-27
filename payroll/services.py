from django.utils import timezone
from pim.models import Employee, EmployeeSalary
from .models import Payslip, PayslipItem
from decimal import Decimal

def generate_payslips_for_month(year, month):
    """
    Gera holerites (rascunhos) para todos os funcionários ativos que tenham salário base cadastrado.
    """
    employees = Employee.objects.filter(state=Employee.STATE_ACTIVE)
    created_count = 0
    
    for emp in employees:
        
        salary_record = EmployeeSalary.objects.filter(employee=emp).first()
        if not salary_record or not salary_record.amount:
            continue
            
        
        payslip, created = Payslip.objects.get_or_create(
            employee=emp,
            reference_month=month,
            reference_year=year,
            defaults={'base_salary': salary_record.amount, 'status': Payslip.STATUS_DRAFT}
        )
        
        if not created and payslip.status != Payslip.STATUS_DRAFT:
            
            continue
            
        if created:
            created_count += 1
            
            
            PayslipItem.objects.create(
                payslip=payslip,
                description='Salário Base',
                reference='Mensalista',
                item_type=PayslipItem.TYPE_EARNING,
                amount=salary_record.amount
            )
            
            
            inss_value = salary_record.amount * Decimal('0.09') 
            PayslipItem.objects.create(
                payslip=payslip,
                description='INSS (Estimativa)',
                reference='9%',
                item_type=PayslipItem.TYPE_DEDUCTION,
                amount=round(inss_value, 2)
            )
                    
            
            payslip.update_totals()
            
    return created_count
