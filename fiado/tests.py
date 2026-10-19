from decimal import Decimal
from datetime import datetime

from django.utils import timezone

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
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



class EdicaoItensFiadoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='operador-edicao')
        self.client.force_login(self.usuario)
        self.cliente = Cliente.objects.create(nome='Cliente edição', celular='61977777777')
        self.produto = produtosModel.objects.create(nome='Café', preco=Decimal('9.00'))
        self.outro_produto = produtosModel.objects.create(nome='Salgado', preco=Decimal('8.00'))
        self.venda = Venda.objects.create(
            cliente=self.cliente, forma_pagamento='FIADO', total=Decimal('18.00'),
        )
        self.item = ItemVenda.objects.create(
            venda=self.venda, produto=self.produto, quantidade=2,
            preco_unitario=Decimal('9.00'), subtotal=Decimal('18.00'),
        )
        self.fiado = Fiado.objects.create(venda=self.venda)
        ConfiguracaoFiado.carregar().definir_senha('4321')
        self.url = reverse('fiado:editar_itens', args=[self.fiado.id])

    def dados_edicao(self, **alteracoes):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        dados = {
            'revisao': resposta.context['autorizacao'].initial['revisao'],
            'senha': '4321',
            'itens-TOTAL_FORMS': '1', 'itens-INITIAL_FORMS': '1',
            'itens-0-id': str(self.item.id),
            'itens-0-produto': str(self.produto.id),
            'itens-0-quantidade': '3', 'itens-0-preco_unitario': '9.00',
        }
        dados.update(alteracoes)
        return dados

    def assert_compra_original(self):
        self.venda.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.venda.total, Decimal('18.00'))
        self.assertEqual(self.item.quantidade, 2)
        self.assertEqual(self.item.preco_unitario, Decimal('9.00'))
        self.assertEqual(self.item.subtotal, Decimal('18.00'))
        self.assertEqual(self.venda.itens.count(), 1)

    def test_detalhe_oferece_edicao_e_get_nao_altera_compra(self):
        resposta = self.client.get(reverse('fiado:detalhe', args=[self.fiado.id]))
        self.assertContains(resposta, 'Editar itens')
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'mesma senha utilizada para quitar')
        self.assertContains(resposta, 'Adicionar produto')
        self.assert_compra_original()

    def test_corrige_produto_quantidade_preco_e_recalcula_saldo(self):
        self.fiado.registrar_pagamento(Decimal('5.00'))
        dados = self.dados_edicao(**{
            'itens-0-produto': str(self.outro_produto.id),
            'itens-0-preco_unitario': '8.50', 'origem': 'clientes',
            'total': '0.01', 'itens-0-subtotal': '0.01',
        })
        resposta = self.client.post(self.url, dados)
        self.assertRedirects(
            resposta,
            reverse('fiado:detalhe', args=[self.fiado.id]) + '?origem=clientes',
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.produto, self.outro_produto)
        self.assertEqual(self.item.quantidade, 3)
        self.assertEqual(self.item.subtotal, Decimal('25.50'))
        fiado = Fiado.objects.select_related('venda').get(pk=self.fiado.id)
        self.assertEqual(fiado.venda.total, Decimal('25.50'))
        self.assertEqual(fiado.valor_pago, Decimal('5.00'))
        self.assertEqual(fiado.saldo_devedor, Decimal('20.50'))
        self.assertFalse(fiado.pago)
        self.assertFalse(RecebimentoFiado.objects.exists())

    def test_adiciona_produto_e_remove_item_lancado_a_mais(self):
        dados = self.dados_edicao(**{
            'itens-TOTAL_FORMS': '2', 'itens-0-DELETE': 'on',
            'itens-1-produto': str(self.outro_produto.id),
            'itens-1-quantidade': '2', 'itens-1-preco_unitario': '8.00',
        })
        self.assertEqual(self.client.post(self.url, dados).status_code, 302)
        self.assertFalse(ItemVenda.objects.filter(pk=self.item.pk).exists())
        novo = self.venda.itens.get()
        self.assertEqual(novo.produto, self.outro_produto)
        self.assertEqual(novo.subtotal, Decimal('16.00'))
        self.venda.refresh_from_db()
        self.assertEqual(self.venda.total, Decimal('16.00'))

    def test_senha_ausente_errada_e_senha_de_login_nao_autorizam(self):
        self.usuario.set_password('senha-login')
        self.usuario.save()
        self.client.force_login(self.usuario)
        for senha in ('', 'errada', 'senha-login'):
            with self.subTest(senha=senha):
                resposta = self.client.post(self.url, self.dados_edicao(senha=senha))
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['autorizacao'].errors)
                if senha:
                    self.assertNotContains(resposta, f'value="{senha}"')
                self.assert_compra_original()

    def test_remove_todos_os_itens_e_encerra_saldo_sem_criar_pagamento(self):
        outro_item = ItemVenda.objects.create(
            venda=self.venda, produto=self.outro_produto, quantidade=1,
            preco_unitario=Decimal('8.00'), subtotal=Decimal('8.00'),
        )
        self.venda.total = Decimal('26.00')
        self.venda.save(update_fields=['total'])
        dados = self.dados_edicao(**{
            'itens-TOTAL_FORMS': '2', 'itens-INITIAL_FORMS': '2',
            'itens-0-DELETE': 'on',
            'itens-1-id': str(outro_item.id), 'itens-1-DELETE': 'on',
        })
        # O navegador não envia os campos desabilitados das linhas removidas.
        for campo in ('produto', 'quantidade', 'preco_unitario'):
            dados.pop(f'itens-0-{campo}')

        resposta = self.client.post(self.url, dados)
        self.assertRedirects(
            resposta, reverse('fiado:detalhe', args=[self.fiado.id]) + '?origem=fiado',
        )
        fiado = Fiado.objects.select_related('venda').get(pk=self.fiado.pk)
        self.assertFalse(fiado.venda.itens.exists())
        self.assertEqual(fiado.venda.total, Decimal('0.00'))
        self.assertEqual(fiado.valor_pago, Decimal('0.00'))
        self.assertEqual(fiado.saldo_devedor, Decimal('0.00'))
        self.assertTrue(fiado.pago)
        self.assertFalse(Fiado.objects.filter(pk=fiado.pk, pago=False).exists())
        self.assertFalse(RecebimentoFiado.objects.exists())
        detalhe = self.client.get(reverse('fiado:detalhe', args=[fiado.id]))
        self.assertContains(detalhe, 'Todos os itens desta compra foram removidos.')
        self.assertContains(detalhe, 'SEM ITENS')
        self.assertNotContains(detalhe, 'Receber pagamento')

    def test_remover_todos_os_itens_exige_senha_correta(self):
        for senha in ('', 'errada'):
            with self.subTest(senha=senha):
                dados = self.dados_edicao(senha=senha, **{'itens-0-DELETE': 'on'})
                resposta = self.client.post(self.url, dados)
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['autorizacao'].errors)
                self.assert_compra_original()

    def test_nao_remove_todos_os_itens_com_pagamento_registrado(self):
        self.fiado.registrar_pagamento(Decimal('5.00'))
        dados = self.dados_edicao(**{'itens-0-DELETE': 'on'})
        resposta = self.client.post(self.url, dados)
        self.assertContains(resposta, 'não pode ser menor que o valor já pago')
        self.assert_compra_original()
        self.fiado.refresh_from_db()
        self.assertEqual(self.fiado.valor_pago, Decimal('5.00'))
        self.assertFalse(self.fiado.pago)

    def test_admin_tambem_precisa_informar_a_senha(self):
        self.usuario.is_superuser = True
        self.usuario.save()
        resposta = self.client.post(self.url, self.dados_edicao(senha='errada'))
        self.assertEqual(resposta.status_code, 200)
        self.assert_compra_original()

    def test_preserva_espacos_da_senha_de_quitacao(self):
        ConfiguracaoFiado.carregar().definir_senha(' 4321 ')
        dados = self.dados_edicao(senha='4321')
        self.assertEqual(self.client.post(self.url, dados).status_code, 200)
        self.assert_compra_original()
        dados['senha'] = ' 4321 '
        self.assertEqual(self.client.post(self.url, dados).status_code, 302)

    def test_sem_senha_configurada_nao_permite_edicao(self):
        dados = self.dados_edicao()
        ConfiguracaoFiado.objects.update(senha_hash='')
        for metodo in (self.client.get, self.client.post):
            resposta = metodo(self.url, dados)
            self.assertEqual(resposta.status_code, 302)
            self.assert_compra_original()

    def test_rejeita_quantidade_preco_produto_e_total_invalidos(self):
        dados_originais = self.dados_edicao()
        for alteracoes in (
            {'itens-0-quantidade': '0'}, {'itens-0-quantidade': '-1'},
            {'itens-0-quantidade': '1.5'}, {'itens-0-quantidade': '2147483648'},
            {'itens-0-preco_unitario': '0'}, {'itens-0-preco_unitario': '-1'},
            {'itens-0-preco_unitario': 'NaN'}, {'itens-0-preco_unitario': 'Infinity'},
            {'itens-0-preco_unitario': '1.001'}, {'itens-0-produto': '999999999'},
            {'itens-0-quantidade': '2147483647', 'itens-0-preco_unitario': '99999999.99'},
            {'itens-TOTAL_FORMS': '0', 'itens-INITIAL_FORMS': '0'},
            {'itens-TOTAL_FORMS': '1001'},
        ):
            with self.subTest(alteracoes=alteracoes):
                resposta = self.client.post(self.url, {**dados_originais, **alteracoes})
                self.assertEqual(resposta.status_code, 200)
                self.assertFalse(resposta.context['formset'].is_valid())
                self.assert_compra_original()

    def test_rejeita_id_de_item_de_outra_compra(self):
        outra_venda = Venda.objects.create(forma_pagamento='FIADO', total=Decimal('8.00'))
        outro_item = ItemVenda.objects.create(
            venda=outra_venda, produto=self.outro_produto, quantidade=1,
            preco_unitario=Decimal('8.00'), subtotal=Decimal('8.00'),
        )
        dados = self.dados_edicao(**{'itens-0-id': str(outro_item.id)})
        self.assertEqual(self.client.post(self.url, dados).status_code, 200)
        self.assert_compra_original()
        outro_item.refresh_from_db()
        self.assertEqual(outro_item.quantidade, 1)

    def test_nao_omite_itens_nem_repete_ids(self):
        dados_originais = self.dados_edicao()
        for alteracoes in (
            {'itens-INITIAL_FORMS': '0'},
            {'itens-0-id': ''},
            {'itens-TOTAL_FORMS': '2', 'itens-INITIAL_FORMS': '2',
             'itens-1-id': str(self.item.id), 'itens-1-produto': str(self.produto.id),
             'itens-1-quantidade': '1', 'itens-1-preco_unitario': '9.00'},
        ):
            with self.subTest(alteracoes=alteracoes):
                resposta = self.client.post(self.url, {**dados_originais, **alteracoes})
                self.assertEqual(resposta.status_code, 200)
                self.assert_compra_original()

    def test_rejeita_total_menor_que_pagamento_e_permite_igual(self):
        self.fiado.registrar_pagamento(Decimal('9.00'))
        resposta = self.client.post(self.url, self.dados_edicao(**{
            'itens-0-quantidade': '1', 'itens-0-preco_unitario': '8.00',
        }))
        self.assertContains(resposta, 'não pode ser menor que o valor já pago')
        self.assert_compra_original()
        resposta = self.client.post(self.url, self.dados_edicao(**{'itens-0-quantidade': '1'}))
        self.assertEqual(resposta.status_code, 302)
        self.fiado.refresh_from_db()
        self.assertTrue(self.fiado.pago)
        self.assertEqual(self.fiado.valor_pago, Decimal('9.00'))
        self.assertIsNotNone(self.fiado.pago_em)
        self.assertFalse(RecebimentoFiado.objects.exists())

    def test_quitado_nao_permite_get_nem_post(self):
        dados = self.dados_edicao()
        self.fiado.marcar_como_pago()
        for metodo in (self.client.get, self.client.post):
            self.assertEqual(metodo(self.url, dados).status_code, 302)
            self.assert_compra_original()
        detalhe = self.client.get(reverse('fiado:detalhe', args=[self.fiado.id]))
        self.assertNotContains(detalhe, 'Editar itens')

    def test_pagamento_durante_edicao_exige_recarregar(self):
        dados = self.dados_edicao()
        self.fiado.registrar_pagamento(Decimal('1.00'))
        resposta = self.client.post(self.url, dados)
        self.assertContains(resposta, 'mudaram durante a edição')
        self.assert_compra_original()

    def test_edicao_simultanea_nao_sobrescreve_alteracao_anterior(self):
        dados = self.dados_edicao()
        self.assertEqual(self.client.post(self.url, dados).status_code, 302)
        resposta = self.client.post(self.url, {**dados, 'itens-0-quantidade': '4'})
        self.assertContains(resposta, 'mudaram durante a edição')
        self.item.refresh_from_db()
        self.venda.refresh_from_db()
        self.assertEqual(self.item.quantidade, 3)
        self.assertEqual(self.venda.total, Decimal('27.00'))

    def test_exige_login_e_csrf(self):
        dados = self.dados_edicao()
        cliente_csrf = Client(enforce_csrf_checks=True)
        cliente_csrf.force_login(self.usuario)
        self.assertEqual(cliente_csrf.post(self.url, dados).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, dados).status_code, 302)
        self.assert_compra_original()


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
