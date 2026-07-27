import os
import zipfile
from io import BytesIO
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from pim.models import Employee
from .models import Payslip

@login_required
def payroll_dashboard(request):
    """
    Dashboard de RH para anexar PDFs de folha de pagamento do mês.
    """
    try:
        month = int(request.GET.get('month', timezone.now().month))
        year = int(request.GET.get('year', timezone.now().year))
    except ValueError:
        month = timezone.now().month
        year = timezone.now().year
        
    
    is_su = getattr(request.user, 'is_superuser', False)
    is_ad = request.user.is_admin() if hasattr(request.user, 'is_admin') and callable(request.user.is_admin) else getattr(request.user, 'is_admin', False)
    is_rh = request.user.is_hr() if hasattr(request.user, 'is_hr') and callable(request.user.is_hr) else getattr(request.user, 'is_hr', False)
    
    
    is_mine = request.GET.get('mine') == '1'
    has_permission = (is_su or is_ad or is_rh) and not is_mine
    
    from leave.models import LeaveRequest
    from admin_app.models import Subunit
    from django.db.models import Q
    
    search_query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department_id', '')
    
    if has_permission:
        payslips_query = Payslip.objects.filter(reference_month=month, reference_year=year)
        leave_docs_query = LeaveRequest.objects.exclude(attachment='')
        
        if search_query:
            payslips_query = payslips_query.filter(
                Q(employee__first_name__icontains=search_query) | 
                Q(employee__last_name__icontains=search_query)
            )
            leave_docs_query = leave_docs_query.filter(
                Q(employee__first_name__icontains=search_query) | 
                Q(employee__last_name__icontains=search_query)
            )
            
        if department_id:
            payslips_query = payslips_query.filter(employee__subunit_id=department_id)
            leave_docs_query = leave_docs_query.filter(employee__subunit_id=department_id)
            
        payslips = payslips_query.order_by('employee__first_name')
        employees = Employee.objects.filter(state=Employee.STATE_ACTIVE).order_by('first_name')
        leave_docs = leave_docs_query.order_by('-date_applied')[:100]
        departments = Subunit.objects.all().order_by('name')
    else:
        
        if hasattr(request.user, 'employee') and request.user.employee:
            payslips = Payslip.objects.filter(employee=request.user.employee).order_by('-reference_year', '-reference_month')
            leave_docs = LeaveRequest.objects.filter(employee=request.user.employee).exclude(attachment='').order_by('-date_applied')
        else:
            payslips = []
            leave_docs = []
        employees = []
        departments = []
    
    if request.method == 'POST' and has_permission:
        
        if 'zip_file' in request.FILES:
            upload_month = int(request.POST.get('month', month))
            upload_year = int(request.POST.get('year', year))
            zip_file = request.FILES.get('zip_file')
            
            success_count = 0
            errors = []
            
            try:
                import unicodedata
                
                def remove_accents(input_str):
                    if not input_str:
                        return ""
                    nfkd_form = unicodedata.normalize('NFKD', input_str)
                    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

                with zipfile.ZipFile(zip_file, 'r') as z:
                    for file_info in z.infolist():
                        if file_info.is_dir() or not file_info.filename.lower().endswith('.pdf') or '__MACOSX' in file_info.filename:
                            continue
                            
                        
                        filename = file_info.filename.split('/')[-1]
                        clean_name = filename.rsplit('.', 1)[0].strip().lower()
                        clean_name_normalized = remove_accents(clean_name)
                        
                        matched_emp = None
                        
                        for emp in employees:
                            emp_full = emp.full_name.strip().lower()
                            emp_full_normalized = remove_accents(emp_full)
                            
                            emp_first = emp.first_name.strip().lower()
                            emp_first_normalized = remove_accents(emp_first)
                            
                            
                            if (clean_name_normalized == emp_full_normalized or 
                                clean_name_normalized == emp_first_normalized or 
                                clean_name_normalized in emp_full_normalized):
                                matched_emp = emp
                                break
                                
                        if matched_emp:
                            pdf_content = z.read(file_info.filename)
                            
                            payslip, created = Payslip.objects.get_or_create(
                                employee=matched_emp,
                                reference_month=upload_month,
                                reference_year=upload_year,
                            )
                            
                            payslip.document.save(filename, ContentFile(pdf_content), save=False)
                            payslip.status = Payslip.STATUS_PENDING
                            payslip.signature_hash = None
                            payslip.signed_at = None
                            payslip.signed_ip = None
                            payslip.save()
                            success_count += 1
                        else:
                            errors.append(filename)
                            
                msg = f"Sucesso: {success_count} holerites vinculados e importados do ZIP."
                if errors:
                    msg += f" Erro: {len(errors)} arquivos não encontraram dono (Verifique o nome exato: {', '.join(errors[:5])}{'...' if len(errors)>5 else ''})"
                    messages.warning(request, msg)
                else:
                    messages.success(request, msg)
                    
            except zipfile.BadZipFile:
                messages.error(request, "O arquivo enviado não é um ZIP válido.")
                
            return redirect(f'/payroll/?month={upload_month}&year={upload_year}')
            
        
        emp_id = request.POST.get('employee_id')
        upload_month = int(request.POST.get('month', month))
        upload_year = int(request.POST.get('year', year))
        pdf_file = request.FILES.get('document')
        
        if emp_id and pdf_file:
            employee = get_object_or_404(Employee, id=emp_id)
            
            payslip, created = Payslip.objects.get_or_create(
                employee=employee,
                reference_month=upload_month,
                reference_year=upload_year,
            )
            payslip.document = pdf_file
            payslip.status = Payslip.STATUS_PENDING
            payslip.signature_hash = None
            payslip.signed_at = None
            payslip.signed_ip = None
            payslip.save()
            
            messages.success(request, f"Holerite de {employee.first_name} anexado com sucesso!")
            return redirect(f'/payroll/?month={upload_month}&year={upload_year}')
            
    MONTHS_PT = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    context = {
        'payslips': payslips,
        'leave_docs': leave_docs,
        'employees': employees,
        'departments': departments,
        'current_month': month,
        'current_year': year,
        'months': MONTHS_PT,
        'years': [timezone.now().year - 1, timezone.now().year, timezone.now().year + 1],
        'is_hr': has_permission,
        'search_query': search_query,
        'department_id': int(department_id) if department_id else '',
    }
    return render(request, 'payroll/payroll_dashboard.html', context)

