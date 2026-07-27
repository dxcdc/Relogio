from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import require_module
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import (Employee, EmpDependent, EmpEmergencyContact, EmpWorkExperience,
                     EmployeeEducation, EmployeeSkill, EmployeeLanguage, EmployeeLicense,
                     EmployeeMembership, EmployeeSalary, EmpPicture, EmployeeImmigrationRecord,
                     EmployeeAttachment, EmployeeTerminationRecord, EmpContract)
from .forms import (EmployeePersonalForm, EmployeeJobForm, EmployeeContactForm,
                    DependentForm, EmergencyContactForm, WorkExperienceForm, EducationForm,
                    SkillForm, LanguageForm, SalaryForm, ImmigrationRecordForm, TerminationForm)
from .utils import get_visible_employees, supervisor_can_access_employee
import csv
from django.http import HttpResponse


from django.urls import reverse
def redirect_with_popup(request, *args, **kwargs):
    from django.shortcuts import redirect
    response = redirect(*args, **kwargs)
    if getattr(request, 'GET', {}).get('popup') or getattr(request, 'POST', {}).get('popup'):
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(response.url)
        new_query = parsed.query + ('&' if parsed.query else '') + 'popup=1'
        new_url = urlunparse(parsed._replace(query=new_query))
        response['Location'] = new_url
    return response



def _can_edit_employee(request, employee):
    """Return True if current user is allowed to view/edit this employee's profile."""
    return supervisor_can_access_employee(request.user, employee)

def _can_edit_personal_data(request, employee):
    """Return True if user can edit dependencies, contact, qualifications, etc."""
    is_self = getattr(request.user, 'employee', None) == employee
    return is_self or request.user.is_admin() or request.user.is_hr()


