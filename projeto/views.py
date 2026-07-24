from django.http import HttpResponse
from usuarios.models import usuariosModel
from django.shortcuts import render
from django.shortcuts import redirect

def home(request):
    return render(request, 'projeto/home.html')