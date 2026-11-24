from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .models import Aluno


def criar_escola(username='escola', plano='profissional', **extra):
    user = User.objects.create_user(username, password='senha-forte-123', **extra)
    UserProfile.objects.create(user=user, escola_nome='Escola Teste', plano=plano)
    return user


class AlunoViewsTests(TestCase):
    def setUp(self):
        self.user = criar_escola()
        self.client.force_login(self.user)

    def dados(self, **extra):
        return {
            'nome': 'Joana Silva',
            'responsavel': 'Maria Silva',
            'telefone': '(11) 98888-7777',
            'email': '',
            **extra,
        }

    def test_cria_aluno(self):
        response = self.client.post(reverse('aluno_create'), self.dados())
        self.assertRedirects(response, reverse('alunos_list'))
        self.assertTrue(Aluno.objects.filter(usuario=self.user, nome='Joana Silva').exists())

    def test_dados_invalidos_nao_geram_erro_500(self):
        response = self.client.post(reverse('aluno_create'), {'nome': 'Joana'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Joana"')
        self.assertFalse(Aluno.objects.exists())

    def test_telefone_invalido(self):
        response = self.client.post(reverse('aluno_create'), self.dados(telefone='123'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'telefone valido')
        self.assertFalse(Aluno.objects.exists())

    def test_formulario_nao_tem_campo_nascimento(self):
        response = self.client.get(reverse('aluno_create'))
        self.assertNotContains(response, 'nascimento')

    def test_nao_edita_aluno_de_outra_escola(self):
        outra = criar_escola('outra')
        aluno = Aluno.objects.create(usuario=outra, nome='X', responsavel='Y', telefone='11999999999')
        response = self.client.post(reverse('aluno_update', args=[aluno.pk]), self.dados())
        self.assertEqual(response.status_code, 404)


class ImportacaoAlunosApiTests(TestCase):
    url = '/alunos/internal/import-alunos/'

    def setUp(self):
        self.escola = criar_escola()
        self.payload = [{
            'usuario': self.escola.pk,
            'nome': 'Aluno Importado',
            'responsavel': 'Resp',
            'telefone': '11999999999',
            'email': '',
        }]

    def test_anonimo_nao_importa(self):
        response = self.client.post(self.url, self.payload, content_type='application/json')
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(Aluno.objects.exists())

    def test_usuario_comum_nao_importa(self):
        self.client.force_login(self.escola)
        response = self.client.post(self.url, self.payload, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Aluno.objects.exists())

    def test_staff_importa(self):
        staff = User.objects.create_user('staff', password='x', is_staff=True)
        self.client.force_login(staff)
        response = self.client.post(self.url, self.payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Aluno.objects.filter(usuario=self.escola).count(), 1)
