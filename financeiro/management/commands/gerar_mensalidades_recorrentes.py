"""
Comando para gerar mensalidades recorrentes automaticamente.
Execute com: python manage.py gerar_mensalidades_recorrentes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from financeiro.models import Mensalidade
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Gera mensalidades recorrentes para alunos com mensalidades em aberto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Gera mensalidades com vencimento nos próximos N dias (padrão: 7)',
        )

    def handle(self, *args, **options):
        dias = options['dias']
        hoje = timezone.now().date()
        data_limite = hoje + relativedelta(days=dias)

        # Buscar mensalidades pagas que ainda não têm próxima mensalidade
        mensalidades_pagas = Mensalidade.objects.filter(
            status='pago',
            recorrente=True,
        ).exclude(
            proxima_mensalidade__isnull=False
        )

        criadas = 0
        for mensalidade in mensalidades_pagas:
            # Verifica se atingiu data de fim de recorrência
            if mensalidade.data_fim_recorrencia and mensalidade.data_vencimento >= mensalidade.data_fim_recorrencia:
                continue

            # Cria próxima mensalidade
            nova = mensalidade.criar_proxima_mensalidade()
            if nova:
                criadas += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Mensalidade criada: {nova.aluno.nome} - {nova.data_vencimento.strftime("%d/%m/%Y")}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{criadas} mensalidade(s) recorrente(s) criada(s) com sucesso!')
        )
