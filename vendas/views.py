import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from clientes.models import Cliente
from fiado.models import Fiado
from produtos.models import produtosModel

from .models import ItemVenda, Venda


def home(request):
    produtos = produtosModel.objects.filter(quantidade__gt=0).order_by('nome')
    clientes = Cliente.objects.all().order_by('nome')
    return render(
        request,
        'PDV/home.html',
        {'produtos': produtos, 'clientes': clientes},
    )


@require_POST
def finalizar(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    itens = payload.get('itens') or []
    forma_pagamento = payload.get('forma_pagamento')
    cliente_id = payload.get('cliente_id')

    formas_validas = {codigo for codigo, _ in Venda.FORMAS_PAGAMENTO}
    if forma_pagamento not in formas_validas:
        return JsonResponse({'erro': 'Forma de pagamento inválida.'}, status=400)

    if not itens:
        return JsonResponse({'erro': 'Adicione pelo menos um produto.'}, status=400)

    cliente = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return JsonResponse({'erro': 'Cliente não encontrado.'}, status=400)

    if forma_pagamento == Venda.FIADO and cliente is None:
        return JsonResponse(
            {'erro': 'Selecione um cliente para registrar uma venda fiada.'},
            status=400,
        )

    try:
        with transaction.atomic():
            venda = Venda.objects.create(
                cliente=cliente,
                forma_pagamento=forma_pagamento,
                total=Decimal('0.00'),
            )

            total = Decimal('0.00')

            for item in itens:
                produto_id = int(item['produto_id'])
                quantidade = int(item['quantidade'])

                if quantidade <= 0:
                    raise ValueError('Quantidade inválida.')

                produto = produtosModel.objects.select_for_update().get(id=produto_id)

                if produto.quantidade < quantidade:
                    raise ValueError(
                        f'Estoque insuficiente para {produto.nome}. Disponível: {produto.quantidade}.'
                    )

                preco_informado = item.get('preco_unitario')
                if preco_informado in (None, ''):
                    preco_unitario = produto.preco
                else:
                    try:
                        preco_unitario = Decimal(str(preco_informado)).quantize(Decimal('0.01'))
                    except InvalidOperation as exc:
                        raise ValueError(f'Preço inválido para {produto.nome}.') from exc

                if preco_unitario < 0:
                    raise ValueError(f'Preço inválido para {produto.nome}.')

                subtotal = (preco_unitario * quantidade).quantize(Decimal('0.01'))

                ItemVenda.objects.create(
                    venda=venda,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    subtotal=subtotal,
                )

                produto.quantidade -= quantidade
                produto.save(update_fields=['quantidade'])
                total += subtotal

            venda.total = total
            venda.save(update_fields=['total'])

            if forma_pagamento == Venda.FIADO:
                Fiado.objects.create(venda=venda)

    except (KeyError, TypeError, ValueError, produtosModel.DoesNotExist) as exc:
        return JsonResponse({'erro': str(exc) or 'Não foi possível finalizar a venda.'}, status=400)

    return JsonResponse({
        'ok': True,
        'venda_id': venda.id,
        'total': f'{venda.total:.2f}',
        'fiado': forma_pagamento == Venda.FIADO,
    })
