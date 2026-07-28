from django.urls import path
from . import views
from produtos import views

app_name = 'produtos'

urlpatterns = [
    path('', views.produtos_home, name='produtos_home'),
    path('adicionar/', views.produtos_adicionar, name='produtos_adicionar'),
    path('remover/<int:id>/', views.produtos_remover, name='produtos_remover'),
    path('editar/<int:id>/', views.produtos_editar, name='produtos_editar'),
    path('buscar/', views.produtos_buscar, name='produtos_buscar'),
]