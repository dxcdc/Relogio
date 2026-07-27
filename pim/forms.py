from django import forms
from .models import (Employee, EmpDependent, EmpEmergencyContact, EmpWorkExperience,
                     EmployeeEducation, EmployeeSkill, EmployeeLanguage, EmployeeLicense,
                     EmployeeMembership, EmployeeSalary, EmpContract, EmployeeImmigrationRecord,
                     EmployeeAttachment, EmployeeTerminationRecord)


class EmployeePersonalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'middle_name', 'last_name', 'nick_name',
            'legal_entity', 'birthday', 'gender', 'marital_status', 'nationality',
            'ssn_number', 'other_id', 'driving_license_no', 'driving_license_expired_date',
            'military_service', 'smoker',
        ]
        widgets = {
            'birthday': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'driving_license_expired_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nick_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'style': 'background:#f0f4ff; color:#333; font-weight:600; cursor:not-allowed;'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.Select(attrs={'class': 'form-select'}),
            'ssn_number': forms.TextInput(attrs={'class': 'form-control'}),
            'other_id': forms.TextInput(attrs={'class': 'form-control'}),
            'driving_license_no': forms.TextInput(attrs={'class': 'form-control'}),
            'military_service': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_entity': forms.Select(attrs={'class': 'form-select'}),
        }


class EmployeeJobForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from admin_app.models import Location
        self.fields['locations'].queryset = Location.objects.filter(is_meeting_room=False)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = Employee
        fields = ['legal_entity', 'job_title', 'job_category', 'emp_status', 'sub_division', 'locations', 'joined_date', 'work_shift', 'is_time_tracking_exempt']
        widgets = {
            'legal_entity': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'job_category': forms.Select(attrs={'class': 'form-select'}),
            'emp_status': forms.Select(attrs={'class': 'form-select'}),
            'sub_division': forms.Select(attrs={'class': 'form-select'}),
            'locations': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'joined_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'work_shift': forms.Select(attrs={'class': 'form-select'}),
            'is_time_tracking_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            
            
            sub = instance.sub_division
            if sub and getattr(sub, 'supervisor', None):
                if sub.supervisor != instance:
                    instance.supervisors.set([sub.supervisor])
                else:
                    instance.supervisors.clear()
            else:
                instance.supervisors.clear()
        return instance


class EmployeeContactForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = Employee
        fields = ['street1', 'street2', 'city', 'zipcode',
                  'home_telephone', 'mobile', 'work_telephone', 'work_email', 'other_email']
        widgets = {
            'street1': forms.TextInput(attrs={'class': 'form-control'}),
            'street2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'home_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'work_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'work_email': forms.TextInput(attrs={'class': 'form-control'}),
            'other_email': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DependentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmpDependent
        fields = ['name', 'relationship_type', 'relationship', 'date_of_birth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'relationship_type': forms.Select(attrs={'class': 'form-select'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class EmergencyContactForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmpEmergencyContact
        fields = ['name', 'relationship', 'home_phone', 'mobile_phone', 'office_phone']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'})
                   for f in ['name', 'relationship', 'home_phone', 'mobile_phone', 'office_phone']}


class WorkExperienceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmpWorkExperience
        fields = ['employer', 'job_title', 'from_date', 'to_date', 'comment']
        widgets = {
            'employer': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'from_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EducationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeEducation
        fields = ['education', 'institute', 'major', 'year', 'gpa', 'start_date', 'end_date']
        widgets = {
            'education': forms.Select(attrs={'class': 'form-select'}),
            'institute': forms.TextInput(attrs={'class': 'form-control'}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class SkillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeSkill
        fields = ['skill', 'proficiency', 'years_of_exp', 'comment']
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
            'years_of_exp': forms.NumberInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LanguageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeLanguage
        fields = ['language', 'fluency', 'competency', 'comment']
        widgets = {
            'language': forms.Select(attrs={'class': 'form-select'}),
            'fluency': forms.Select(attrs={'class': 'form-select'}),
            'competency': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LicenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeLicense
        fields = ['license', 'license_no', 'issued_date', 'expiry_date']
        widgets = {
            'license': forms.Select(attrs={'class': 'form-select'}),
            'license_no': forms.TextInput(attrs={'class': 'form-control'}),
            'issued_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class MembershipForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeMembership
        fields = ['membership', 'subscription_paid_by', 'subscription_fee',
                  'subscription_currency', 'subscription_commence_date', 'subscription_renewal_date']
        widgets = {
            'membership': forms.Select(attrs={'class': 'form-select'}),
            'subscription_paid_by': forms.Select(attrs={'class': 'form-select'}),
            'subscription_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subscription_currency': forms.Select(attrs={'class': 'form-select'}),
            'subscription_commence_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'subscription_renewal_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }


class SalaryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeSalary
        fields = ['salary_component', 'payment_frequency', 'currency', 'amount', 'comment']
        widgets = {
            'salary_component': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ImmigrationRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeImmigrationRecord
        fields = ['document_type', 'number', 'issue_date', 'expiry_date', 'issued_by', 'country', 'comment']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'issued_by': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ContractForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmpContract
        fields = ['contract_start_date', 'contract_end_date', 'contract_file']
        widgets = {
            'contract_start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'contract_end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'contract_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class TerminationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = 'Selecione uma opção...'
    class Meta:
        model = EmployeeTerminationRecord
        fields = ['termination_reason', 'date', 'note']
        widgets = {
            'termination_reason': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
