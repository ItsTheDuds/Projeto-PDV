from django.shortcuts import render
from django.http import HttpResponse
from .models import produtosModel
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from .forms import produtoForm

# Create your views here.
def produtos_home(request):
    context = {
        "produtos": produtosModel.objects.all()
    }
    return render(request, 'produtos/home.html', context)

def produtos_adicionar(request):
    if request.method == 'POST':
        form = produtoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('produtos:produtos_home')
    else:
        form = produtoForm()
    context = {
        'form': form
    }
    return render(request, 'produtos/adicionar.html', context)

def produtos_buscar(request):
    query = request.GET.get('nome')
    if query:
        produtos = produtosModel.objects.filter(nome__icontains=query)
    else:
        produtos = produtosModel.objects.none()
    context = {
        'produtos': produtos,
        'query': query
    }
    return render(request, 'produtos/buscar.html', context)

# Mude de: def produtos_editar(request, produto_id):
def produtos_editar(request, id): # <--- Alterado aqui
    produto = get_object_or_404(produtosModel, id=id)
    if request.method == 'POST':
        form = produtoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('produtos:produtos_home')
    else:
        form = produtoForm(instance=produto)
    context = {
        'form': form,
        'produto': produto
    }
    return render(request, 'produtos/editar.html', context)

def produtos_remover(request, id):
    produto = get_object_or_404(produtosModel, id=id)
    if request.method == 'POST':
        produto.delete()
        return redirect('produtos:produtos_home')
    context = {
        'produto': produto
    }
    return render(request, 'produtos/remover.html', context)

