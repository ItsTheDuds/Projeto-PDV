from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from produtos.models import produtosModel
from vendas.models import ItemVenda, Venda

from .models import ConfiguracaoFiado, Fiado, RecebimentoFiado


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
        self.assertEqual(self.fiado.valor_pago, Decimal('5.00'))
        self.assertEqual(self.fiado.saldo_devedor, Decimal('0.00'))
        self.assertIsNotNone(self.fiado.pago_em)

    def test_pagamento_parcial_mantem_fiado_em_aberto(self):
        self.fiado.registrar_pagamento(Decimal('2.00'))
        self.fiado.refresh_from_db()

        self.assertFalse(self.fiado.pago)
        self.assertEqual(self.fiado.valor_pago, Decimal('2.00'))
        self.assertEqual(self.fiado.saldo_devedor, Decimal('3.00'))

    def test_pagamentos_parciais_podem_quitar_o_fiado(self):
        self.fiado.registrar_pagamento(Decimal('2.00'))
        self.fiado.registrar_pagamento(Decimal('3.00'))
        self.fiado.refresh_from_db()

        self.assertTrue(self.fiado.pago)
        self.assertEqual(self.fiado.valor_pago, Decimal('5.00'))
        self.assertEqual(self.fiado.saldo_devedor, Decimal('0.00'))



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


class RecebimentoClienteTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='operador',
            password='senha-login-123',
        )
        self.client.force_login(self.usuario)

        self.cliente = Cliente.objects.create(
            nome='Cliente Teste',
            celular='61988888888',
        )
        self.produto = produtosModel.objects.create(
            nome='Item',
            descricao='',
            preco=Decimal('1.00'),
        )

        self.fiados = []
        for total in (Decimal('5.00'), Decimal('7.00')):
            venda = Venda.objects.create(
                cliente=self.cliente,
                forma_pagamento='FIADO',
                total=total,
            )
            ItemVenda.objects.create(
                venda=venda,
                produto=self.produto,
                quantidade=1,
                preco_unitario=total,
                subtotal=total,
            )
            self.fiados.append(Fiado.objects.create(venda=venda))

        ConfiguracaoFiado.carregar().definir_senha('4321')

    def test_recebimento_parcial_quita_mais_antiga_e_abate_proxima(self):
        response = self.client.post(
            reverse('fiado:receber_cliente', args=[self.cliente.id]),
            {
                'valor': '8.00',
                'senha': '4321',
            },
        )

        self.assertRedirects(
            response,
            reverse('fiado:cliente_historico', args=[self.cliente.id]),
        )

        primeiro, segundo = self.fiados
        primeiro.refresh_from_db()
        segundo.refresh_from_db()

        self.assertTrue(primeiro.pago)
        self.assertEqual(primeiro.valor_pago, Decimal('5.00'))
        self.assertFalse(segundo.pago)
        self.assertEqual(segundo.valor_pago, Decimal('3.00'))
        self.assertEqual(segundo.saldo_devedor, Decimal('4.00'))

        recebimento = RecebimentoFiado.objects.get()
        self.assertEqual(recebimento.valor_total, Decimal('8.00'))
        self.assertEqual(recebimento.aplicacoes.count(), 2)

    def test_quitacao_total_fecha_todas_as_compras(self):
        response = self.client.post(
            reverse('fiado:receber_cliente', args=[self.cliente.id]),
            {
                'valor': '12.00',
                'senha': '4321',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Fiado.objects.filter(venda__cliente=self.cliente, pago=False).exists()
        )

    def test_recebimento_rejeita_valor_maior_que_saldo(self):
        response = self.client.post(
            reverse('fiado:receber_cliente', args=[self.cliente.id]),
            {
                'valor': '12.01',
                'senha': '4321',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(RecebimentoFiado.objects.exists())
        self.assertEqual(
            sum(
                fiado.valor_pago
                for fiado in Fiado.objects.filter(venda__cliente=self.cliente)
            ),
            Decimal('0.00'),
        )
