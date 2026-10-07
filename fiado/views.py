import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from clientes.models import Cliente

from .models import (
    AplicacaoRecebimento,
    ConfiguracaoFiado,
    Fiado,
    RecebimentoFiado,
)


def _decimal_pagamento(valor):
    texto = str(valor or '').strip().replace(',', '.')
    try:
        return Decimal(texto).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        raise ValueError('Informe um valor de pagamento válido.')


def _origem(request):
    origem = request.POST.get('origem') or request.GET.get('origem')
    return origem if origem in ('clientes', 'fiado') else 'fiado'


def _fiados_abertos_cliente(cliente):
    return (
        Fiado.objects.filter(venda__cliente=cliente, pago=False)
        .select_related('venda', 'venda__cliente')
        .prefetch_related('venda__itens__produto')
        .order_by('venda__criada_em', 'id')
    )


def home(request):
    query = request.GET.get('q', '').strip()
    fiados = (
        Fiado.objects.filter(pago=False)
        .select_related('venda', 'venda__cliente')
        .order_by('venda__cliente__nome', 'venda__criada_em', 'id')
    )

    if query:
        filtro = Q(venda__cliente__nome__icontains=query)
        celular_query = re.sub(r'\D', '', query)
        if celular_query:
            filtro |= Q(venda__cliente__celular__icontains=celular_query)
        fiados = fiados.filter(filtro)

    agrupados = {}
    for fiado in fiados:
        cliente = fiado.venda.cliente
        if cliente is None:
            continue

        dados = agrupados.setdefault(
            cliente.id,
            {
                'cliente': cliente,
                'quantidade_compras': 0,
                'saldo': Decimal('0.00'),
            },
        )
        dados['quantidade_compras'] += 1
        dados['saldo'] += fiado.saldo_devedor

    clientes_em_aberto = list(agrupados.values())

    configuracao = ConfiguracaoFiado.carregar()
    return render(
        request,
        'fiado/home.html',
        {
            'clientes_em_aberto': clientes_em_aberto,
            'query': query,
            'senha_configurada': configuracao.senha_configurada,
            'pode_configurar_senha': (
                not configuracao.senha_configurada or request.user.is_superuser
            ),
        },
    )


def detalhe(request, id):
    origem = _origem(request)
    fiado = get_object_or_404(
        Fiado.objects.select_related('venda', 'venda__cliente').prefetch_related('venda__itens__produto'),
        id=id,
    )
    configuracao = ConfiguracaoFiado.carregar()
    return render(
        request,
        'fiado/detalhe.html',
        {
            'fiado': fiado,
            'senha_configurada': configuracao.senha_configurada,
            'origem': origem,
        },
    )


def configurar_senha(request):
    configuracao = ConfiguracaoFiado.carregar()

    if configuracao.senha_configurada and not request.user.is_superuser:
        messages.error(
            request,
            'A senha de quitação já foi definida. Somente o administrador do sistema pode alterá-la ou resetá-la.',
        )
        return redirect('fiado:home')

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '')
        confirmar_senha = request.POST.get('confirmar_senha', '')

        if len(nova_senha) < 4:
            messages.error(request, 'A nova senha deve ter pelo menos 4 caracteres.')
            return redirect('fiado:configurar_senha')

        if nova_senha != confirmar_senha:
            messages.error(request, 'A confirmação da senha não confere.')
            return redirect('fiado:configurar_senha')

        primeira_configuracao = not configuracao.senha_configurada
        configuracao.definir_senha(nova_senha)

        if primeira_configuracao:
            messages.success(request, 'Senha de quitação cadastrada com sucesso.')
        else:
            messages.success(request, 'Senha de quitação redefinida com sucesso.')

        return redirect('fiado:home')

    return render(
        request,
        'fiado/configurar_senha.html',
        {
            'senha_configurada': configuracao.senha_configurada,
            'alteracao_admin': configuracao.senha_configurada and request.user.is_superuser,
        },
    )


