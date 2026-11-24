from django import forms

from .models import Aluno


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'responsavel', 'telefone', 'email']

    def clean_telefone(self):
        telefone = self.cleaned_data['telefone'].strip()
        digitos = ''.join(filter(str.isdigit, telefone))
        if not 10 <= len(digitos) <= 13:
            raise forms.ValidationError('Informe um telefone valido com DDD.')
        return telefone
