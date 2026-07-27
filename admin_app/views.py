from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (Organization, LegalEntity, Location, Subunit, JobTitle, JobCategory, EmploymentStatus,
                     PayGrade, WorkShift, Education, Skill, Language, License, Membership,
                     Nationality, CurrencyType, City, Province, Country)
from django import forms


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        exclude = []
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'street1': forms.TextInput(attrs={'class': 'form-control'}),
            'street2': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class LegalEntityForm(forms.ModelForm):
    class Meta:
        model = LegalEntity
        fields = ['name', 'tax_id', 'registration_number', 'phone', 'email', 'address', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'country', 'province', 'city', 'neighborhood', 'address', 'address_number', 'zip_code', 'phone', 'fax', 'note', 'latitude', 'longitude', 'radius_meters', 'allowed_ipv4']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'address_number': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'radius_meters': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowed_ipv4': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 177.10.20.30'}),
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome da cidade...'}),
        }

class SubunitForm(forms.ModelForm):
    class Meta:
        model = Subunit
        fields = ['name', 'description', 'parent', 'supervisor', 'allow_shift_swaps']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'allow_shift_swaps': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class JobTitleForm(forms.ModelForm):
    class Meta:
        model = JobTitle
        fields = ['title', 'description', 'note']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class WorkShiftForm(forms.ModelForm):
    class Meta:
        model = WorkShift
        fields = ['name', 'hours_per_day', 'start_time', 'end_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'hours_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
        }


def make_simple_form(model_class, field='name'):
    class SimpleForm(forms.ModelForm):
        class Meta:
            model = model_class
            fields = [field]
            widgets = {field: forms.TextInput(attrs={'class': 'form-control'})}
    return SimpleForm


def _admin_required(request):
    if not (request.user.is_admin() or request.user.is_hr()):
        messages.error(request, 'Acesso restrito a administradores ou RH.')
        return False
    return True




@login_required
def organization_view(request):
    if not _admin_required(request):
        return redirect('dashboard')
    org = Organization.objects.first()
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados da organizacao atualizados!')
            return redirect('organization')
    else:
        form = OrganizationForm(instance=org)
    return render(request, 'admin_app/organization.html', {'form': form, 'org': org})




@login_required
def legal_entity_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    entities = LegalEntity.objects.all()
    return render(request, 'admin_app/legal_entity_list.html', {'entities': entities})

@login_required
def legal_entity_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = LegalEntityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa/Filial criada!')
            return redirect('legal_entity_list')
    else:
        form = LegalEntityForm()
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Nova Empresa/Filial'})

@login_required
def legal_entity_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(LegalEntity, pk=pk)
    if request.method == 'POST':
        form = LegalEntityForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa/Filial atualizada!')
            return redirect('legal_entity_list')
    else:
        form = LegalEntityForm(instance=obj)
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Editar Empresa/Filial'})



@login_required
def location_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    locations = Location.objects.all()
    return render(request, 'admin_app/location_list.html', {'locations': locations})


@login_required
def location_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localizacao criada!')
            return redirect('location_list')
    else:
        form = LocationForm()
    return render(request, 'admin_app/location_form.html', {'form': form, 'title': 'Nova Localizacao'})

@login_required
def location_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localizacao atualizada!')
            return redirect('location_list')
    else:
        form = LocationForm(instance=obj)
    return render(request, 'admin_app/location_form.html', {'form': form, 'title': 'Editar Localizacao'})


