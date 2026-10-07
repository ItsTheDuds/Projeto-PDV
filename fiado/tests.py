from decimal import Decimal
from datetime import datetime

from django.utils import timezone

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


    def test_pagar_tudo_gera_comprovante_somente_do_recebimento(self):
        self.fiados[0].registrar_pagamento(Decimal('2.00'))
        response = self.client.post(
            reverse('fiado:receber_cliente', args=[self.cliente.id]),
            {'valor': '10.00', 'senha': '4321', 'tipo_recebimento': 'quitar_tudo'},
        )
        recebimento = RecebimentoFiado.objects.get()
        url = reverse(
            'fiado:imprimir_recebimento', args=[self.cliente.id, recebimento.id]
        )
        self.assertRedirects(response, url + '?origem=fiado', fetch_redirect_response=False)
        self.assertEqual(recebimento.valor_total, Decimal('10.00'))
        self.assertEqual(
            list(recebimento.aplicacoes.values_list('valor', flat=True)),
            [Decimal('3.00'), Decimal('7.00')],
        )
        recibo = self.client.get(url)
        self.assertContains(recibo, 'COMPROVANTE DE QUITAÇÃO')
        self.assertContains(recibo, 'window.print()')
        self.assertContains(recibo, 'TOTAL QUITADO AGORA:')
        self.assertContains(recibo, '10,00')

    def test_pagar_tudo_invalido_nao_registra_recebimento(self):
        url = reverse('fiado:receber_cliente', args=[self.cliente.id])
        for dados in (
            {'valor': '12.00', 'senha': 'errada'},
            {'valor': '7.00', 'senha': '4321'},
        ):
            resposta = self.client.post(
                url, {**dados, 'tipo_recebimento': 'quitar_tudo'},
            )
            self.assertEqual(resposta.status_code, 302)
            self.assertFalse(RecebimentoFiado.objects.exists())

    def test_pagamento_normal_nao_imprime_automaticamente(self):
        resposta = self.client.post(
            reverse('fiado:receber_cliente', args=[self.cliente.id]),
            {'valor': '12.00', 'senha': '4321'},
        )
        self.assertRedirects(
            resposta, reverse('fiado:cliente_historico', args=[self.cliente.id])
        )