def receber_cliente(request, cliente_id):
    origem = _origem(request)
    cliente = get_object_or_404(Cliente, id=cliente_id)
    configuracao = ConfiguracaoFiado.carregar()
    fiados = list(_fiados_abertos_cliente(cliente))
    saldo_total = sum((fiado.saldo_devedor for fiado in fiados), Decimal('0.00'))

    if request.method == 'POST':
        if not configuracao.senha_configurada:
            messages.error(request, 'Cadastre primeiro a senha de quitação do fiado.')
            return redirect('fiado:configurar_senha')

        senha = request.POST.get('senha', '')
        if not configuracao.conferir_senha(senha):
            messages.error(request, 'Senha de quitação inválida.')
            return redirect(f"{reverse('fiado:receber_cliente', kwargs={'cliente_id': cliente.id})}?origem={origem}")

        try:
            valor = _decimal_pagamento(request.POST.get('valor'))
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect(f"{reverse('fiado:receber_cliente', kwargs={'cliente_id': cliente.id})}?origem={origem}")

        if valor <= 0:
            messages.error(request, 'O valor recebido deve ser maior que R$ 0,00.')
            return redirect(f"{reverse('fiado:receber_cliente', kwargs={'cliente_id': cliente.id})}?origem={origem}")

        if valor > saldo_total:
            messages.error(
                request,
                f'O valor recebido não pode ser maior que o saldo de R$ {saldo_total:.2f}.',
            )
            return redirect(f"{reverse('fiado:receber_cliente', kwargs={'cliente_id': cliente.id})}?origem={origem}")

        with transaction.atomic():
            fiados_bloqueados = list(
                Fiado.objects.select_for_update()
                .filter(venda__cliente=cliente, pago=False)
                .select_related('venda')
                .order_by('venda__criada_em', 'id')
            )

            saldo_atual = sum(
                (fiado.saldo_devedor for fiado in fiados_bloqueados),
                Decimal('0.00'),
            )
            if valor > saldo_atual:
                messages.error(
                    request,
                    'O saldo mudou enquanto o recebimento era processado. Tente novamente.',
                )
                return redirect(f"{reverse('fiado:receber_cliente', kwargs={'cliente_id': cliente.id})}?origem={origem}")

            recebimento = RecebimentoFiado.objects.create(
                cliente=cliente,
                valor_total=valor,
                usuario=request.user,
            )

            restante = valor
            for fiado in fiados_bloqueados:
                if restante <= 0:
                    break

                aplicar = min(restante, fiado.saldo_devedor)
                if aplicar <= 0:
                    continue

                fiado.registrar_pagamento(aplicar)
                AplicacaoRecebimento.objects.create(
                    recebimento=recebimento,
                    fiado=fiado,
                    valor=aplicar,
                )
                restante -= aplicar

        messages.success(
            request,
            f'Recebimento de R$ {valor:.2f} registrado para {cliente.nome}.',
        )
        return redirect(f"{reverse('fiado:cliente_historico', kwargs={'cliente_id': cliente.id})}?origem={origem}")

    return render(
        request,
        'fiado/receber_cliente.html',
        {
            'cliente': cliente,
            'fiados': fiados,
            'saldo_total': saldo_total,
            'senha_configurada': configuracao.senha_configurada,
            'origem': origem,
        },
    )


def marcar_pago(request, id):
    fiado = get_object_or_404(
        Fiado.objects.select_related('venda', 'venda__cliente'),
        id=id,
    )
    configuracao = ConfiguracaoFiado.carregar()

    if request.method == 'POST':
        if not configuracao.senha_configurada:
            messages.error(request, 'Cadastre primeiro a senha de quitação do fiado.')
            return redirect('fiado:configurar_senha')

        senha = request.POST.get('senha', '')
        if not configuracao.conferir_senha(senha):
            messages.error(request, 'Senha inválida.')
            return redirect('fiado:detalhe', id=fiado.id)

        if fiado.pago:
            return redirect('fiado:detalhe', id=fiado.id)

        with transaction.atomic():
            fiado = (
                Fiado.objects.select_for_update()
                .select_related('venda', 'venda__cliente')
                .get(id=fiado.id)
            )
            valor = fiado.saldo_devedor
            recebimento = RecebimentoFiado.objects.create(
                cliente=fiado.venda.cliente,
                valor_total=valor,
                usuario=request.user,
            )
            fiado.registrar_pagamento(valor)
            AplicacaoRecebimento.objects.create(
                recebimento=recebimento,
                fiado=fiado,
                valor=valor,
            )

        messages.success(request, 'Pedido quitado com sucesso.')
        return redirect('fiado:detalhe', id=fiado.id)

    return redirect('fiado:detalhe', id=fiado.id)