@login_required
def location_delete(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(Location, pk=pk)
    obj.delete()
    messages.success(request, 'Removido!')
    return redirect('location_list')




@login_required
def city_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    cities = City.objects.select_related('province').all()
    return render(request, 'admin_app/city_list.html', {'objects': cities, 'title': 'Cidades Base'})

@login_required
def city_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.save(commit=False)
            
            api_state = request.POST.get('api_state')
            api_country = request.POST.get('api_country')
            api_country_code = request.POST.get('api_country_code')
            
            if not city.province and api_state and api_country:
                country, _ = Country.objects.get_or_create(
                    code=api_country_code[:3].upper() if api_country_code else 'INT',
                    defaults={'name': api_country}
                )
                province, _ = Province.objects.get_or_create(
                    name=api_state,
                    country=country,
                    defaults={'code': api_state[:10].upper()}
                )
                city.province = province
                
            city.save()
            messages.success(request, 'Cidade criada!')
            return redirect('city_list')
    else:
        form = CityForm()
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Nova Cidade Base'})

@login_required
def city_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(City, pk=pk)
    form = CityForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        city = form.save(commit=False)
        
        api_state = request.POST.get('api_state')
        api_country = request.POST.get('api_country')
        api_country_code = request.POST.get('api_country_code')
        
        
        if not city.province and api_state and api_country:
            country, _ = Country.objects.get_or_create(
                code=api_country_code[:3].upper() if api_country_code else 'INT',
                defaults={'name': api_country}
            )
            province, _ = Province.objects.get_or_create(
                name=api_state,
                country=country,
                defaults={'code': api_state[:10].upper()}
            )
            city.province = province
            
        city.save()
        messages.success(request, 'Cidade atualizada!')
        return redirect('city_list')
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Editar Cidade'})



@login_required
def subunit_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    subunits = Subunit.objects.select_related('parent').order_by('parent__name', 'name')
    for sub in subunits:
        sub.edit_form = SubunitForm(instance=sub, prefix=f"edit_{sub.pk}")
    return render(request, 'admin_app/subunit_list.html', {'subunits': subunits, 'form': SubunitForm()})


@login_required
def subunit_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = SubunitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento criado!')
            return redirect('subunit_list')
    else:
        form = SubunitForm()
    return render(request, 'admin_app/subunit_form.html', {'form': form, 'title': 'Nova Unidade', 'action': 'Nova'})


@login_required
def subunit_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    subunit = get_object_or_404(Subunit, pk=pk)
    if request.method == 'POST':
        form = SubunitForm(request.POST, instance=subunit, prefix=f"edit_{pk}")
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento atualizado!')
            return redirect('subunit_list')
    else:
        form = SubunitForm(instance=subunit, prefix=f"edit_{pk}")
    return render(request, 'admin_app/subunit_form.html', {'form': form, 'title': 'Editar Unidade', 'action': 'Editar'})




@login_required
def job_title_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    titles = JobTitle.objects.filter(is_deleted=False)
    return render(request, 'admin_app/job_title_list.html', {'titles': titles})


@login_required
def job_title_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = JobTitleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo criado!')
            return redirect('job_title_list')
    else:
        form = JobTitleForm()
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Novo Cargo'})


@login_required
def job_title_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(JobTitle, pk=pk)
    if request.method == 'POST':
        form = JobTitleForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo atualizado!')
            return redirect('job_title_list')
    else:
        form = JobTitleForm(instance=obj)
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Editar Cargo'})




@login_required
def job_category_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, JobCategory, 'job_category_list', 'Categoria de Cargo')

@login_required
def job_category_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, JobCategory, pk, 'job_category_list', 'Categoria de Cargo')

@login_required
def work_shift_list(request):
    if not _admin_required(request):
        return redirect('dashboard')
    shifts = WorkShift.objects.all()
    return render(request, 'admin_app/work_shift_list.html', {'shifts': shifts})


@login_required
def work_shift_create(request):
    if not _admin_required(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = WorkShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno criado!')
            return redirect('work_shift_list')
    else:
        form = WorkShiftForm()
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Novo Turno'})


@login_required
def work_shift_edit(request, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    obj = get_object_or_404(WorkShift, pk=pk)
    if request.method == 'POST':
        form = WorkShiftForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno atualizado!')
            return redirect('work_shift_list')
    else:
        form = WorkShiftForm(instance=obj)
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': 'Editar Turno'})




def _simple_crud(request, model_class, list_url, title, field='name'):
    Form = make_simple_form(model_class, field)
    objects = model_class.objects.all()
    form = Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{title} criado(a)!')
        return redirect(list_url)
    return render(request, 'admin_app/simple_crud.html', {
        'objects': objects, 'form': form, 'title': title
    })


def _simple_edit(request, model_class, pk, list_url, title, field='name'):
    Form = make_simple_form(model_class, field)
    obj = get_object_or_404(model_class, pk=pk)
    form = Form(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{title} atualizado(a)!')
        return redirect(list_url)
    return render(request, 'admin_app/admin_form.html', {'form': form, 'title': f'Editar {title}'})


@login_required
def nationality_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, Nationality, 'nationality_list', 'Nacionalidade')

@login_required
def nationality_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, Nationality, pk, 'nationality_list', 'Nacionalidade')

@login_required
def skill_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, Skill, 'skill_list', 'Habilidade')

@login_required
def skill_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, Skill, pk, 'skill_list', 'Habilidade')

@login_required
def language_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, Language, 'language_list', 'Idioma')

@login_required
def language_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, Language, pk, 'language_list', 'Idioma')

@login_required
def license_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, License, 'license_list', 'Licenca')

@login_required
def license_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, License, pk, 'license_list', 'Licenca')

@login_required
def membership_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, Membership, 'membership_list', 'Filiacao')

@login_required
def membership_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, Membership, pk, 'membership_list', 'Filiacao')