@login_required
def employee_list(request):
    if not request.user.is_supervisor():
        emp = getattr(request.user, 'employee', None)
        if emp:
            return redirect_with_popup(request, 'employee_detail', pk=emp.pk)
        messages.warning(request, 'Seu usuário não está vinculado a um funcionário.')
        return redirect_with_popup(request, 'dashboard')
    q = request.GET.get('q', '')
    department = request.GET.get('department', '')
    company = request.GET.get('company', '')
    status = request.GET.get('status', 'ACTIVE')

    
    employees = get_visible_employees(request.user)

    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(employee_id__icontains=q) | Q(work_email__icontains=q)
        )
    if department:
        employees = employees.filter(sub_division_id=department)
    if company:
        employees = employees.filter(legal_entity_id=company)
    if status:
        employees = employees.filter(state=status)
    employees = employees.select_related('job_title', 'sub_division', 'emp_status', 'legal_entity')
    paginator = Paginator(employees, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    from admin_app.models import Subunit, LegalEntity
    
    if request.user.is_admin():
        departments = Subunit.objects.all()
        companies = LegalEntity.objects.all()
    else:
        my_emp = getattr(request.user, 'employee', None)
        if my_emp and my_emp.sub_division:
            departments = Subunit.objects.filter(pk=my_emp.sub_division.pk)
        else:
            departments = Subunit.objects.none()
            
        if my_emp and my_emp.legal_entity:
            companies = LegalEntity.objects.filter(pk=my_emp.legal_entity.pk)
        else:
            companies = LegalEntity.objects.none()

    return render(request, 'pim/employee_list.html', {
        'page_obj': page_obj, 'departments': departments, 'companies': companies,
        'q': q, 'selected_department': department, 'selected_company': company, 'selected_status': status,
    })


@login_required
def employee_export(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito.')
        return redirect_with_popup(request, 'dashboard')
        
    q = request.GET.get('q', '')
    department = request.GET.get('department', '')
    company = request.GET.get('company', '')
    status = request.GET.get('status', 'ACTIVE')

    employees = get_visible_employees(request.user)

    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(employee_id__icontains=q) | Q(work_email__icontains=q)
        )
    if department:
        employees = employees.filter(sub_division_id=department)
    if company:
        employees = employees.filter(legal_entity_id=company)
    if status:
        employees = employees.filter(state=status)
    employees = employees.select_related('job_title', 'sub_division', 'emp_status', 'legal_entity')

    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="funcionarios.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Nome', 'Email Corporativo', 'Empresa Contratante', 'Departamento', 'Cargo', 'Status', 'Admissão'])

    for emp in employees:
        writer.writerow([
            emp.employee_id or '',
            emp.full_name or '',
            emp.work_email or '',
            emp.legal_entity.name if emp.legal_entity else 'Sem Empresa',
            emp.sub_division.name if emp.sub_division else 'Sem Departamento',
            emp.job_title.title if emp.job_title else '',
            emp.get_state_display() or '',
            emp.joined_date.strftime('%d/%m/%Y') if emp.joined_date else '',
        ])

    return response



@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee.objects.select_related(
        'job_title', 'sub_division', 'emp_status', 'nationality', 'work_shift'
    ), pk=pk)
    if not _can_edit_employee(request, employee):
        messages.error(request, 'Você não tem permissão para ver este perfil.')
        return redirect_with_popup(request, 'dashboard')
        
    is_self = getattr(request.user, 'employee', None) == employee
    can_manage_job = request.user.is_admin() or request.user.is_hr()
    can_edit_personal = is_self or request.user.is_admin() or request.user.is_hr()
    
    if request.method == 'POST' and can_edit_personal:
        if request.POST.get('action') == 'personal_data':
            from core.audit import log_action
            
            
            
            
            
            
            if 'first_name' in request.POST: employee.first_name = request.POST.get('first_name')
            if 'last_name' in request.POST: employee.last_name = request.POST.get('last_name')
            if 'nick_name' in request.POST: employee.nick_name = request.POST.get('nick_name')
            
            bd = request.POST.get('birthday')
            if bd: employee.birthday = bd
            
            if 'gender' in request.POST: 
                gender_val = request.POST.get('gender')
                try:
                    employee.gender = int(gender_val) if gender_val else None
                except ValueError:
                    
                    mapping = {'M': 1, 'F': 2, 'O': 3, 'Masculino': 1, 'Feminino': 2}
                    employee.gender = mapping.get(str(gender_val).strip()[:1].upper(), None)

            if 'marital_status' in request.POST: 
                ms_val = request.POST.get('marital_status')
                employee.marital_status = ms_val if ms_val else None

            if 'nationality' in request.POST: 
                nat_val = request.POST.get('nationality')
                if nat_val:
                    if str(nat_val).strip().isdigit():
                        employee.nationality_id = int(str(nat_val).strip())
                    else:
                        
                        from admin_app.models import Nationality
                        nat_obj = Nationality.objects.filter(name__iexact=str(nat_val).strip()).first()
                        if nat_obj:
                            employee.nationality_id = nat_obj.pk
                        else:
                            
                            employee.nationality_id = None
                else:
                    employee.nationality_id = None
            if 'ssn_number' in request.POST: employee.ssn_number = request.POST.get('ssn_number')
            if 'driving_license_no' in request.POST: employee.driving_license_no = request.POST.get('driving_license_no')
            
            cnh_exp = request.POST.get('driving_license_expired_date')
            if cnh_exp: employee.driving_license_expired_date = cnh_exp
            
            employee.save()
            log_action(request, 'UPDATE', f'Atualizou os dados pessoais de {employee.full_name} via PIM.')
            messages.success(request, 'Dados pessoais atualizados com sucesso.')
            return redirect_with_popup(request, 'employee_detail', pk=pk)

    import json
    
    supervisors = employee.supervisors.filter(state=Employee.STATE_ACTIVE).select_related('job_title')
    subordinates = Employee.objects.filter(supervisors=employee, state=Employee.STATE_ACTIVE).select_related('job_title')

    supervisor_org_data = json.dumps([{
        'pk': s.pk, 'name': s.full_name, 'job_title': str(s.job_title) if s.job_title else '—'
    } for s in supervisors])
    subordinate_org_data = json.dumps([{
        'pk': s.pk, 'name': s.full_name, 'job_title': str(s.job_title) if s.job_title else '—'
    } for s in subordinates])
    current_org_data = json.dumps({
        'pk': employee.pk, 'name': employee.full_name, 'job_title': str(employee.job_title) if employee.job_title else '—'
    })
    from admin_app.models import Nationality
    nationalities = Nationality.objects.all().order_name() if hasattr(Nationality.objects, 'order_name') else Nationality.objects.all().order_by('name')

    return render(request, 'pim/employee_detail.html', {
        'employee': employee,
        'supervisor_org_data': supervisor_org_data,
        'subordinate_org_data': subordinate_org_data,
        'current_org_data': current_org_data,
        'is_self': is_self,
        'can_manage_job': can_manage_job,
        'can_edit_personal': can_edit_personal,
        'nationalities': nationalities,
    })



@login_required
def employee_create(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Apenas Recursos Humanos e Administradores podem cadastrar funcionários.')
        return redirect_with_popup(request, 'dashboard')

    def _generate_employee_id():
        """Gera o próximo ID sequencial no formato EMP-XXXX."""
        last = Employee.objects.filter(
            employee_id__startswith='EMP-'
        ).order_by('-employee_id').first()
        if last and last.employee_id:
            try:
                num = int(last.employee_id.split('-')[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        candidate = f'EMP-{num:04d}'
        
        while Employee.objects.filter(employee_id=candidate).exists():
            num += 1
            candidate = f'EMP-{num:04d}'
        return candidate

    if request.method == 'POST':
        form = EmployeePersonalForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            if not employee.employee_id:
                employee.employee_id = _generate_employee_id()
            employee.save()
            from core.audit import log_action
            log_action(request, 'EMP_CREATE',
                f'{request.user.username} cadastrou o funcionário {employee.full_name} '
                f'(ID: {employee.employee_id}).')
            messages.success(request, f'Funcionário {employee.full_name} criado com sucesso!')
            return redirect_with_popup(request, 'employee_detail', pk=employee.pk)
    else:
        next_id = _generate_employee_id()
        form = EmployeePersonalForm(initial={'employee_id': next_id})
    return render(request, 'pim/employee_form.html', {'form': form, 'title': 'Novo Funcionário'})


@login_required
def employee_personal_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EmployeePersonalForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados pessoais atualizados!')
            return redirect_with_popup(request, 'employee_detail', pk=pk)
    else:
        form = EmployeePersonalForm(instance=employee)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Editar Dados Pessoais'
    })


@login_required
def employee_job_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a RH e Administradores.')
        return redirect_with_popup(request, 'dashboard')
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeJobForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados de emprego atualizados!')
            return redirect_with_popup(request, 'employee_detail', pk=pk)
    else:
        form = EmployeeJobForm(instance=employee)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Editar Informações de Emprego'
    })