def cliente_historico(request, cliente_id):
    origem = _origem(request)
    cliente = get_object_or_404(Cliente, id=cliente_id)
    fiados = list(
        Fiado.objects.filter(venda__cliente=cliente)
        .select_related('venda')
        .prefetch_related('venda__itens__produto')
        .order_by('-venda__criada_em', '-id')
    )
    saldo = sum((fiado.saldo_devedor for fiado in fiados), Decimal('0.00'))
    recebimentos = (
        RecebimentoFiado.objects.filter(cliente=cliente)
        .select_related('usuario')
        .prefetch_related('aplicacoes__fiado__venda')
        .order_by('-criado_em')
    )

    return render(
        request,
        'fiado/historico_cliente.html',
        {
            'cliente': cliente,
            'fiados': fiados,
            'saldo': saldo,
            'recebimentos': recebimentos,
            'origem': origem,
        },
    )


@require_http_methods(['GET', 'POST'])
def imprimir_cliente(request, cliente_id):
    """Seleciona compras fiadas para impressão térmica sem alterar pagamentos."""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    origem = _origem(request)
    parametros = request.POST if request.method == 'POST' else request.GET
    retorno = 'receber' if parametros.get('retorno') == 'receber' else 'conta'

    todas = list(
        Fiado.objects.filter(venda__cliente=cliente)
        .select_related('venda')
        .order_by('-venda__criada_em', '-venda_id')
    )

    selecionados = {f.id for f in todas if f.saldo_devedor > 0}
    erro = ''

    if request.method == 'POST':
        ids_raw = request.POST.getlist('fiados')
        selecionados = set()

        if not ids_raw:
            erro = 'Selecione ao menos uma compra para imprimir.'
        elif len(ids_raw) != len(set(ids_raw)):
            erro = 'A seleção contém compras repetidas.'
        elif not all(re.fullmatch(r'[1-9]\\d*', id_raw) for id_raw in ids_raw):
            erro = 'A seleção de compras é inválida.'
        else:
            selecionados = {int(id_raw) for id_raw in ids_raw}
            disponiveis = {f.id for f in todas}
            if not selecionados.issubset(disponiveis):
                erro = 'Uma das compras selecionadas não pertence a este cliente.'

        if not erro:
            # Mantém a impressão apenas nas vendas selecionadas e
            # recupera os itens/produtos de cada uma sem consultas repetidas.
            fiados = list(
                Fiado.objects.filter(venda__cliente=cliente, id__in=selecionados)
                .select_related('venda')
                .prefetch_related('venda__itens__produto')
                .order_by('venda__criada_em', 'venda_id')
            )
            return render(
                request,
                'fiado/imprimir_cliente.html',
                {
                    'cliente': cliente,
                    'fiados': fiados,
                    'total_compras': sum((f.venda.total for f in fiados), Decimal('0.00')),
                    'total_pago': sum((f.valor_pago for f in fiados), Decimal('0.00')),
                    'saldo_em_aberto': sum((f.saldo_devedor for f in fiados), Decimal('0.00')),
                    'emitido_em': timezone.now(),
                    'auto_imprimir': True,
                    'nome_estabelecimento': 'Águia Café',
                    'origem': origem,
                    'retorno': retorno,
                },
            )

    primeira = todas[-1].venda.criada_em if todas else None
    return render(
        request,
        'fiado/imprimir_opcoes.html',
        {
            'cliente': cliente,
            'fiados': todas,
            'selecionados': selecionados,
            'data_inicial': (
                timezone.localtime(primeira).strftime('%d/%m/%Y')
                if primeira else ''
            ),
            'data_final': timezone.localdate().strftime('%d/%m/%Y'),
            'origem': origem,
            'retorno': retorno,
            'erro': erro,
        },
    )