@login_required
def education_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, Education, 'education_list', 'Nivel de Educacao')

@login_required
def education_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, Education, pk, 'education_list', 'Nivel de Educacao')

@login_required
def employment_status_list(request):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_crud(request, EmploymentStatus, 'employment_status_list', 'Status de Emprego')

@login_required
def employment_status_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    return _simple_edit(request, EmploymentStatus, pk, 'employment_status_list', 'Status de Emprego')

@login_required
def termination_reason_list(request):
    if not _admin_required(request): return redirect('dashboard')
    from pim.models import TerminationReason
    return _simple_crud(request, TerminationReason, 'termination_reason_list', 'Motivos de Desligamento')

@login_required
def termination_reason_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    from pim.models import TerminationReason
    return _simple_edit(request, TerminationReason, pk, 'termination_reason_list', 'Motivo de Desligamento')

@login_required
def pay_grade_list(request):
    if not _admin_required(request): return redirect('dashboard')
    pay_grades = PayGrade.objects.all()
    return render(request, 'admin_app/pay_grade_list.html', {'pay_grades': pay_grades})

@login_required
def pay_grade_create(request):
    if not _admin_required(request): return redirect('dashboard')
    currencies = CurrencyType.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        currency_id = request.POST.get('currency')
        min_sal = request.POST.get('min_salary')
        max_sal = request.POST.get('max_salary')
        if name:
            pg = PayGrade.objects.create(name=name)
            if currency_id:
                from admin_app.models import PayGradeCurrency
                PayGradeCurrency.objects.create(
                    pay_grade=pg,
                    currency_id=currency_id,
                    min_salary=min_sal if min_sal else None,
                    max_salary=max_sal if max_sal else None
                )
            messages.success(request, 'Faixa Salarial criada com sucesso!')
            return redirect('pay_grade_list')
    return render(request, 'admin_app/pay_grade_form.html', {'currencies': currencies, 'action': 'Nova'})

@login_required
def pay_grade_edit(request, pk):
    if not _admin_required(request): return redirect('dashboard')
    pg = get_object_or_404(PayGrade, pk=pk)
    from admin_app.models import PayGradeCurrency
    pg_currency = PayGradeCurrency.objects.filter(pay_grade=pg).first()
    currencies = CurrencyType.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        currency_id = request.POST.get('currency')
        min_sal = request.POST.get('min_salary')
        max_sal = request.POST.get('max_salary')
        if name:
            pg.name = name
            pg.save()
            if currency_id:
                if pg_currency:
                    pg_currency.currency_id = currency_id
                    pg_currency.min_salary = min_sal if min_sal else None
                    pg_currency.max_salary = max_sal if max_sal else None
                    pg_currency.save()
                else:
                    PayGradeCurrency.objects.create(
                        pay_grade=pg,
                        currency_id=currency_id,
                        min_salary=min_sal if min_sal else None,
                        max_salary=max_sal if max_sal else None
                    )
            elif pg_currency:
                pg_currency.delete()
            messages.success(request, 'Faixa Salarial atualizada!')
            return redirect('pay_grade_list')
    return render(request, 'admin_app/pay_grade_form.html', {'pg': pg, 'pg_currency': pg_currency, 'currencies': currencies, 'action': 'Editar'})


@login_required
def delete_generic(request, model_name, pk):
    if not _admin_required(request):
        return redirect('dashboard')
    from pim.models import TerminationReason
    model_map = {
        'nationality': Nationality, 'skill': Skill, 'language': Language,
        'license': License, 'membership': Membership, 'education': Education,
        'employment_status': EmploymentStatus, 'location': Location, 'legal_entity': LegalEntity,
        'subunit': Subunit, 'job_title': JobTitle, 'job_category': JobCategory, 'work_shift': WorkShift,
        'pay_grade': PayGrade, 'city': City, 'termination_reason': TerminationReason,
    }
    redirect_map = {
        'nationality': 'nationality_list', 'skill': 'skill_list', 'language': 'language_list',
        'license': 'license_list', 'membership': 'membership_list', 'education': 'education_list',
        'employment_status': 'employment_status_list', 'location': 'location_list', 'legal_entity': 'legal_entity_list',
        'subunit': 'subunit_list', 'job_title': 'job_title_list', 'job_category': 'job_category_list', 'work_shift': 'work_shift_list',
        'pay_grade': 'pay_grade_list', 'city': 'city_list', 'termination_reason': 'termination_reason_list',
    }
    model_class = model_map.get(model_name)
    if model_class:
        obj = get_object_or_404(model_class, pk=pk)
        obj.delete()
        messages.success(request, 'Removido com sucesso!')
    return redirect(redirect_map.get(model_name, 'dashboard'))