@login_required
def payslip_detail(request, pk):
    """
    Visualização do holerite (PDF embutido).
    """
    payslip = get_object_or_404(Payslip, pk=pk)
    
    
    if not getattr(request.user, 'is_hr', False) and not request.user.is_superuser:
        if payslip.employee.id != getattr(request.user, 'employee_id', None):
            messages.error(request, "Acesso Negado.")
            return redirect('core_dashboard')

    return render(request, 'payroll/payslip_detail.html', {'payslip': payslip})

@login_required
def payslip_sign(request, pk):
    """
    Processa a assinatura digital do funcionário.
    """
    payslip = get_object_or_404(Payslip, pk=pk)
    
    if request.method == 'POST' and payslip.status == Payslip.STATUS_PENDING:
        
        password = request.POST.get('password')
        signature_image = request.POST.get('signature_image')
        
        if not signature_image or not signature_image.startswith('data:image'):
            messages.error(request, "Por favor, desenhe sua assinatura antes de confirmar.")
            return redirect('payslip_detail', pk=pk)
            
        if request.user.check_password(password):
            
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
                
            success = payslip.sign_document(ip_address=ip, signature_base64=signature_image)
            if success:
                messages.success(request, "Holerite assinado digitalmente com sucesso!")
            else:
                messages.error(request, "Falha ao assinar. Verifique o status ou arquivo.")
        else:
            messages.error(request, "Senha incorreta. A assinatura não foi realizada.")
            
    return redirect('payslip_detail', pk=pk)

@login_required
def payslip_delete(request, pk):
    """
    Deleta o holerite (Apenas RH ou Superuser)
    """
    payslip = get_object_or_404(Payslip, pk=pk)
    
    is_su = getattr(request.user, 'is_superuser', False)
    is_ad = request.user.is_admin() if hasattr(request.user, 'is_admin') and callable(request.user.is_admin) else getattr(request.user, 'is_admin', False)
    is_rh = request.user.is_hr() if hasattr(request.user, 'is_hr') and callable(request.user.is_hr) else getattr(request.user, 'is_hr', False)
    
    if not (is_su or is_ad or is_rh):
        messages.error(request, "Acesso Negado.")
        return redirect('payroll_dashboard')
        
    if request.method == 'POST':
        month = payslip.reference_month
        year = payslip.reference_year
        
        if payslip.document:
            try:
                payslip.document.delete(save=False)
            except Exception as e:
                pass
        
        payslip.delete()
        messages.success(request, "Holerite apagado com sucesso!")
        return redirect(f'/payroll/?month={month}&year={year}')
        
    return redirect('payroll_dashboard')

@login_required
def payslip_delete_all(request, year, month):
    """
    Deleta todos os holerites de um determinado mês e ano (Apenas RH ou Superuser)
    """
    is_su = getattr(request.user, 'is_superuser', False)
    is_ad = request.user.is_admin() if hasattr(request.user, 'is_admin') and callable(request.user.is_admin) else getattr(request.user, 'is_admin', False)
    is_rh = request.user.is_hr() if hasattr(request.user, 'is_hr') and callable(request.user.is_hr) else getattr(request.user, 'is_hr', False)
    
    if not (is_su or is_ad or is_rh):
        messages.error(request, "Acesso Negado.")
        return redirect('payroll_dashboard')
        
    if request.method == 'POST':
        payslips = Payslip.objects.filter(reference_year=year, reference_month=month)
        count = payslips.count()
        
        for payslip in payslips:
            if payslip.document:
                try:
                    payslip.document.delete(save=False)
                except Exception as e:
                    pass
                    
        payslips.delete()
        messages.success(request, f"{count} holerite(s) apagado(s) com sucesso!")
        
    return redirect(f'/payroll/?month={month}&year={year}')
