# serializers.py
from rest_framework import serializers
from .models import Aluno

class AlunoBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ['usuario', 'nome', 'responsavel', 'telefone', 'email']
        
    