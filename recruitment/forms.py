from django import forms
from django.utils.safestring import mark_safe
from itertools import groupby

from .models import JobOpening, Candidate, Interview, InterviewFeedback, Skill, PublicApplication
from pim.models import Employee


# ---------------------------------------------------------------------------
# Grouped checkbox widget for skills
# ---------------------------------------------------------------------------
class GroupedSkillCheckboxWidget(forms.CheckboxSelectMultiple):
    """Renders skill checkboxes grouped by category with styled labels."""

    def optgroups(self, name, value, attrs=None):
        # Sort choices by category
        groups = []
        for category, category_label in Skill.CATEGORY_CHOICES:
            skills = Skill.objects.filter(category=category)
            subgroup = []
            for skill in skills:
                option_value = str(skill.pk)
                option_label = skill.name
                selected = option_value in value
                subgroup.append(
                    self.create_option(
                        name, option_value, option_label,
                        selected, len(groups),
                        attrs=attrs,
                    )
                )
            if subgroup:
                groups.append((category_label, subgroup, len(groups)))
        return groups


class JobOpeningForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Skills Obrigatórias",
    )
    desired_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Skills Desejáveis",
    )

    class Meta:
        model = JobOpening
        fields = ['title', 'department', 'job_title', 'description', 'quantity', 'status', 'required_skills', 'desired_skills']
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Desenvolvedor Python'}),
            'department':  forms.Select(attrs={'class': 'form-select'}),
            'job_title':   forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Requisitos, atribuições...'}),
            'quantity':    forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50}),
            'status':      forms.Select(attrs={'class': 'form-select'}),
        }


class CandidateForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Skills",
    )

    class Meta:
        model = Candidate
        fields = ['name', 'email', 'phone', 'linkedin_url', 'resume', 'job_opening',
                  'skills', 'current_stage', 'status']
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email':        forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'candidato@email.com'}),
            'phone':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}),
            'resume':       forms.FileInput(attrs={'class': 'form-control'}),
            'job_opening':  forms.Select(attrs={'class': 'form-select'}),
            'current_stage':forms.Select(attrs={'class': 'form-select'}),
            'status':       forms.Select(attrs={'class': 'form-select'}),
        }


class PublicApplicationForm(forms.ModelForm):
    """Form used on the public (unauthenticated) candidate portal."""
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Suas Skills",
        help_text="Selecione todas as skills que você domina ou tem conhecimento.",
    )

    class Meta:
        model = PublicApplication
        fields = ['name', 'email', 'phone', 'linkedin_url', 'resume', 'skills']
        widgets = {
            'name':         forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Seu nome completo',
            }),
            'email':        forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'seu@email.com',
            }),
            'phone':        forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000',
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/seu-perfil (opcional)',
            }),
            'resume':       forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.job_opening = kwargs.pop('job_opening', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        if email and self.job_opening:
            if PublicApplication.objects.filter(email=email, job_opening=self.job_opening).exists():
                raise forms.ValidationError(
                    "Este e-mail já possui uma candidatura registrada para esta vaga. "
                    "Não é possível se inscrever duas vezes."
                )
        return cleaned


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['candidate', 'stage', 'date', 'interviewers', 'notes', 'status']
        widgets = {
            'candidate':    forms.Select(attrs={'class': 'form-select'}),
            'stage':        forms.Select(attrs={'class': 'form-select'}),
            'date':         forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'interviewers': forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': 'multiple'}),
            'notes':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Pauta, link da sala...'}),
            'status':       forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interviewers'].queryset = Employee.objects.filter(state=Employee.STATE_ACTIVE)


class InterviewFeedbackForm(forms.ModelForm):
    class Meta:
        model = InterviewFeedback
        fields = ['score', 'feedback_text']
        widgets = {
            'score':         forms.Select(attrs={'class': 'form-select'}),
            'feedback_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escreva uma avaliação do candidato...'}),
        }