@login_required
def employee_contact_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EmployeeContactForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados de contato atualizados!')
            return redirect_with_popup(request, 'employee_detail', pk=pk)
    else:
        form = EmployeeContactForm(instance=employee)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Editar Contato'
    })


@login_required
def employee_photo_upload(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para alterar a foto deste funcionário.')
        return redirect_with_popup(request, 'dashboard')
        
    if request.method == 'POST' and request.FILES.get('photo'):
        photo_file = request.FILES['photo']
        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
        MAX_SIZE_MB = 5
        if photo_file.content_type not in ALLOWED_TYPES:
            messages.error(request, 'Tipo de arquivo inválido. Envie apenas JPEG, PNG ou WebP.')
        elif photo_file.size > MAX_SIZE_MB * 1024 * 1024:
            messages.error(request, f'Foto muito grande. Tamanho máximo permitido: {MAX_SIZE_MB}MB.')
        else:
            EmpPicture.objects.update_or_create(
                employee=employee,
                defaults={
                    'picture': photo_file,
                    'file_name': photo_file.name,
                    'file_type': photo_file.content_type,
                }
            )
            messages.success(request, 'Foto atualizada com sucesso!')
    from django.utils.http import url_has_allowed_host_and_scheme
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect_with_popup(request, next_url)
    return redirect_with_popup(request, 'employee_detail', pk=pk)




@login_required
def dependent_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = DependentForm(request.POST)
        if form.is_valid():
            dep = form.save(commit=False)
            dep.employee = employee
            dep.save()
            messages.success(request, 'Dependente adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = DependentForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Dependente'
    })


@login_required
def dependent_edit(request, pk):
    dep = get_object_or_404(EmpDependent, pk=pk)
    if not _can_edit_personal_data(request, dep.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = DependentForm(request.POST, instance=dep)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dependente atualizado!')
            return redirect_with_popup(request, 'employee_detail', pk=dep.employee.pk)
    else:
        form = DependentForm(instance=dep)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': dep.employee, 'title': 'Editar Dependente'
    })


@login_required
def dependent_delete(request, pk):
    dep = get_object_or_404(EmpDependent, pk=pk)
    if not _can_edit_personal_data(request, dep.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = dep.employee.pk
    dep.delete()
    messages.success(request, 'Dependente removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def emergency_contact_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.employee = employee
            contact.save()
            messages.success(request, 'Contato de emergência adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = EmergencyContactForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Contato de Emergência'
    })


@login_required
def emergency_contact_edit(request, pk):
    contact = get_object_or_404(EmpEmergencyContact, pk=pk)
    if not _can_edit_personal_data(request, contact.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contato atualizado!')
            return redirect_with_popup(request, 'employee_detail', pk=contact.employee.pk)
    else:
        form = EmergencyContactForm(instance=contact)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': contact.employee, 'title': 'Editar Contato de Emergência'
    })


@login_required
def emergency_contact_delete(request, pk):
    contact = get_object_or_404(EmpEmergencyContact, pk=pk)
    if not _can_edit_personal_data(request, contact.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = contact.employee.pk
    contact.delete()
    messages.success(request, 'Contato removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def work_experience_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.employee = employee
            exp.save()
            messages.success(request, 'Experiência adicionada!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = WorkExperienceForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Experiência Profissional'
    })


@login_required
def work_experience_edit(request, pk):
    exp = get_object_or_404(EmpWorkExperience, pk=pk)
    if not _can_edit_personal_data(request, exp.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, 'Experiência atualizada!')
            return redirect_with_popup(request, 'employee_detail', pk=exp.employee.pk)
    else:
        form = WorkExperienceForm(instance=exp)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': exp.employee, 'title': 'Editar Experiência Profissional'
    })


