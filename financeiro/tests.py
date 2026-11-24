from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Aluno
from core.tests import criar_escola

from .models import Mensalidade


class MensalidadeViewsTests(TestCase):
    def setUp(self):
        self.user = criar_escola()
        self.client.force_login(self.user)
        self.aluno = Aluno.objects.create(
            usuario=self.user, nome='Joana', responsavel='Maria', telefone='11988887777',
        )
        self.hoje = timezone.localdate()

    def criar_mensalidade(self, **extra):
        extra.setdefault('valor', Decimal('300.00'))
        extra.setdefault('data_vencimento', self.hoje + timedelta(days=5))
        return Mensalidade.objects.create(usuario=self.user, aluno=self.aluno, **extra)

    def test_cria_mensalidade(self):
        response = self.client.post(reverse('mensalidade_create'), {
            'aluno': self.aluno.pk,
            'valor': '250.00',
            'data_vencimento': (self.hoje + timedelta(days=3)).isoformat(),
            'recorrente': 'on',
        })
        self.assertRedirects(response, reverse('mensalidades_list'))
        mensalidade = Mensalidade.objects.get()
        self.assertEqual(mensalidade.status, 'pendente')
        self.assertTrue(mensalidade.recorrente)

    def test_mensalidade_com_vencimento_passado_ja_nasce_atrasada(self):
        self.client.post(reverse('mensalidade_create'), {
            'aluno': self.aluno.pk,
            'valor': '250.00',
            'data_vencimento': (self.hoje - timedelta(days=3)).isoformat(),
        })
        self.assertEqual(Mensalidade.objects.get().status, 'atrasado')

    def test_valor_invalido_nao_gera_erro_500(self):
        for valor in ['', 'abc', '-10', '0']:
            with self.subTest(valor=valor):
                response = self.client.post(reverse('mensalidade_create'), {
                    'aluno': self.aluno.pk,
                    'valor': valor,
                    'data_vencimento': self.hoje.isoformat(),
                })
                self.assertEqual(response.status_code, 200)
        self.assertFalse(Mensalidade.objects.exists())

    def test_fim_da_recorrencia_antes_do_vencimento(self):
        response = self.client.post(reverse('mensalidade_create'), {
            'aluno': self.aluno.pk,
            'valor': '100',
            'data_vencimento': self.hoje.isoformat(),
            'data_fim_recorrencia': (self.hoje - timedelta(days=30)).isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Mensalidade.objects.exists())

    def test_nao_cria_mensalidade_para_aluno_de_outra_escola(self):
        outra = criar_escola('outra')
        aluno_alheio = Aluno.objects.create(usuario=outra, nome='X', responsavel='Y', telefone='11999999999')
        response = self.client.post(reverse('mensalidade_create'), {
            'aluno': aluno_alheio.pk,
            'valor': '100',
            'data_vencimento': self.hoje.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Mensalidade.objects.exists())

    def test_link_da_ficha_do_aluno_pre_seleciona_o_aluno(self):
        response = self.client.get(reverse('mensalidade_create') + f'?aluno_id={self.aluno.pk}')
        self.assertContains(response, f'value="{self.aluno.pk}" selected')

    def test_editar_para_pago_registra_pagamento_e_gera_proxima(self):
        mensalidade = self.criar_mensalidade()
        response = self.client.post(reverse('mensalidade_update', args=[mensalidade.pk]), {
            'valor': '300.00',
            'data_vencimento': mensalidade.data_vencimento.isoformat(),
            'status': 'pago',
            'recorrente': 'on',
        })
        self.assertRedirects(response, reverse('mensalidades_list'))
        mensalidade.refresh_from_db()
        self.assertEqual(mensalidade.status, 'pago')
        self.assertEqual(mensalidade.data_pagamento, self.hoje)
        self.assertTrue(mensalidade.proxima_mensalidade.exists())

    def test_editar_de_pago_para_pendente_limpa_data_pagamento(self):
        mensalidade = self.criar_mensalidade(status='pago', data_pagamento=self.hoje, recorrente=False)
        self.client.post(reverse('mensalidade_update', args=[mensalidade.pk]), {
            'valor': '300.00',
            'data_vencimento': mensalidade.data_vencimento.isoformat(),
            'status': 'pendente',
        })
        mensalidade.refresh_from_db()
        self.assertEqual(mensalidade.status, 'pendente')
        self.assertIsNone(mensalidade.data_pagamento)

    def test_status_invalido_e_rejeitado(self):
        mensalidade = self.criar_mensalidade()
        response = self.client.post(reverse('mensalidade_update', args=[mensalidade.pk]), {
            'valor': '300.00',
            'data_vencimento': mensalidade.data_vencimento.isoformat(),
            'status': 'qualquer-coisa',
        })
        self.assertEqual(response.status_code, 200)
        mensalidade.refresh_from_db()
        self.assertEqual(mensalidade.status, 'pendente')

    def test_dashboard_soma_os_totais_do_mes(self):
        self.criar_mensalidade(data_vencimento=self.hoje, status='pago')
        self.criar_mensalidade(data_vencimento=self.hoje.replace(day=1), valor=Decimal('50'))
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total_pago'], Decimal('300.00'))
        self.assertEqual(
            response.context['total_pendente'] + response.context['total_pago'],
            Decimal('350.00'),
        )


class ImportacaoMensalidadesApiTests(TestCase):
    url = '/financeiro/internal/import-mensalidades/'

    def setUp(self):
        self.escola = criar_escola()
        self.outra = criar_escola('outra')
        self.aluno_da_outra = Aluno.objects.create(
            usuario=self.outra, nome='X', responsavel='Y', telefone='11999999999',
        )
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)

    def payload(self, usuario, aluno):
        return [{
            'usuario': usuario.pk,
            'aluno': aluno.pk,
            'valor': '100.00',
            'data_vencimento': timezone.localdate().isoformat(),
        }]

    def test_anonimo_nao_importa(self):
        response = self.client.post(
            self.url, self.payload(self.outra, self.aluno_da_outra), content_type='application/json',
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(Mensalidade.objects.exists())

    def test_aluno_precisa_pertencer_ao_usuario(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            self.url, self.payload(self.escola, self.aluno_da_outra), content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Mensalidade.objects.exists())

    def test_staff_importa(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            self.url, self.payload(self.outra, self.aluno_da_outra), content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Mensalidade.objects.count(), 1)
