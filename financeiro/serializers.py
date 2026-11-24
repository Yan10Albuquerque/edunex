from rest_framework import serializers

from .models import Mensalidade


class MensalidadeBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensalidade
        fields = ['usuario', 'aluno', 'valor', 'data_vencimento']

    def validate_valor(self, valor):
        if valor <= 0:
            raise serializers.ValidationError('O valor deve ser maior que zero.')
        return valor

    def validate(self, attrs):
        if attrs['aluno'].usuario_id != attrs['usuario'].pk:
            raise serializers.ValidationError(
                {'aluno': 'O aluno informado nao pertence a este usuario.'}
            )
        return attrs