@login_required
def work_experience_delete(request, pk):
    exp = get_object_or_404(EmpWorkExperience, pk=pk)
    if not _can_edit_personal_data(request, exp.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = exp.employee.pk
    exp.delete()
    messages.success(request, 'Experiência removida!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def education_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            ed = form.save(commit=False)
            ed.employee = employee
            ed.save()
            messages.success(request, 'Formação adicionada!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = EducationForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Formação'
    })


@login_required
def education_edit(request, pk):
    ed = get_object_or_404(EmployeeEducation, pk=pk)
    if not _can_edit_personal_data(request, ed.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=ed)
        if form.is_valid():
            form.save()
            messages.success(request, 'Formação atualizada!')
            return redirect_with_popup(request, 'employee_detail', pk=ed.employee.pk)
    else:
        form = EducationForm(instance=ed)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': ed.employee, 'title': 'Editar Formação'
    })


@login_required
def education_delete(request, pk):
    ed = get_object_or_404(EmployeeEducation, pk=pk)
    if not _can_edit_personal_data(request, ed.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = ed.employee.pk
    ed.delete()
    messages.success(request, 'Formação removida!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def skill_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            sk = form.save(commit=False)
            sk.employee = employee
            sk.save()
            messages.success(request, 'Habilidade adicionada!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = SkillForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Habilidade'
    })


@login_required
def skill_edit(request, pk):
    sk = get_object_or_404(EmployeeSkill, pk=pk)
    if not _can_edit_personal_data(request, sk.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=sk)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habilidade atualizada!')
            return redirect_with_popup(request, 'employee_detail', pk=sk.employee.pk)
    else:
        form = SkillForm(instance=sk)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': sk.employee, 'title': 'Editar Habilidade'
    })


@login_required
def skill_delete(request, pk):
    sk = get_object_or_404(EmployeeSkill, pk=pk)
    if not _can_edit_personal_data(request, sk.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = sk.employee.pk
    sk.delete()
    messages.success(request, 'Habilidade removida!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def language_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            lang = form.save(commit=False)
            lang.employee = employee
            lang.save()
            messages.success(request, 'Idioma adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = LanguageForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Idioma'
    })


@login_required
def language_edit(request, pk):
    lang = get_object_or_404(EmployeeLanguage, pk=pk)
    if not _can_edit_personal_data(request, lang.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = LanguageForm(request.POST, instance=lang)
        if form.is_valid():
            form.save()
            messages.success(request, 'Idioma atualizado!')
            return redirect_with_popup(request, 'employee_detail', pk=lang.employee.pk)
    else:
        form = LanguageForm(instance=lang)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': lang.employee, 'title': 'Editar Idioma'
    })


@login_required
def language_delete(request, pk):
    lang = get_object_or_404(EmployeeLanguage, pk=pk)
    if not _can_edit_personal_data(request, lang.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = lang.employee.pk
    lang.delete()
    messages.success(request, 'Idioma removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def license_create(request, emp_pk):
    from .forms import LicenseForm
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            lic = form.save(commit=False)
            lic.employee = employee
            lic.save()
            messages.success(request, 'Licenca adicionada!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = LicenseForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Licenca'
    })


@login_required
def license_edit(request, pk):
    from .forms import LicenseForm
    lic = get_object_or_404(EmployeeLicense, pk=pk)
    if not _can_edit_personal_data(request, lic.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = LicenseForm(request.POST, instance=lic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Licenca atualizada!')
            return redirect_with_popup(request, 'employee_detail', pk=lic.employee.pk)
    else:
        form = LicenseForm(instance=lic)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': lic.employee, 'title': 'Editar Licenca'
    })


@login_required
def license_delete(request, pk):
    lic = get_object_or_404(EmployeeLicense, pk=pk)
    if not _can_edit_personal_data(request, lic.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = lic.employee.pk
    lic.delete()
    messages.success(request, 'Licenca removida!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def membership_create(request, emp_pk):
    from .forms import MembershipForm
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = MembershipForm(request.POST)
        if form.is_valid():
            mem = form.save(commit=False)
            mem.employee = employee
            mem.save()
            messages.success(request, 'Filiacao adicionada!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = MembershipForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Filiacao'
    })


@login_required
def membership_edit(request, pk):
    from .forms import MembershipForm
    mem = get_object_or_404(EmployeeMembership, pk=pk)
    if not _can_edit_personal_data(request, mem.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=mem)
        if form.is_valid():
            form.save()
            messages.success(request, 'Filiacao atualizada!')
            return redirect_with_popup(request, 'employee_detail', pk=mem.employee.pk)
    else:
        form = MembershipForm(instance=mem)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': mem.employee, 'title': 'Editar Filiacao'
    })


