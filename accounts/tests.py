from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Aluno
from financeiro.models import Mensalidade

from .demo import ALUNOS_DEMO, criar_visitante


class ModoVisitanteTests(TestCase):
    def entrar_como_visitante(self):
        return self.client.post(reverse('visitante_entrar'))

    def test_login_mostra_botao_de_visitante(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, reverse('visitante_entrar'))
        self.assertContains(response, 'Entrar como visitante')

    def test_entrar_como_visitante_cria_conta_com_dados_ficticios(self):
        response = self.entrar_como_visitante()

        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(profile__visitante=True)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.profile.plano, 'profissional')
        self.assertEqual(Aluno.objects.filter(usuario=user).count(), len(ALUNOS_DEMO))
        self.assertEqual(Mensalidade.objects.filter(usuario=user).count(), len(ALUNOS_DEMO) * 5)

    def test_visitante_navega_pelas_telas(self):
        self.entrar_como_visitante()
        user = User.objects.get(profile__visitante=True)
        aluno = Aluno.objects.filter(usuario=user).first()

        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, 'Você está no modo visitante')

        for url in [
            reverse('alunos_list'),
            reverse('aluno_detail', args=[aluno.pk]),
            reverse('aluno_create'),
            reverse('mensalidades_list'),
            reverse('mensalidade_create'),
            reverse('profile'),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_visitante_entrar_exige_post(self):
        self.assertEqual(self.client.get(reverse('visitante_entrar')).status_code, 405)

    def test_visitantes_tem_dados_isolados(self):
        self.entrar_como_visitante()
        primeiro = User.objects.get(profile__visitante=True)
        self.client.logout()

        self.entrar_como_visitante()
        segundo = User.objects.filter(profile__visitante=True).exclude(pk=primeiro.pk).get()

        aluno_do_primeiro = Aluno.objects.filter(usuario=primeiro).first()
        response = self.client.get(reverse('aluno_detail', args=[aluno_do_primeiro.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(primeiro.pk, segundo.pk)

    def test_sair_apaga_conta_do_visitante(self):
        self.entrar_como_visitante()
        user = User.objects.get(profile__visitante=True)

        response = self.client.get(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(Aluno.objects.filter(usuario_id=user.pk).exists())
        self.assertFalse(Mensalidade.objects.filter(usuario_id=user.pk).exists())

    def test_criar_minha_conta_encerra_visitante_e_vai_para_registro(self):
        self.entrar_como_visitante()
        response = self.client.get(reverse('logout') + '?next=register')
        self.assertRedirects(response, reverse('register'))
        self.assertFalse(User.objects.filter(profile__visitante=True).exists())

    def test_visitantes_expirados_sao_removidos(self):
        antigo = criar_visitante()
        User.objects.filter(pk=antigo.pk).update(date_joined=timezone.now() - timedelta(days=2))

        self.entrar_como_visitante()

        self.assertFalse(User.objects.filter(pk=antigo.pk).exists())
        self.assertEqual(User.objects.filter(profile__visitante=True).count(), 1)

    def test_usuario_real_nao_e_afetado(self):
        user = User.objects.create_user('escola', password='senha-forte-123')
        self.client.force_login(user)

        response = self.entrar_como_visitante()

        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(User.objects.filter(profile__visitante=True).exists())

        self.client.get(reverse('logout'))
        self.assertTrue(User.objects.filter(pk=user.pk).exists())


class PaginaVendasRemovidaTests(TestCase):
    def test_pagina_de_vendas_nao_existe(self):
        self.assertEqual(self.client.get('/vendas/').status_code, 404)


class ComandoDadosFicticiosTests(TestCase):
    def test_comando_cria_conta_demo_idempotente(self):
        from io import StringIO
        from django.core.management import call_command

        call_command('popular_dados_ficticios', stdout=StringIO())
        call_command('popular_dados_ficticios', stdout=StringIO())

        demo = User.objects.get(username='demo')
        self.assertTrue(demo.check_password('demo12345'))
        self.assertFalse(demo.profile.visitante)
        self.assertEqual(Aluno.objects.filter(usuario=demo).count(), len(ALUNOS_DEMO))
        self.assertEqual(Mensalidade.objects.filter(usuario=demo).count(), len(ALUNOS_DEMO) * 5)


class RegistroLoginPerfilTests(TestCase):
    def dados_registro(self, **extra):
        return {
            'escola_nome': 'Colegio Aurora',
            'username': 'aurora',
            'email': 'contato@aurora.example.com',
            'telefone': '',
            'password': 'Senha-Muito-Forte-2026',
            'password_confirm': 'Senha-Muito-Forte-2026',
            **extra,
        }

    def test_registro_cria_usuario_e_perfil(self):
        response = self.client.post(reverse('register'), self.dados_registro())
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='aurora')
        self.assertEqual(user.profile.escola_nome, 'Colegio Aurora')
        self.assertFalse(user.profile.visitante)

    def test_registro_rejeita_senha_fraca_e_mantem_dados(self):
        response = self.client.post(
            reverse('register'),
            self.dados_registro(password='123', password_confirm='123'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="aurora"')
        self.assertFalse(User.objects.filter(username='aurora').exists())

    def test_registro_rejeita_campos_vazios(self):
        response = self.client.post(reverse('register'), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_registro_rejeita_email_duplicado(self):
        User.objects.create_user('outro', email='contato@aurora.example.com', password='x')
        response = self.client.post(
            reverse('register'),
            self.dados_registro(email='CONTATO@aurora.example.com'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='aurora').exists())

    def test_login_respeita_next_seguro(self):
        User.objects.create_user('escola', password='senha-forte-123')
        destino = reverse('alunos_list')
        response = self.client.post(
            reverse('login') + '?next=' + destino,
            {'username': 'escola', 'password': 'senha-forte-123', 'next': destino},
        )
        self.assertRedirects(response, destino, fetch_redirect_response=False)

    def test_login_ignora_next_externo(self):
        User.objects.create_user('escola', password='senha-forte-123')
        response = self.client.post(
            reverse('login'),
            {'username': 'escola', 'password': 'senha-forte-123', 'next': 'https://site-malicioso.example.com/'},
        )
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)

    def test_perfil_rejeita_email_de_outra_conta(self):
        User.objects.create_user('outro', email='ocupado@example.com', password='x')
        user = User.objects.create_user('escola', email='escola@example.com', password='x')
        self.client.force_login(user)
        response = self.client.post(reverse('profile'), {
            'escola_nome': 'Escola', 'email': 'ocupado@example.com', 'telefone': '',
        })
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, 'escola@example.com')

    def test_perfil_atualiza_nome_da_escola_no_topo(self):
        user = User.objects.create_user('escola', email='escola@example.com', password='x')
        self.client.force_login(user)
        self.client.post(reverse('profile'), {
            'escola_nome': 'Novo Nome', 'email': 'escola@example.com', 'telefone': '',
        })
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Novo Nome')
        self.assertEqual(user.profile.escola_nome, 'Novo Nome')
