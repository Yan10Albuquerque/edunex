from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from core.models import Aluno
from financeiro.models import Mensalidade


class Command(BaseCommand):
    help = "Cria uma conta demo com alunos e mensalidades ficticias."

    DEMO_USERNAME = "demo"
    DEMO_PASSWORD = "demo12345"

    alunos_demo = [
        {
            "nome": "Ana Beatriz Lima",
            "responsavel": "Mariana Lima",
            "telefone": "+55 11 98888-1001",
            "email": "ana.lima@example.com",
            "valor": Decimal("320.00"),
            "dia_vencimento": 5,
        },
        {
            "nome": "Bruno Martins",
            "responsavel": "Ricardo Martins",
            "telefone": "+55 11 98888-1002",
            "email": "bruno.martins@example.com",
            "valor": Decimal("280.00"),
            "dia_vencimento": 10,
        },
        {
            "nome": "Carla Souza",
            "responsavel": "Patricia Souza",
            "telefone": "+55 21 97777-2003",
            "email": "carla.souza@example.com",
            "valor": Decimal("350.00"),
            "dia_vencimento": 15,
        },
        {
            "nome": "Diego Alves",
            "responsavel": "Fernanda Alves",
            "telefone": "+55 31 96666-3004",
            "email": "diego.alves@example.com",
            "valor": Decimal("300.00"),
            "dia_vencimento": 20,
        },
        {
            "nome": "Elisa Rocha",
            "responsavel": "Camila Rocha",
            "telefone": "+55 41 95555-4005",
            "email": "elisa.rocha@example.com",
            "valor": Decimal("420.00"),
            "dia_vencimento": 25,
        },
        {
            "nome": "Felipe Costa",
            "responsavel": "Joao Costa",
            "telefone": "+55 51 94444-5006",
            "email": "felipe.costa@example.com",
            "valor": Decimal("260.00"),
            "dia_vencimento": 8,
        },
        {
            "nome": "Gabriela Nunes",
            "responsavel": "Luciana Nunes",
            "telefone": "+55 61 93333-6007",
            "email": "gabriela.nunes@example.com",
            "valor": Decimal("390.00"),
            "dia_vencimento": 12,
        },
        {
            "nome": "Henrique Moreira",
            "responsavel": "Paulo Moreira",
            "telefone": "+55 71 92222-7008",
            "email": "henrique.moreira@example.com",
            "valor": Decimal("310.00"),
            "dia_vencimento": 18,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove alunos e mensalidades da conta demo antes de recriar os dados.",
        )

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username=self.DEMO_USERNAME,
            defaults={
                "email": "demo@edunex.local",
                "first_name": "Escola Demo Edunex",
            },
        )

        if created:
            user.set_password(self.DEMO_PASSWORD)
            user.save()
        elif not user.has_usable_password():
            user.set_password(self.DEMO_PASSWORD)
            user.save()

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "escola_nome": "Escola Demo Edunex",
                "telefone": "+55 11 4002-8922",
                "plano": "profissional",
                "ativo": True,
            },
        )

        if options["reset"]:
            Mensalidade.objects.filter(usuario=user).delete()
            Aluno.objects.filter(usuario=user).delete()

        hoje = timezone.localdate()
        mes_atual = hoje.replace(day=1)

        alunos_criados = 0
        mensalidades_criadas = 0

        for index, item in enumerate(self.alunos_demo):
            aluno, aluno_created = Aluno.objects.update_or_create(
                usuario=user,
                nome=item["nome"],
                defaults={
                    "responsavel": item["responsavel"],
                    "telefone": item["telefone"],
                    "email": item["email"],
                },
            )
            alunos_criados += int(aluno_created)
            mensalidades_criadas += self._criar_mensalidades(aluno, item, mes_atual, index)

        self.stdout.write(self.style.SUCCESS("Dados ficticios prontos."))
        self.stdout.write(f"Usuario: {self.DEMO_USERNAME}")
        self.stdout.write(f"Senha: {self.DEMO_PASSWORD}")
        self.stdout.write(f"Alunos novos: {alunos_criados}")
        self.stdout.write(f"Mensalidades novas: {mensalidades_criadas}")

    def _criar_mensalidades(self, aluno, item, mes_atual, index):
        total_criadas = 0
        meses = [-2, -1, 0, 1, 2]

        for offset in meses:
            vencimento = self._data_vencimento(mes_atual + relativedelta(months=offset), item["dia_vencimento"])
            status, data_pagamento = self._status_para_mensalidade(vencimento, index, offset)

            _, created = Mensalidade.objects.get_or_create(
                usuario=aluno.usuario,
                aluno=aluno,
                data_vencimento=vencimento,
                defaults={
                    "valor": item["valor"],
                    "status": status,
                    "data_pagamento": data_pagamento,
                    "recorrente": True,
                    "data_fim_recorrencia": mes_atual + relativedelta(months=10),
                },
            )
            total_criadas += int(created)

        return total_criadas

    def _data_vencimento(self, mes, dia):
        ultimo_dia = (mes + relativedelta(months=1, days=-1)).day
        return mes.replace(day=min(dia, ultimo_dia))

    def _status_para_mensalidade(self, vencimento, index, offset):
        hoje = timezone.localdate()

        if offset < 0:
            if index % 3 == 0 and offset == -1:
                return "atrasado", None
            return "pago", vencimento + relativedelta(days=2)

        if vencimento < hoje:
            if index % 2 == 0:
                return "atrasado", None
            return "pago", vencimento + relativedelta(days=1)

        if index % 4 == 0 and offset == 0:
            return "pago", hoje

        return "pendente", None
