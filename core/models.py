from django.db import models
from django.contrib.auth.models import User


class Aluno(models.Model):
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alunos')
    nome = models.CharField(max_length=255, verbose_name='Nome do Aluno')
    responsavel = models.CharField(max_length=255, verbose_name='Nome do Responsável')
    telefone = models.CharField(max_length=20, verbose_name='Telefone (WhatsApp)')
    email = models.EmailField(blank=True, verbose_name='Email')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def get_whatsapp_link(self):
        telefone_limpo = ''.join(filter(str.isdigit, self.telefone))
        return f"https://wa.me/{telefone_limpo}"
