from django import forms

from core.models import Aluno

from .models import Mensalidade


class MensalidadeForm(forms.ModelForm):
    class Meta:
        model = Mensalidade
        fields = ['aluno', 'valor', 'data_vencimento', 'status', 'recorrente', 'data_fim_recorrencia']

    def __init__(self, *args, usuario, edit=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aluno'].queryset = Aluno.objects.filter(usuario=usuario)
        if edit:
            # O aluno nao muda na edicao.
            del self.fields['aluno']
        else:
            # O status de uma nova mensalidade e calculado automaticamente.
            del self.fields['status']

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor is not None and valor <= 0:
            raise forms.ValidationError('O valor deve ser maior que zero.')
        return valor

    def clean(self):
        cleaned_data = super().clean()
        vencimento = cleaned_data.get('data_vencimento')
        fim = cleaned_data.get('data_fim_recorrencia')
        if vencimento and fim and fim < vencimento:
            self.add_error(
                'data_fim_recorrencia',
                'A data final da recorrencia nao pode ser anterior ao vencimento.',
            )
        return cleaned_data
