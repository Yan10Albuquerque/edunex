from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.demo import popular_dados_ficticios
from accounts.models import UserProfile
from core.models import Aluno
from financeiro.models import Mensalidade


class Command(BaseCommand):
    help = "Cria uma conta demo com alunos e mensalidades ficticias."

    DEMO_USERNAME = "demo"
    DEMO_PASSWORD = "demo12345"

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

        if created or not user.has_usable_password():
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

        alunos_criados, mensalidades_criadas = popular_dados_ficticios(user)

        self.stdout.write(self.style.SUCCESS("Dados ficticios prontos."))
        self.stdout.write(f"Usuario: {self.DEMO_USERNAME}")
        self.stdout.write(f"Senha: {self.DEMO_PASSWORD}")
        self.stdout.write(f"Alunos novos: {alunos_criados}")
        self.stdout.write(f"Mensalidades novas: {mensalidades_criadas}")
