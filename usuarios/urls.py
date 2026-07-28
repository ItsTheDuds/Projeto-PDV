from django.urls import path
from . import views
from usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.usuarios_home, name='usuarios_home'),
    path('adicionar/', views.usuarios_adicionar, name='usuarios_adicionar'),
    path('remover/<int:id>/', views.usuarios_remover, name='usuarios_remover'),
    path('editar/<int:id>/', views.usuarios_editar, name='usuarios_editar'),
    path('buscar/', views.usuarios_buscar, name='usuarios_buscar'),
]