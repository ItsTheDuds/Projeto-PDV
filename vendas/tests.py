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
            quantidade=10,
        )

    def test_venda_fiada_cria_fiado_e_baixa_estoque(self):
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

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 8)


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
