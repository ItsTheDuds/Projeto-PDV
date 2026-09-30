from django.contrib import messages
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente


def _com_saldo(queryset):
    return queryset.annotate(
        saldo_devedor=Coalesce(
            Sum(
                'vendas__total',
                filter=Q(vendas__fiado__pago=False),
            ),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )


def home(request):
    clientes = _com_saldo(Cliente.objects.all())
    return render(request, 'clientes/home.html', {'clientes': clientes})


def adicionar(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente cadastrado com sucesso.')
        return redirect('clientes:home')
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Adicionar cliente'})


def editar(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente atualizado com sucesso.')
        return redirect('clientes:home')
    return render(
        request,
        'clientes/form.html',
        {'form': form, 'cliente': cliente, 'titulo': 'Editar cliente'},
    )


def remover(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, 'Cliente removido com sucesso.')
            return redirect('clientes:home')
        except ProtectedError:
            messages.error(
                request,
                'Este cliente possui vendas registradas e não pode ser removido.',
            )
            return redirect('clientes:home')
    return render(request, 'clientes/remover.html', {'cliente': cliente})


def buscar(request):
    query = request.GET.get('q', '').strip()
    clientes = Cliente.objects.none()

    if query:
        clientes = Cliente.objects.filter(
            Q(nome__icontains=query)
            | Q(celular__icontains=query)
            | Q(email__icontains=query)
        )
        clientes = _com_saldo(clientes)

    return render(
        request,
        'clientes/buscar.html',
        {'clientes': clientes, 'query': query},
    )
