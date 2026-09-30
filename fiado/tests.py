from decimal import Decimal

from django.test import TestCase

from clientes.models import Cliente
from produtos.models import produtosModel
from vendas.models import ItemVenda, Venda

from .models import ConfiguracaoFiado, Fiado


class FiadoTests(TestCase):
    def setUp(self):
        cliente = Cliente.objects.create(nome='Ana', celular='61999999999')
        produto = produtosModel.objects.create(nome='Item', descricao='x', preco=Decimal('5.00'), quantidade=1)
        venda = Venda.objects.create(cliente=cliente, forma_pagamento='FIADO', total=Decimal('5.00'))
        ItemVenda.objects.create(venda=venda, produto=produto, quantidade=1, preco_unitario=Decimal('5.00'), subtotal=Decimal('5.00'))
        self.fiado = Fiado.objects.create(venda=venda)

    def test_senha_e_armazenada_com_hash(self):
        configuracao = ConfiguracaoFiado.carregar()
        configuracao.definir_senha('4321')

        self.assertNotEqual(configuracao.senha_hash, '4321')
        self.assertTrue(configuracao.conferir_senha('4321'))
        self.assertFalse(configuracao.conferir_senha('9999'))

    def test_marcar_como_pago(self):
        self.fiado.marcar_como_pago()
        self.fiado.refresh_from_db()

        self.assertTrue(self.fiado.pago)
        self.assertIsNotNone(self.fiado.pago_em)
