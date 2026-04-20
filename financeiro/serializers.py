# serializers.py
from rest_framework import serializers
from .models import Mensalidade

class MensalidadeBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensalidade
        fields = ['usuario', 'aluno', 'valor', 'data_vencimento']
        
        
    