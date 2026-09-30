from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.home, name='home'),
    path('adicionar/', views.adicionar, name='adicionar'),
    path('editar/<int:id>/', views.editar, name='editar'),
    path('remover/<int:id>/', views.remover, name='remover'),
    path('buscar/', views.buscar, name='buscar'),
]