class PainelResumoVendasPermissaoTests(TestCase):
    def setUp(self):
        self.operador = get_user_model().objects.create_user(
            username='operador-painel',
            password='senha-123',
        )
        self.superuser = get_user_model().objects.create_superuser(
            username='admin-painel',
            email='admin-painel@example.com',
            password='senha-123',
        )

    def test_operador_nao_ve_painel_resumo_vendas(self):
        self.client.force_login(self.operador)

        response = self.client.get(reverse('fiado:home'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vendas do período')

    def test_superuser_ve_painel_resumo_vendas(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse('fiado:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vendas do período')



class ImpressaoFiadoClienteTests(TestCase):
    def setUp(self):
        self.operador = get_user_model().objects.create_user(
            username='operador-impressao',
            password='senha-teste-123',
        )
        self.client.force_login(self.operador)
        self.cliente = Cliente.objects.create(
            nome='Cliente Extrato',
            celular='61999999999',
        )
        self.outro_cliente = Cliente.objects.create(
            nome='Outro Cliente',
            celular='61988888888',
        )
        self.produto = produtosModel.objects.create(
            nome='Pao de queijo',
            preco=Decimal('5.00'),
        )

    def criar_fiado(self, cliente, valor, quantidade=1):
        venda = Venda.objects.create(
            cliente=cliente,
            forma_pagamento='FIADO',
            total=valor,
        )
        ItemVenda.objects.create(
            venda=venda,
            produto=self.produto,
            quantidade=quantidade,
            preco_unitario=valor / quantidade,
            subtotal=valor,
        )
        return Fiado.objects.create(venda=venda)

    def test_pendentes_preselecionados_e_quitados_desmarcados(self):
        pago = self.criar_fiado(self.cliente, Decimal('10.00'))
        parcial = self.criar_fiado(self.cliente, Decimal('15.00'))
        aberto = self.criar_fiado(self.cliente, Decimal('5.00'))
        outra = self.criar_fiado(self.outro_cliente, Decimal('50.00'))
        pago.registrar_pagamento(Decimal('10.00'))
        parcial.registrar_pagamento(Decimal('5.00'))

        resposta = self.client.get(
            reverse('fiado:imprimir_cliente', args=[self.cliente.id])
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, 'fiado/imprimir_opcoes.html')
        self.assertEqual(
            resposta.context['selecionados'], {parcial.id, aberto.id}
        )
        self.assertNotContains(resposta, f'value="{outra.id}"')
        self.assertNotContains(resposta, 'EXTRATO DE FIADO')

    def test_somente_compras_selecionadas_sao_impressas_e_somadas(self):
        pago = self.criar_fiado(self.cliente, Decimal('10.00'), quantidade=2)
        parcial = self.criar_fiado(self.cliente, Decimal('15.00'))
        aberto = self.criar_fiado(self.cliente, Decimal('25.00'))
        pago.registrar_pagamento(Decimal('10.00'))
        parcial.registrar_pagamento(Decimal('5.00'))

        resposta = self.client.post(
            reverse('fiado:imprimir_cliente', args=[self.cliente.id]),
            {'fiados': [str(pago.id), str(parcial.id)]},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, 'fiado/imprimir_cliente.html')
        self.assertContains(resposta, 'EXTRATO DE FIADO')
        self.assertContains(resposta, 'Pao de queijo')
        self.assertContains(resposta, 'window.print()')
        self.assertContains(resposta, f'VENDA #{pago.venda_id}')
        self.assertContains(resposta, f'VENDA #{parcial.venda_id}')
        self.assertNotContains(resposta, f'VENDA #{aberto.venda_id}')
        self.assertEqual(resposta.context['total_compras'], Decimal('25.00'))
        self.assertEqual(resposta.context['total_pago'], Decimal('15.00'))
        self.assertEqual(resposta.context['saldo_em_aberto'], Decimal('10.00'))

    def test_pagamento_pendente_pode_ser_impresso_sozinho(self):
        pago = self.criar_fiado(self.cliente, Decimal('20.00'))
        aberto = self.criar_fiado(self.cliente, Decimal('7.00'))
        pago.registrar_pagamento(Decimal('20.00'))

        resposta = self.client.post(
            reverse('fiado:imprimir_cliente', args=[self.cliente.id]),
            {'fiados': [str(aberto.id)]},
        )
        self.assertEqual(resposta.context['total_compras'], Decimal('7.00'))
        self.assertEqual(resposta.context['total_pago'], Decimal('0.00'))
        self.assertEqual(resposta.context['saldo_em_aberto'], Decimal('7.00'))

    def test_primeira_compra_predefinida_para_localizar_por_data(self):
        recente = self.criar_fiado(self.cliente, Decimal('15.00'))
        antiga = self.criar_fiado(self.cliente, Decimal('5.00'))
        outra = self.criar_fiado(self.outro_cliente, Decimal('99.00'))
        for fiado, data in (
            (recente, datetime(2026, 10, 6, 10, 0)),
            (antiga, datetime(2026, 9, 28, 16, 30)),
            (outra, datetime(2026, 1, 1, 8, 0)),
        ):
            Venda.objects.filter(pk=fiado.venda_id).update(
                criada_em=timezone.make_aware(data)
            )

        resposta = self.client.get(
            reverse('fiado:imprimir_cliente', args=[self.cliente.id])
        )
        self.assertEqual(resposta.context['data_inicial'], '28/09/2026')
        self.assertContains(resposta, 'value="28/09/2026"')

    def test_impede_selecao_vazia_duplicada_ou_de_outro_cliente(self):
        fiado = self.criar_fiado(self.cliente, Decimal('10.00'))
        outro = self.criar_fiado(self.outro_cliente, Decimal('99.00'))
        url = reverse('fiado:imprimir_cliente', args=[self.cliente.id])
        for dados in (
            {},
            {'fiados': [str(outro.id)]},
            {'fiados': [str(fiado.id), str(outro.id)]},
            {'fiados': ['abc']},
            {'fiados': [str(fiado.id), str(fiado.id)]},
            {'fiados': ['999999999']},
        ):
            resposta = self.client.post(url, dados)
            self.assertEqual(resposta.status_code, 200)
            self.assertTemplateUsed(resposta, 'fiado/imprimir_opcoes.html')
            self.assertNotContains(resposta, 'window.print()')

    def test_get_nao_imprime_mesmo_com_parametros_antigos(self):
        resposta = self.client.get(
            reverse('fiado:imprimir_cliente', args=[self.cliente.id]),
            {'modo': 'todas', 'auto': '1'},
        )
        self.assertTemplateUsed(resposta, 'fiado/imprimir_opcoes.html')
        self.assertNotContains(resposta, 'window.print()')