@login_required
def membership_delete(request, pk):
    mem = get_object_or_404(EmployeeMembership, pk=pk)
    if not _can_edit_personal_data(request, mem.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = mem.employee.pk
    mem.delete()
    messages.success(request, 'Filiacao removida!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def immigration_create(request, emp_pk):
    employee = get_object_or_404(Employee, pk=emp_pk)
    if not _can_edit_personal_data(request, employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = ImmigrationRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.employee = employee
            rec.save()
            messages.success(request, 'Documento adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = ImmigrationRecordForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Documento de Imigracao'
    })


@login_required
def immigration_edit(request, pk):
    rec = get_object_or_404(EmployeeImmigrationRecord, pk=pk)
    if not _can_edit_personal_data(request, rec.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = ImmigrationRecordForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento atualizado!')
            return redirect_with_popup(request, 'employee_detail', pk=rec.employee.pk)
    else:
        form = ImmigrationRecordForm(instance=rec)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': rec.employee, 'title': 'Editar Documento'
    })


@login_required
def immigration_delete(request, pk):
    rec = get_object_or_404(EmployeeImmigrationRecord, pk=pk)
    if not _can_edit_personal_data(request, rec.employee):
        messages.error(request, 'Você não tem permissão para editar estes dados.')
        return redirect_with_popup(request, 'dashboard')
    emp_pk = rec.employee.pk
    rec.delete()
    messages.success(request, 'Documento removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def salary_create(request, emp_pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a Recursos Humanos e Gestão.')
        return redirect_with_popup(request, 'dashboard')
    employee = get_object_or_404(Employee, pk=emp_pk)
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            salary = form.save(commit=False)
            salary.employee = employee
            salary.save()
            messages.success(request, 'Salario adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = SalaryForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Salario'
    })


@login_required
def salary_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a Recursos Humanos e Gestão.')
        return redirect_with_popup(request, 'dashboard')
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salario atualizado!')
            return redirect_with_popup(request, 'employee_detail', pk=salary.employee.pk)
    else:
        form = SalaryForm(instance=salary)
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': salary.employee, 'title': 'Editar Salario'
    })


@login_required
def salary_delete(request, pk):
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    emp_pk = salary.employee.pk
    salary.delete()
    messages.success(request, 'Salario removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def contract_create(request, emp_pk):
    from .forms import ContractForm
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a Recursos Humanos e Gestão.')
        return redirect_with_popup(request, 'dashboard')
    employee = get_object_or_404(Employee, pk=emp_pk)
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            c = form.save(commit=False)
            c.employee = employee
            c.save()
            messages.success(request, 'Contrato adicionado!')
            return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    else:
        form = ContractForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Adicionar Contrato'
    })


