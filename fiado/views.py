import re

from django.contrib import messages
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente

from .models import ConfiguracaoFiado, Fiado


def home(request):
    query = request.GET.get('q', '').strip()
    fiados = (
        Fiado.objects.filter(pago=False)
        .select_related('venda', 'venda__cliente')
        .prefetch_related('venda__itens__produto')
    )

    if query:
        filtro = Q(venda__cliente__nome__icontains=query)
        celular_query = re.sub(r'\D', '', query)
        if celular_query:
            filtro |= Q(venda__cliente__celular__icontains=celular_query)
        fiados = fiados.filter(filtro)

    configuracao = ConfiguracaoFiado.carregar()
    return render(
        request,
        'fiado/home.html',
        {
            'fiados': fiados,
            'query': query,
            'senha_configurada': configuracao.senha_configurada,
            'pode_configurar_senha': (
                not configuracao.senha_configurada or request.user.is_superuser
            ),
        },
    )


def detalhe(request, id):
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


def marcar_pago(request, id):
    fiado = get_object_or_404(Fiado, id=id)
    configuracao = ConfiguracaoFiado.carregar()

    if request.method == 'POST':
        if not configuracao.senha_configurada:
            messages.error(request, 'Cadastre primeiro a senha de quitação do fiado.')
            return redirect('fiado:configurar_senha')

        senha = request.POST.get('senha', '')
        if not configuracao.conferir_senha(senha):
            messages.error(request, 'Senha inválida.')
            return redirect('fiado:detalhe', id=fiado.id)

        fiado.marcar_como_pago()
        messages.success(request, 'Fiado marcado como pago.')
        return redirect('fiado:detalhe', id=fiado.id)

    return redirect('fiado:detalhe', id=fiado.id)


def cliente_historico(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    fiados = (
        Fiado.objects.filter(venda__cliente=cliente)
        .select_related('venda')
        .prefetch_related('venda__itens__produto')
    )
    saldo = (
        fiados.filter(pago=False).aggregate(
            total=Coalesce(
                Sum('venda__total'),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )['total']
    )
    return render(
        request,
        'fiado/historico_cliente.html',
        {'cliente': cliente, 'fiados': fiados, 'saldo': saldo},
    )
