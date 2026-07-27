from django import forms
from .models import ChangelogPost, BugReport, BugReportComment


class MultipleFileInput(forms.FileInput):
    """Widget customizado que aceita múltiplos arquivos."""
    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        
        super(forms.FileInput, self).__init__(attrs=default_attrs)


class MultipleFileField(forms.FileField):
    """Campo que aceita lista de arquivos."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        
        if not data:
            return []
        if isinstance(data, list):
            return [super(MultipleFileField, self).clean(d, initial) for d in data]
        return [super(MultipleFileField, self).clean(data, initial)]


class ChangelogPostForm(forms.ModelForm):
    class Meta:
        model = ChangelogPost
        fields = ['title', 'version', 'category', 'content', 'pinned']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Melhorias no sistema de ponto...'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: v1.3.0'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Descreva as mudancas desta versao...'
            }),
            'pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Titulo da Atualizacao',
            'version': 'Versao (opcional)',
            'category': 'Categoria',
            'content': 'Descricao das Mudancas',
            'pinned': 'Fixar no topo',
        }


class BugReportForm(forms.ModelForm):
    screenshots = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'bug-screenshots-input',
        }),
        label='Capturas de Tela (opcional)',
        required=False,
    )

    class Meta:
        model = BugReport
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Botao de ponto nao esta funcionando...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descreva o problema com detalhes: o que aconteceu, o que voce esperava, passos para reproduzir...'
            }),
        }
        labels = {
            'title': 'Titulo do Problema',
            'description': 'Descricao Detalhada',
        }


class BugReportCommentForm(forms.ModelForm):
    class Meta:
        model = BugReportComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escreva sua resposta...'
            }),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'content': 'Resposta',
            'is_internal': 'Nota interna (apenas admins veem)',
        }


class BugStatusForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ['status', 'priority']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'priority': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
