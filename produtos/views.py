from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import produtoForm
from .models import produtosModel


def produtos_home(request):
    produtos = produtosModel.objects.all().order_by('nome', 'id')
    pagina = Paginator(produtos, 20).get_page(request.GET.get('page'))
    return render(
        request,
        'produtos/home.html',
        {'produtos': pagina},
    )


def produtos_adicionar(request):
    form = produtoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto cadastrado com sucesso.')
        return redirect('produtos:produtos_home')

    return render(
        request,
        'produtos/form.html',
        {'form': form, 'titulo': 'Adicionar produto', 'acao': 'Cadastrar produto'},
    )


def produtos_buscar(request):
    query = request.GET.get('nome', '').strip()
    produtos = produtosModel.objects.none()

    if query:
        produtos = produtosModel.objects.filter(nome__icontains=query).order_by('nome')

    return render(
        request,
        'produtos/buscar.html',
        {'produtos': produtos, 'query': query},
    )


def produtos_editar(request, id):
    produto = get_object_or_404(produtosModel, id=id)
    form = produtoForm(request.POST or None, instance=produto)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto atualizado com sucesso.')
        return redirect('produtos:produtos_home')

    return render(
        request,
        'produtos/form.html',
        {
            'form': form,
            'produto': produto,
            'titulo': f'Editar produto: {produto.nome}',
            'acao': 'Salvar alterações',
        },
    )


def produtos_remover(request, id):
    produto = get_object_or_404(produtosModel, id=id)

    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, 'Produto removido com sucesso.')
        except ProtectedError:
            messages.error(
                request,
                'Este produto já aparece em vendas e não pode ser removido, pois faz parte do histórico.',
            )
        return redirect('produtos:produtos_home')

    return render(request, 'produtos/remover.html', {'produto': produto})
