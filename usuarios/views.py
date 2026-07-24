from django.shortcuts import render
from django.http import HttpResponse
from .forms import usuarioForm
from django.shortcuts import redirect
from .models import usuariosModel
from django.shortcuts import get_object_or_404

def usuarios_home(request):
    context = {
        "usuarios":usuariosModel.objects.all()
    }
    return render(request, 'usuarios/home.html', context)

def usuarios_adicionar(request):
    if request.method == 'POST':
        form = usuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:usuarios_home')
    else:
        form = usuarioForm()
    context = {
        'form': form
    }
    return render(request, 'usuarios/adicionar.html', context)
    
def usuarios_remover(request, id):
    try:
        usuario = usuariosModel.objects.get(id=id)
        if request.method == 'POST':
            usuario.delete()
            return redirect('usuarios:usuarios_home')
    except usuariosModel.DoesNotExist:
        return HttpResponse("Usuário não encontrado.")
    return render(request, 'usuarios/remover.html', {'usuario': usuario})

def usuarios_editar(request, id):
    usuario = get_object_or_404(usuariosModel, id=id)
    if request.method == 'POST':
        form = usuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('usuarios:usuarios_home')
    else:
        form = usuarioForm(instance=usuario)
    context = {
        'form': form,
        'usuario': usuario
    }
    return render(request, 'usuarios/editar.html', context)