from django.shortcuts import render
from produtos.models import produtosModel

def home(request):
    itens = produtosModel.objects.all()

    return render(
        request,
        'PDV/home.html',
        {'itens': itens}
    )
    
def Pinicial(request):
    return render(request, 'projeto/home.html')




