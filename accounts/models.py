from datetime import timedelta, timezone

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Perfil estendido do usuário com informações do plano SaaS
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    escola_nome = models.CharField(max_length=255, verbose_name='Nome da Escola')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    
    # Informações SaaS
    plano = models.CharField(
        max_length=20,
        choices=[
            ('gratuito', 'Gratuito'),
            ('basico', 'Básico'),
            ('profissional', 'Profissional'),
        ],
        default='gratuito',
        verbose_name='Plano'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis dos Usuários'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.escola_nome}"
