from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Aluno


class Mensalidade(models.Model):
    """
    Modelo de mensalidade vinculada a um aluno
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensalidades')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='mensalidades')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data de Pagamento')
    
    # Campos para controle de recorrência
    recorrente = models.BooleanField(default=True, verbose_name='Recorrente')
    mensalidade_anterior = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='proxima_mensalidade',
        verbose_name='Mensalidade Anterior'
    )
    data_fim_recorrencia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Fim da Recorrência'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Mensalidade'
        verbose_name_plural = 'Mensalidades'
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.aluno.nome} - {self.data_vencimento.strftime('%m/%Y')}"
    
    def atualizar_status(self):
        """
        Atualiza o status baseado na data de vencimento
        """
        if self.status == 'pago':
            return
        
        if timezone.now().date() > self.data_vencimento:
            self.status = 'atrasado'
        else:
            self.status = 'pendente'
        
        self.save()
    
    def marcar_como_pago(self):
        """
        Marca a mensalidade como paga e cria a próxima se recorrente
        """
        self.status = 'pago'
        self.data_pagamento = timezone.now().date()
        self.save()
        
        # Cria próxima mensalidade se recorrente
        if self.recorrente:
            self.criar_proxima_mensalidade()
    
    def get_dias_atraso(self):
        """
        Retorna numero de dias em atraso
        """
        if self.status != 'atrasado':
            return 0
        return (timezone.now().date() - self.data_vencimento).days
    
    def get_whatsapp_message(self):
        """
        Retorna mensagem formatada para WhatsApp
        """
        return f"Ola, tudo bem? A mensalidade do aluno {self.aluno.nome} esta em aberto. Poderia verificar, por favor?"
    
    def criar_proxima_mensalidade(self):
        """
        Cria a próxima mensalidade recorrente quando a atual for paga.
        Mantém o mesmo dia do mês e permite valor variável.
        """
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        # Verifica se deve criar próxima mensalidade
        if not self.recorrente or self.status != 'pago':
            return None
        
        # Verifica se já existe próxima mensalidade
        if self.proxima_mensalidade.exists():
            return None
        
        # Verifica se atingiu data de fim de recorrência
        if self.data_fim_recorrencia and self.data_vencimento >= self.data_fim_recorrencia:
            return None
        
        # Calcula data de vencimento da próxima mensalidade
        # Mantém o mesmo dia do mês
        try:
            proxima_data = self.data_vencimento + relativedelta(months=1)
        except ValueError:
            # Se o dia não existe no próximo mês (ex: 31 de janeiro -> fevereiro)
            # usa o último dia do mês
            proxima_data = self.data_vencimento + relativedelta(months=1)
            # Tenta ajustar para o último dia do mês se necessário
            try:
                proxima_data = proxima_data.replace(day=self.data_vencimento.day)
            except ValueError:
                from calendar import monthrange
                ultimo_dia = monthrange(proxima_data.year, proxima_data.month)[1]
                proxima_data = proxima_data.replace(day=ultimo_dia)
        
        # Cria nova mensalidade
        nova_mensalidade = Mensalidade.objects.create(
            usuario=self.usuario,
            aluno=self.aluno,
            valor=self.valor,  # Mesmo valor por padrão
            data_vencimento=proxima_data,
            status='pendente',
            recorrente=self.recorrente,
            mensalidade_anterior=self,
            data_fim_recorrencia=self.data_fim_recorrencia,
        )
        
        return nova_mensalidade
