from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from produtos.models import produtosModel
from vendas.models import ItemVenda, Venda

from .models import ConfiguracaoFiado, Fiado


class FiadoTests(TestCase):
    def setUp(self):
        cliente = Cliente.objects.create(nome='Ana', celular='61999999999')
        produto = produtosModel.objects.create(nome='Item', descricao='x', preco=Decimal('5.00'))
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



class PermissaoSenhaFiadoTests(TestCase):
    def setUp(self):
        self.usuario_comum = get_user_model().objects.create_user(
            username='ronaldo',
            password='senha-login-123',
        )
        self.superadmin = get_user_model().objects.create_superuser(
            username='superadmin',
            email='admin@example.com',
            password='senha-admin-123',
        )

    def test_usuario_comum_pode_cadastrar_primeira_senha(self):
        self.client.force_login(self.usuario_comum)

        response = self.client.post(
            reverse('fiado:configurar_senha'),
            {
                'nova_senha': '4321',
                'confirmar_senha': '4321',
            },
        )

        self.assertRedirects(response, reverse('fiado:home'))
        configuracao = ConfiguracaoFiado.carregar()
        self.assertTrue(configuracao.conferir_senha('4321'))

    def test_usuario_comum_nao_pode_alterar_senha_ja_configurada(self):
        configuracao = ConfiguracaoFiado.carregar()
        configuracao.definir_senha('4321')
        self.client.force_login(self.usuario_comum)

        response = self.client.post(
            reverse('fiado:configurar_senha'),
            {
                'nova_senha': '9999',
                'confirmar_senha': '9999',
            },
        )

        self.assertRedirects(response, reverse('fiado:home'))
        configuracao.refresh_from_db()
        self.assertTrue(configuracao.conferir_senha('4321'))
        self.assertFalse(configuracao.conferir_senha('9999'))

    def test_superadmin_pode_resetar_senha_sem_saber_a_anterior(self):
        configuracao = ConfiguracaoFiado.carregar()
        configuracao.definir_senha('4321')
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse('fiado:configurar_senha'),
            {
                'nova_senha': '9876',
                'confirmar_senha': '9876',
            },
        )

        self.assertRedirects(response, reverse('fiado:home'))
        configuracao.refresh_from_db()
        self.assertFalse(configuracao.conferir_senha('4321'))
        self.assertTrue(configuracao.conferir_senha('9876'))

    def test_usuario_comum_nao_acessa_tela_de_alteracao(self):
        configuracao = ConfiguracaoFiado.carregar()
        configuracao.definir_senha('4321')
        self.client.force_login(self.usuario_comum)

        response = self.client.get(reverse('fiado:configurar_senha'))

        self.assertRedirects(response, reverse('fiado:home'))
