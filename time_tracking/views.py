from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer, Project, ProjectActivity, Timesheet, TimesheetItem
from django import forms
from pim.utils import get_visible_employees


class TimesheetForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class TimesheetItemForm(forms.ModelForm):
    class Meta:
        model = TimesheetItem
        fields = ['project', 'activity', 'date', 'duration', 'comment']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'duration': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'placeholder': 'HH:MM'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['customer', 'name', 'description']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }




@login_required
def timesheet_list(request):
    user = request.user
    visible_employees = get_visible_employees(user)
    timesheets = Timesheet.objects.filter(employee__in=visible_employees).select_related('employee').order_by('-start_date')
    return render(request, 'time_tracking/timesheet_list.html', {'timesheets': timesheets})


@login_required
def timesheet_detail(request, pk):
    visible_employees = get_visible_employees(request.user)
    timesheet = get_object_or_404(
        Timesheet.objects.prefetch_related('items__project', 'items__activity').filter(employee__in=visible_employees), 
        pk=pk
    )
    return render(request, 'time_tracking/timesheet_detail.html', {'timesheet': timesheet})


@login_required
def timesheet_create(request):
    emp = getattr(request.user, 'employee', None)
    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            ts = form.save(commit=False)
            ts.employee = emp
            ts.save()
            messages.success(request, 'Timesheet criado!')
            return redirect('timesheet_detail', pk=ts.pk)
    else:
        form = TimesheetForm()
    return render(request, 'time_tracking/timesheet_form.html', {'form': form, 'title': 'Novo Timesheet'})


@login_required
def timesheet_delete(request, pk):
    visible_employees = get_visible_employees(request.user)
    ts = get_object_or_404(Timesheet.objects.filter(employee__in=visible_employees), pk=pk)
    emp = getattr(request.user, 'employee', None)
    if not request.user.is_supervisor() and (not emp or ts.employee != emp):
        messages.error(request, 'Voce nao tem permissao para excluir este timesheet.')
        return redirect('timesheet_list')
    ts.delete()
    messages.success(request, 'Timesheet excluido.')
    return redirect('timesheet_list')


@login_required
def timesheet_submit(request, pk):
    visible_employees = get_visible_employees(request.user)
    ts = get_object_or_404(Timesheet.objects.filter(employee__in=visible_employees), pk=pk)
    ts.state = Timesheet.STATUS_SUBMITTED
    ts.save()
    messages.success(request, 'Timesheet enviado para aprovacao!')
    return redirect('timesheet_detail', pk=pk)


@login_required
def timesheet_approve(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    visible_employees = get_visible_employees(request.user)
    ts = get_object_or_404(Timesheet.objects.filter(employee__in=visible_employees), pk=pk)
    ts.state = Timesheet.STATUS_APPROVED
    ts.save()
    messages.success(request, 'Timesheet aprovado!')
    return redirect('timesheet_detail', pk=pk)


@login_required
def timesheet_reject(request, pk):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    visible_employees = get_visible_employees(request.user)
    ts = get_object_or_404(Timesheet.objects.filter(employee__in=visible_employees), pk=pk)
    ts.state = Timesheet.STATUS_NOT_SUBMITTED
    ts.save()
    messages.warning(request, 'Timesheet rejeitado e devolvido ao funcionario.')
    return redirect('timesheet_detail', pk=pk)


@login_required
def timesheet_item_add(request, ts_pk):
    visible_employees = get_visible_employees(request.user)
    ts = get_object_or_404(Timesheet.objects.filter(employee__in=visible_employees), pk=ts_pk)
    if request.method == 'POST':
        form = TimesheetItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.timesheet = ts
            item.save()
            messages.success(request, 'Horas lancadas!')
            return redirect('timesheet_detail', pk=ts_pk)
    else:
        form = TimesheetItemForm()
    return render(request, 'time_tracking/timesheet_form.html', {
        'form': form, 'timesheet': ts, 'title': 'Lancar Horas'
    })


@login_required
def timesheet_item_delete(request, pk):
    visible_employees = get_visible_employees(request.user)
    item = get_object_or_404(TimesheetItem.objects.select_related('timesheet'), pk=pk)
    if item.timesheet.employee not in visible_employees:
        messages.error(request, 'Acesso negado.')
        return redirect('timesheet_list')
    ts_pk = item.timesheet_id
    item.delete()
    messages.success(request, 'Lancamento removido.')
    return redirect('timesheet_detail', pk=ts_pk)




@login_required
def project_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    projects = Project.objects.filter(is_deleted=False).select_related('customer')
    return render(request, 'time_tracking/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projeto criado!')
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'time_tracking/timesheet_form.html', {'form': form, 'title': 'Novo Projeto'})


@login_required
def project_edit(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projeto atualizado!')
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'time_tracking/timesheet_form.html', {'form': form, 'title': 'Editar Projeto'})


@login_required
def project_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    project = get_object_or_404(Project, pk=pk)
    project.is_deleted = True
    project.save()
    messages.success(request, 'Projeto excluido.')
    return redirect('project_list')




@login_required
def customer_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')
    customers = Customer.objects.filter(is_deleted=False)
    return render(request, 'time_tracking/customer_list.html', {'customers': customers})


@login_required
def customer_create(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente criado!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'time_tracking/timesheet_form.html', {'form': form, 'title': 'Novo Cliente'})


@login_required
def customer_edit(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado!')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'time_tracking/timesheet_form.html', {'form': form, 'title': 'Editar Cliente'})


@login_required
def customer_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_deleted = True
    customer.save()
    messages.success(request, 'Cliente excluido.')
    return redirect('customer_list')
