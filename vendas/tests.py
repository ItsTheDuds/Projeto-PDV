import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from fiado.models import Fiado
from produtos.models import produtosModel

from .models import Venda


class VendaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='operador',
            password='senha-segura-123',
        )
        self.client.force_login(self.usuario)

        self.cliente = Cliente.objects.create(nome='João', celular='61999999999')
        self.produto = produtosModel.objects.create(
            nome='Produto',
            descricao='Teste',
            preco=Decimal('10.00'),
        )

    def test_venda_fiada_cria_fiado(self):
        response = self.client.post(
            reverse('vendas:finalizar'),
            data=json.dumps({
                'cliente_id': self.cliente.id,
                'forma_pagamento': 'FIADO',
                'itens': [{
                    'produto_id': self.produto.id,
                    'quantidade': 2,
                    'preco_unitario': '8.50',
                }],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        venda = Venda.objects.get()
        self.assertEqual(venda.total, Decimal('17.00'))
        self.assertTrue(Fiado.objects.filter(venda=venda, pago=False).exists())


    def test_forma_de_pagamento_nao_fiado_e_rejeitada(self):
        response = self.client.post(
            reverse('vendas:finalizar'),
            data=json.dumps({
                'cliente_id': self.cliente.id,
                'forma_pagamento': 'PIX',
                'itens': [{
                    'produto_id': self.produto.id,
                    'quantidade': 1,
                    'preco_unitario': '10.00',
                }],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Forma de pagamento inválida', response.json()['erro'])


    def test_preco_zero_e_rejeitado(self):
        response = self.client.post(
            reverse('vendas:finalizar'),
            data=json.dumps({
                'cliente_id': self.cliente.id,
                'forma_pagamento': 'FIADO',
                'itens': [{
                    'produto_id': self.produto.id,
                    'quantidade': 2,
                    'preco_unitario': '0.00',
                }],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('maior que R$ 0,00', response.json()['erro'])
        self.assertFalse(Venda.objects.exists())

    def test_venda_com_varios_itens_zero_e_rejeitada(self):
        outro_produto = produtosModel.objects.create(
            nome='Outro produto',
            descricao='',
            preco=Decimal('5.00'),
        )

        response = self.client.post(
            reverse('vendas:finalizar'),
            data=json.dumps({
                'cliente_id': self.cliente.id,
                'forma_pagamento': 'FIADO',
                'itens': [
                    {
                        'produto_id': self.produto.id,
                        'quantidade': 1,
                        'preco_unitario': '0.00',
                    },
                    {
                        'produto_id': outro_produto.id,
                        'quantidade': 1,
                        'preco_unitario': '0.00',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Venda.objects.exists())
        self.assertFalse(Fiado.objects.exists())


class ResumoVendasPermissaoTests(TestCase):
    def setUp(self):
        self.operador = get_user_model().objects.create_user(
            username='operador-resumo',
            password='senha-123',
        )
        self.superuser = get_user_model().objects.create_superuser(
            username='admin-resumo',
            email='admin-resumo@example.com',
            password='senha-123',
        )

    def test_operador_nao_pode_acessar_resumo_de_vendas(self):
        self.client.force_login(self.operador)

        response = self.client.get(
            reverse('vendas:resumo_periodo'),
            {'tipo': 'mes', 'mes': '2026-10'},
        )

        self.assertEqual(response.status_code, 403)

    def test_valores_vendido_em_aberto_e_total_com_pagamento_parcial(self):
        self.client.force_login(self.superuser)
        cliente = Cliente.objects.create(nome='Resumo Teste', celular='61988888888')

        venda_paga = Venda.objects.create(
            cliente=cliente, forma_pagamento='FIADO', total=Decimal('50.00'),
        )
        fiado_pago = Fiado.objects.create(venda=venda_paga)
        fiado_pago.registrar_pagamento(Decimal('50.00'))

        venda_parcial = Venda.objects.create(
            cliente=cliente, forma_pagamento='FIADO', total=Decimal('100.00'),
        )
        fiado_parcial = Fiado.objects.create(venda=venda_parcial)
        fiado_parcial.registrar_pagamento(Decimal('25.00'))

        venda_aberta = Venda.objects.create(
            cliente=cliente, forma_pagamento='FIADO', total=Decimal('30.00'),
        )
        Fiado.objects.create(venda=venda_aberta)

        response = self.client.get(reverse('vendas:resumo_periodo'))
        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(Decimal(dados['vendido']), Decimal('75.00'))
        self.assertEqual(Decimal(dados['em_aberto']), Decimal('105.00'))
        self.assertEqual(Decimal(dados['total']), Decimal('180.00'))
        self.assertEqual(
            Decimal(dados['vendido']) + Decimal(dados['em_aberto']),
            Decimal(dados['total']),
        )

    def test_superuser_pode_acessar_resumo_de_vendas(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('vendas:resumo_periodo'),
            {'tipo': 'mes', 'mes': '2026-10'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('total', response.json())