@login_required
def contract_delete(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a Recursos Humanos e Gestão.')
        return redirect_with_popup(request, 'dashboard')
    c = get_object_or_404(EmpContract, pk=pk)
    emp_pk = c.employee.pk
    c.delete()
    messages.success(request, 'Contrato removido!')
    return redirect_with_popup(request, 'employee_detail', pk=emp_pk)




@login_required
def terminate_employee(request, pk):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Apenas administradores e RH podem desligar funcionarios.')
        return redirect_with_popup(request, 'employee_list')
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = TerminationForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.employee = employee
            record.save()
            employee.state = Employee.STATE_TERMINATED
            employee.termination_record = record
            employee.save()
            from core.audit import log_action
            log_action(request, 'EMP_TERMINATE',
                f'{request.user.username} desligou o funcionário {employee.full_name} '
                f'(ID: {employee.employee_id}). Motivo: {record.termination_reason if hasattr(record, "termination_reason") else "N/A"}')
            messages.success(request, f'{employee.full_name} foi desligado.')
            return redirect_with_popup(request, 'employee_list')
    else:
        form = TerminationForm()
    return render(request, 'pim/employee_form.html', {
        'form': form, 'employee': employee, 'title': 'Desligar Funcionario'
    })




@login_required
@require_module('org_chart')
def org_chart_view(request):
    """View que renderiza a página do organograma."""
    from admin_app.models import Subunit
    departments = Subunit.objects.all().order_by('name')
    employees = Employee.objects.filter(state=Employee.STATE_ACTIVE).order_by('first_name', 'last_name')
    context = {
        'departments': departments,
        'employees': employees,
        'is_admin_user': request.user.role in ['Admin', 'HR']
    }
    return render(request, 'pim/org_chart.html', context)

@login_required
def api_org_chart_data(request):
    """Retorna os dados dos funcionários ativos para o organograma."""
    from django.http import JsonResponse
    from admin_app.models import LegalEntity
    
    
    qs = Employee.objects.filter(state=Employee.STATE_ACTIVE).select_related(
        'job_title', 'sub_division', 'picture', 'legal_entity'
    ).prefetch_related('supervisors')
    
    can_edit_all = request.user.role in ['Admin', 'HR']
    my_emp_id = str(request.user.employee.id) if hasattr(request.user, 'employee') and request.user.employee else None
    
    
    data = [{
        "id": "root",
        "parentId": "",
        "name": "Matriz / Grupo",
        "positionName": "Nível Máximo",
        "department": "",
        "imageUrl": "",
        "canEdit": can_edit_all
    }]
    
    
    legal_entities = LegalEntity.objects.all()
    for entity in legal_entities:
        data.append({
            "id": f"entity_{entity.id}",
            "parentId": "root",
            "name": entity.name,
            "positionName": f"CNPJ: {entity.tax_id}",
            "department": "Empresa",
            "imageUrl": "",
            "canEdit": can_edit_all,
            "legalEntityId": str(entity.id)
        })
        
    
    data.append({
        "id": "entity_none",
        "parentId": "root",
        "name": "Pessoas Sem Empresa Definida",
        "positionName": "Unbound",
        "department": "Aviso",
        "imageUrl": "",
        "canEdit": can_edit_all
    })
    
    for emp in qs:
        first_supervisor = emp.supervisors.first()
        
        
        if first_supervisor:
            parent_id = str(first_supervisor.id)
        else:
            if emp.legal_entity:
                parent_id = f"entity_{emp.legal_entity.id}"
            else:
                parent_id = "entity_none"
                
        
        image_url = ""
        if hasattr(emp, 'picture') and emp.picture and emp.picture.picture:
            image_url = emp.picture.picture.url
            
        
        job_title = emp.job_title.title if emp.job_title else "Sem Cargo"
        department = emp.sub_division.name if emp.sub_division else ""
        
        
        from core.models import OrangeUser
        user_account = OrangeUser.objects.filter(employee=emp).first()
        is_sup = user_account.role == 'Supervisor' if user_account else False
        
        can_edit = can_edit_all
        node = {
            "id": str(emp.id),
            "parentId": parent_id,
            "name": emp.full_name,
            "positionName": job_title,
            "department": department,
            "imageUrl": image_url,
            "isSupervisor": is_sup,
            "canEdit": can_edit,
            "legalEntityName": emp.legal_entity.name if emp.legal_entity else "",
            "legalEntityId": str(emp.legal_entity.id) if emp.legal_entity else ""
        }
        data.append(node)
        
    return JsonResponse(data, safe=False)

@login_required
def api_org_chart_assign(request):
    """Atribui subordinados a um supervisor específico (individual ou lote por departamento)."""
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            supervisor_id = data.get('supervisor_id')
            assign_type = data.get('assign_type')  
            target_id = data.get('target_id')
            
            if not supervisor_id or str(supervisor_id) == 'root' or not target_id:
                return JsonResponse({'success': False, 'message': 'Dados incompletos.'})
                
            
            needs_approval = request.user.role not in ['Admin', 'HR']
            
            if needs_approval:
                my_emp = getattr(request.user, 'employee', None)
                if not my_emp or str(my_emp.id) != str(supervisor_id):
                    return JsonResponse({'success': False, 'message': 'Sem permissão. Você só pode atribuir subordinados a si mesmo.'})
                
            supervisor = Employee.objects.get(pk=supervisor_id)
            from .models import OrgHierarchyRequest
            
            if assign_type == 'employee':
                emp = Employee.objects.get(pk=target_id)
                if emp.id == supervisor.id:
                    return JsonResponse({'success': False, 'message': 'Não pode vincular a si mesmo.'})
                    
                if needs_approval:
                    OrgHierarchyRequest.objects.create(
                        requester=my_emp,
                        supervisor=supervisor,
                        target_employee=emp
                    )
                    return JsonResponse({'success': True, 'message': 'Solicitação enviada! Aguardando aprovação do RH.'})
                else:
                    emp.supervisors.clear()
                    emp.supervisors.add(supervisor)
                    
                    emp.sub_division = supervisor.sub_division
                    emp.save(update_fields=['sub_division'])
                    return JsonResponse({'success': True, 'message': '1 funcionário vinculado com sucesso.'})
                
            elif assign_type == 'department':
                from django.db.models import Q
                from admin_app.models import Subunit
                subunit = Subunit.objects.get(pk=target_id)
                
                
                
                emps = Employee.objects.filter(
                    Q(sub_division_id=target_id) | Q(job_title__title__icontains=subunit.name)
                ).exclude(id=supervisor.id)
                
                count = 0
                for emp in emps:
                    
                    
                    if not emp.sub_division:
                        emp.sub_division = subunit
                        emp.save(update_fields=['sub_division'])
                        
                    emp.supervisors.clear()
                    emp.supervisors.add(supervisor)
                    count += 1
            else:
                return JsonResponse({'success': False, 'message': 'Tipo inválido.'})
                
            return JsonResponse({'success': True, 'message': f'{count} funcionário(s) vinculados ao gestor {supervisor.first_name}.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})


@login_required
def api_org_chart_requests(request):
    """
    GET: Lista solicitações pendentes.
    POST: Aprova ou Rejeita uma solicitação.
    Apenas Admin/HR podem operar.
    """
    from django.http import JsonResponse
    
    if request.user.role not in ['Admin', 'HR']:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
        
    from .models import OrgHierarchyRequest
    
    if request.method == 'GET':
        qs = OrgHierarchyRequest.objects.filter(status='PENDING').select_related(
            'requester', 'supervisor', 'target_employee', 'target_department'
        )
        data = []
        for req in qs:
            target_str = req.target_employee.full_name if req.target_employee else f"Setor {req.target_department.name}"
            data.append({
                'id': req.id,
                'requester': req.requester.full_name,
                'supervisor': req.supervisor.full_name,
                'target': target_str,
                'date': req.created_at.strftime('%d/%m/%Y %H:%M')
            })
        return JsonResponse({'success': True, 'requests': data})
        
    elif request.method == 'POST':
        import json
        from django.utils import timezone
        
        try:
            body = json.loads(request.body)
            req_id = body.get('request_id')
            action = body.get('action') 
            
            if not req_id or action not in ['APP', 'REJ']:
                return JsonResponse({'success': False, 'message': 'Parâmetros inválidos.'})
                
            req_obj = OrgHierarchyRequest.objects.get(pk=req_id)
            if req_obj.status != 'PENDING':
                return JsonResponse({'success': False, 'message': 'Solicitação já resolvida.'})
                
            if action == 'REJ':
                req_obj.status = 'REJECTED'
                req_obj.resolved_at = timezone.now()
                req_obj.resolved_by = request.user
                req_obj.save()
                return JsonResponse({'success': True, 'message': 'Solicitação rejeitada.'})
                
            elif action == 'APP':
                
                from django.db.models import Q
                supervisor = req_obj.supervisor
                
                if req_obj.target_employee:
                    emp = req_obj.target_employee
                    emp.supervisors.clear()
                    emp.supervisors.add(supervisor)
                    emp.sub_division = supervisor.sub_division
                    emp.save(update_fields=['sub_division'])
                elif req_obj.target_department:
                    subunit = req_obj.target_department
                    emps = Employee.objects.filter(
                        Q(sub_division_id=subunit.id) | Q(job_title__title__icontains=subunit.name)
                    ).exclude(id=supervisor.id)
                    for emp in emps:
                        if not emp.sub_division:
                            emp.sub_division = subunit
                            emp.save(update_fields=['sub_division'])
                        emp.supervisors.clear()
                        emp.supervisors.add(supervisor)
                        
                req_obj.status = 'APPROVED'
                req_obj.resolved_at = timezone.now()
                req_obj.resolved_by = request.user
                req_obj.save()
                
                return JsonResponse({'success': True, 'message': 'Solicitação Aprovada! O Organograma foi alterado.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})




@login_required
@require_module('org_chart')
def organization_chart(request):
    import json
    from admin_app.models import LegalEntity, Subunit
    from pim.models import Employee

    nodes = []

    
    nodes.append({
        "id": "root", 
        "parentId": "", 
        "name": "Ecossistema", 
        "positionName": "Grupo Organizacional",
        "imageUrl": "https://img.icons8.com/color/96/network-company.png",
        "type": "root"
    })

    
    ceo_qs = Employee.objects.filter(first_name__in=['LÍDIA', 'VICTOR', 'NEY'])
    ceo_data_list = []
    for c in ceo_qs:
        try:
            if hasattr(c, 'picture') and c.picture and c.picture.picture:
                img = c.picture.picture.url
            else:
                img = f"https://ui-avatars.com/api/?name={c.first_name}&background=e2e8f0&color=475569"
        except:
            img = f"https://ui-avatars.com/api/?name={c.first_name}&background=e2e8f0&color=475569"
        ceo_data_list.append({"name": c.first_name, "img": img})

    nodes.append({
        "id": "board",
        "parentId": "root",
        "name": "Conselho de Sócios",
        "type": "board",
        "ceos": ceo_data_list
    })

    
    first_le_id = None
    for le in LegalEntity.objects.all():
        if not first_le_id:
            first_le_id = le.id
        nodes.append({
            "id": f"le_{le.id}",
            "parentId": "board", 
            "name": le.name,
            "positionName": f"CNPJ: {le.tax_id or 'Matriz'}",
            "imageUrl": "https://img.icons8.com/color/96/company.png",
            "type": "company"
        })

    
    supervisor_ids = set()
    all_emps = Employee.objects.prefetch_related('supervisors')
    for e in all_emps:
        for sup in e.supervisors.all():
            supervisor_ids.add(sup.id)

    
    for emp in Employee.objects.select_related('job_title', 'sub_division', 'legal_entity').prefetch_related('supervisors', 'picture'):
        
        if emp.first_name in ['LÍDIA', 'VICTOR', 'NEY']:
            continue
            
        
        
        
        if emp.supervisors.exists():
            pid = f"emp_{emp.supervisors.first().id}"
        elif emp.legal_entity_id:
            pid = f"le_{emp.legal_entity_id}"
        else:
            pid = f"le_{first_le_id}" if first_le_id else "board"

        try:
            if hasattr(emp, 'picture') and emp.picture and emp.picture.picture:
                img_url = emp.picture.picture.url
            else:
                img_url = f"https://ui-avatars.com/api/?name={emp.full_name.replace(' ', '+')}&background=2563eb&color=fff"
        except Exception:
            img_url = f"https://ui-avatars.com/api/?name={emp.full_name.replace(' ', '+')}&background=2563eb&color=fff"
            
        nodes.append({
            "id": f"emp_{emp.id}",
            "parentId": pid,
            "name": emp.full_name,
            "positionName": str(emp.job_title) if emp.job_title else "Sem Cargo",
            "imageUrl": img_url,
            "type": "employee",
            "is_supervisor": emp.id in supervisor_ids
        })

    org_data_json = json.dumps(nodes)
    return render(request, 'pim/org_chart.html', {'org_data_json': org_data_json})


@login_required
def employee_onboarding_dashboard(request):
    from django.contrib import messages
    from django.db import transaction
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    from .utils import generate_uppercase_username, generate_random_temp_password
    from core.models import OrangeUser
    from admin_app.models import JobTitle, Subunit, LegalEntity
    from .models import Employee

    # Restrição de segurança: Apenas Admin ou RH
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito ao Recursos Humanos.')
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile = request.POST.get('mobile', '').strip()
        job_title_text = request.POST.get('job_title', '').strip()
        department_text = request.POST.get('department', '').strip()
        legal_entity_text = request.POST.get('legal_entity', '').strip()

        if not first_name or not last_name or not email:
            messages.error(request, 'Nome, Sobrenome e E-mail são obrigatórios.')
        else:
            try:
                with transaction.atomic():
                    # 1. Resolução dinâmica de entidades
                    job_title = None
                    if job_title_text:
                        job_title, _ = JobTitle.objects.get_or_create(title=job_title_text)
                    
                    subunit = None
                    if department_text:
                        subunit, _ = Subunit.objects.get_or_create(name=department_text)
                    
                    legal_entity = None
                    if legal_entity_text:
                        legal_entity = LegalEntity.objects.filter(name__iexact=legal_entity_text).first()

                    # 2. Criação do perfil do colaborador
                    # ID sequencial EMP-XXXX automático
                    last_emp = Employee.objects.filter(employee_id__startswith='EMP-').order_by('-employee_id').first()
                    if last_emp and last_emp.employee_id:
                        try:
                            num = int(last_emp.employee_id.split('-')[1]) + 1
                        except (IndexError, ValueError):
                            num = 1
                    else:
                        num = 1
                    emp_id = f'EMP-{num:04d}'
                    while Employee.objects.filter(employee_id=emp_id).exists():
                        num += 1
                        emp_id = f'EMP-{num:04d}'

                    employee = Employee.objects.create(
                        employee_id=emp_id,
                        first_name=first_name,
                        last_name=last_name,
                        work_email=email,
                        mobile=mobile,
                        job_title=job_title,
                        sub_division=subunit,
                        legal_entity=legal_entity,
                        state=Employee.STATE_ACTIVE
                    )

                    # 3. Geração de Credenciais
                    username = generate_uppercase_username(first_name, last_name)
                    temp_password = generate_random_temp_password()

                    # 4. Conta de Usuário
                    user = OrangeUser.objects.create_user(
                        username=username,
                        email=email,
                        password=temp_password,
                        role=OrangeUser.ROLE_ESS,
                        employee=employee
                    )

                    # 5. Envio do E-mail
                    email_sent = False
                    try:
                        from emails.utils import send_custom_email
                        context = {
                            'first_name': first_name,
                            'username': username,
                            'temp_password': temp_password,
                        }
                        
                        email_sent = send_custom_email('onboard_welcome', context, email)
                        if not email_sent:
                            html_content = render_to_string('email/welcome_onboarding.html', context)
                            email_msg = EmailMultiAlternatives(
                                subject="Bem-vindo(a) ao CDC. Suas credenciais de acesso",
                                body=f"Olá, {first_name}! Seu usuário é {username} e sua senha é {temp_password}.",
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@netlineplay.com.br'),
                                to=[email],
                            )
                            email_msg.attach_alternative(html_content, "text/html")
                            email_msg.send(fail_silently=True)
                            email_sent = True
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Erro no e-mail: {e}")

                    msg_text = f"Admissão de {employee.full_name} realizada! Usuário gerado: {username}."
                    if email_sent:
                        msg_text += " E-mail de boas-vindas enviado."
                    else:
                        msg_text += " [ALERTA] Falha ao disparar e-mail."
                    messages.success(request, msg_text)

            except Exception as e:
                messages.error(request, f"Erro inesperado ao realizar admissão: {e}")
                
        return redirect('employee_onboarding_dashboard')

    # GET: Buscar as 10 admissões mais recentes
    recent_employees = Employee.objects.select_related('job_title', 'sub_division', 'legal_entity').order_by('-id')[:10]
    
    # Buscar os dados de token da API de teste do admin se disponível
    api_token = "OBTENHA_O_TOKEN_NA_CENTRAL"
    try:
        from rest_framework.authtoken.models import Token
        token_obj, _ = Token.objects.get_or_create(user=request.user)
        api_token = token_obj.key
    except Exception:
        pass

    return render(request, 'pim/onboarding_dashboard.html', {
        'recent_employees': recent_employees,
        'api_token': api_token,
    })

