from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from .models import OrangeUser


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário', 'id': 'id_username'}),
        label='Usuário'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha', 'id': 'id_password'}),
        label='Senha'
    )


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite a senha'}),
        help_text='Mínimo 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a senha'}),
    )

    class Meta:
        model = OrangeUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'employee']
        labels = {
            'username': 'Usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'role': 'Perfil de Acesso',
            'employee': 'Funcionário Vinculado',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('As senhas não coincidem.')
        return p2

    def clean_password1(self):
        p1 = self.cleaned_data.get('password1', '')
        if p1:
            validate_password(p1)
        return p1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if OrangeUser.objects.filter(email__iexact=email, is_deleted=False).exists():
                raise forms.ValidationError('Este e-mail já está cadastrado em outro usuário.')
        return email


class UserEditForm(forms.ModelForm):
    class Meta:
        model = OrangeUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'employee', 'is_active']
        labels = {
            'username': 'Usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'role': 'Perfil de Acesso',
            'employee': 'Funcionário Vinculado',
            'is_active': 'Conta Ativa',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = OrangeUser.objects.filter(email__iexact=email, is_deleted=False)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Este e-mail já está cadastrado em outro usuário.')
        return email


class UserResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nova senha'}),
        help_text='Mínimo 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a senha'}),
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('As senhas não coincidem.')
        return p2

    def clean_password1(self):
        p1 = self.cleaned_data.get('password1', '')
        if p1:
            validate_password(p1)
        return p1

class AnnouncementForm(forms.ModelForm):
    class Meta:
        from .models import Announcement
        model = Announcement
        fields = ['title', 'content', 'image', 'visibility', 'department', 'expires_at', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Novo Serviço na Copa!'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Escreva a mensagem aqui...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'expires_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
