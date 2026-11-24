"""
Dados ficticios usados pela conta demo e pelo modo visitante.
"""
import uuid
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from core.models import Aluno
from financeiro.models import Mensalidade

from .models import UserProfile


VISITANTE_PREFIXO = 'visitante_'
VISITANTE_ESCOLA_NOME = 'Escola Exemplo (visitante)'
VISITANTE_VALIDADE = timedelta(hours=24)

ALUNOS_DEMO = [
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


def popular_dados_ficticios(user):
    """
    Cria (ou completa) alunos e mensalidades ficticias para o usuario.
    Retorna a tupla (alunos_criados, mensalidades_criadas).
    """
    mes_atual = timezone.localdate().replace(day=1)
    alunos_criados = 0
    mensalidades_criadas = 0

    for index, item in enumerate(ALUNOS_DEMO):
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
        mensalidades_criadas += _criar_mensalidades(aluno, item, mes_atual, index)

    return alunos_criados, mensalidades_criadas


def _criar_mensalidades(aluno, item, mes_atual, index):
    total_criadas = 0

    for offset in (-2, -1, 0, 1, 2):
        vencimento = _data_vencimento(mes_atual + relativedelta(months=offset), item["dia_vencimento"])
        status, data_pagamento = _status_para_mensalidade(vencimento, index, offset)

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


def _data_vencimento(mes, dia):
    ultimo_dia = (mes + relativedelta(months=1, days=-1)).day
    return mes.replace(day=min(dia, ultimo_dia))


def _status_para_mensalidade(vencimento, index, offset):
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


def is_visitante(user):
    if not user.is_authenticated:
        return False
    try:
        return user.profile.visitante
    except UserProfile.DoesNotExist:
        return False


def limpar_visitantes_expirados():
    """
    Remove contas de visitante criadas ha mais tempo que VISITANTE_VALIDADE.
    Alunos e mensalidades sao removidos em cascata.
    """
    limite = timezone.now() - VISITANTE_VALIDADE
    removidos, _ = User.objects.filter(
        profile__visitante=True,
        date_joined__lt=limite,
    ).delete()
    return removidos


@transaction.atomic
def criar_visitante():
    """
    Cria uma conta temporaria e isolada para um visitante, ja com dados ficticios.
    Cada visitante recebe a sua propria copia dos dados, entao pode cadastrar,
    editar e excluir livremente sem afetar outras pessoas.
    """
    user = User(
        username=f"{VISITANTE_PREFIXO}{uuid.uuid4().hex[:10]}",
        first_name=VISITANTE_ESCOLA_NOME,
    )
    user.set_unusable_password()
    user.save()

    UserProfile.objects.create(
        user=user,
        escola_nome=VISITANTE_ESCOLA_NOME,
        telefone="+55 11 4002-8922",
        plano="profissional",
        ativo=True,
        visitante=True,
    )

    popular_dados_ficticios(user)
    return user
