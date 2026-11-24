from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator


class RegistroForm(forms.Form):
    escola_nome = forms.CharField(label='Nome da escola', max_length=255)
    username = forms.CharField(
        label='Usuario',
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    email = forms.EmailField(label='Email')
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)
    password = forms.CharField(label='Senha', strip=False)
    password_confirm = forms.CharField(label='Confirmacao de senha', strip=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este usuario ja existe.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este email ja esta registrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas nao conferem.')
        elif password:
            usuario = User(
                username=cleaned_data.get('username', ''),
                email=cleaned_data.get('email', ''),
                first_name=cleaned_data.get('escola_nome', '')[:150],
            )
            try:
                validate_password(password, usuario)
            except forms.ValidationError as erro:
                self.add_error('password', erro)

        return cleaned_data


class PerfilForm(forms.Form):
    escola_nome = forms.CharField(label='Nome da escola', max_length=255)
    email = forms.EmailField(label='Email')
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('Este email ja esta em uso por outra conta.')
        return email
